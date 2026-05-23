from datetime import datetime

import numpy as np
import pandas as pd
import yaml

from pandera.pandas import Column, DataFrameSchema, Check

from utils.collections import reverse_map
from etl.extract import extract_api_source, extract_sql_source


def map_field_names(data):
    with open("../config.yaml", "r", encoding="utf-8") as f:
        mappings = yaml.safe_load(f)["mappings"]
        mappings = {k: reverse_map(v) for k, v in mappings.items()}
        for key, df in data.items():
            if df is None:
                continue
            columns = mappings[key]
            if columns:
                df.rename(columns=columns, inplace=True)


def normalize(data):
    customers = data["customer"]
    if customers is not None:
        customers["first_name"] = customers["first_name"].str.strip()
        customers["last_name"] = customers["last_name"].str.strip()
        customers["email"] = customers["email"].str.strip()

    products = data["product"]
    products["category"] = products["category"].str.strip().str.capitalize()
    products["name"] = products["name"].str.strip()

    orders = data["order"]
    orders["status"] = orders["status"].str.strip().str.lower()

    orders["created_at"] = pd.to_datetime(orders["created_at"])


def validate(data):
    if data["customer"] is not None:
        schema = DataFrameSchema({
            "id": Column(int, nullable=False),
            "email": Column(str, Check.str_matches(r"^[^@]+@[^@]+\.[^@]+$"), nullable=False),
            "first_name": Column(str, Check.str_matches(r"^[A-Za-z]{1,50}$"), nullable=False),
            "last_name": Column(str, Check.str_matches(r"^[A-Za-z]{1,50}$"), nullable=False)
        }, drop_invalid_rows=True)
        data["customer"] = schema.validate(data["customer"], lazy=True)

    schema = DataFrameSchema({
        "id": Column(int, nullable=False),
        "sku": Column(str, Check.str_length(20, 20), nullable=False),
        "category": Column(str, Check.str_length(1, 50), nullable=False),
        "name": Column(str, Check.str_length(1, 50), nullable=False),
        "price": Column(int, Check.gt(0), nullable=False)
    }, drop_invalid_rows=True)
    data["product"] = schema.validate(data["product"], lazy=True)

    schema = DataFrameSchema({
        "id": Column(int, nullable=False),
        "status": Column(str, nullable=False),
        "created_at": Column(datetime, Check.le(pd.Timestamp.now()), nullable=False)
    }, drop_invalid_rows=True)
    data["order"] = schema.validate(data["order"], lazy=True)

    schema = DataFrameSchema({
        "id": Column(int, nullable=False),
        "quantity": Column(int, Check.gt(0), nullable=False),
        "unit_price": Column(int, Check.gt(0), nullable=False)
    }, drop_invalid_rows=True)
    data["order_item"] = schema.validate(data["order_item"], lazy=True)


def filter_data(data):
    valid_customer_ids = data["customer"]["id"] if data["customer"] is not None else []
    valid_product_ids = data["product"]["id"]
    data["order"] = data["order"][
        (data["order"]["status"] == "delivered") &
        ((data["customer"] is None) | (data["order"]["customer_id"].isin(valid_customer_ids)))
        ]
    valid_order_ids = data["order"]["id"]
    data["order_item"] = data["order_item"][
        (data["order_item"]["order_id"].isin(valid_order_ids)) &
        (data["order_item"]["product_id"].isin(valid_product_ids))
        ].copy()
    orders_with_items = data["order_item"]["order_id"].unique()
    data["order"] = data["order"][
        data["order"]["id"].isin(orders_with_items)
    ].copy()


def add_total_price(data):
    order_items = data["order_item"]
    order_items["total_price"] = order_items["quantity"] * order_items["unit_price"]
    data["order"] = (order_items
                     .groupby("order_id")["total_price"]
                     .sum()
                     .reset_index()
                     .merge(data["order"], right_on="id", left_on="order_id", how="right"))


def add_dim_date(data):
    dt = data["order"]["created_at"].dt
    data["order"]["created_at_id"] = dt.strftime("%Y%m%d").astype(int)
    data["dim_date"] = pd.DataFrame({
        "id": data["order"]["created_at_id"],
        "full_date": dt.date,
        "year": dt.year,
        "month": dt.month,
        "day": dt.day,
    })
    data["dim_date"].drop_duplicates(subset=["id"], inplace=True)


def get_score(series, ascending=True, tiles=5):
    bins = pd.qcut(series, tiles, duplicates="drop")
    n = len(bins.cat.categories)
    start, end = tiles - n + 1, tiles + 1
    labels = list(range(start, end))
    if not ascending:
        labels = labels[::-1]
    return bins.cat.rename_categories(labels).astype(int)


def add_customer_metrics(data):
    today = datetime.today()
    r_agg = pd.NamedAgg(column="created_at", aggfunc=lambda dates: (today - dates.max()).days)
    f_agg = pd.NamedAgg(column="order_id", aggfunc="count")
    m_agg = pd.NamedAgg(column="total_price", aggfunc="sum")
    rfm = (data["order"]
           .groupby("customer_id")
           .agg(recency=r_agg, frequency=f_agg, monetary=m_agg)
           .reset_index())

    rfm["r_score"] = get_score(rfm["recency"], ascending=False)
    rfm["f_score"] = get_score(rfm["frequency"])
    rfm["m_score"] = get_score(rfm["monetary"])

    data["customer"] = (data["customer"]
                        .merge(rfm, left_on="id", right_on="customer_id", how="left")
                        .reset_index()
                        .fillna({"r_score": 0, "f_score": 0, "m_score": 0, "frequency": 0, "monetary": 0}))

    data["customer"]["rfm_code"] = (
            data["customer"]["r_score"].astype(int).astype(str) +
            data["customer"]["f_score"].astype(int).astype(str) +
            data["customer"]["m_score"].astype(int).astype(str)
    )


def add_product_metrics(data):
    t_agg = pd.NamedAgg(column="total_price", aggfunc="sum")
    s_agg = pd.NamedAgg(column="quantity", aggfunc="sum")
    metrics = (data["order_item"]
               .groupby("product_id")
               .agg(turnover=t_agg, sales_count=s_agg)
               .reset_index())
    data["product"] = (data["product"]
                       .merge(metrics, left_on="id", right_on="product_id", how="left")
                       .fillna({"turnover": 0, "sales_count": 0}))


def filter_columns(data):
    data["customer"] = data["customer"][[
        "id",
        "last_name",
        "first_name",
        "email",
        "recency",
        "frequency",
        "monetary",
        "rfm_code"
    ]]
    data["product"] = data["product"][[
        "id",
        "sku",
        "name",
        "category",
        "price",
        "turnover",
        "sales_count"
    ]]
    data["order"] = data["order"][[
        "id",
        "created_at_id",
        "customer_id",
        "total_price"
    ]]
    data["order_item"] = data["order_item"][[
        "id",
        "order_id",
        "product_id",
        "quantity",
        "unit_price",
        "total_price"
    ]]


def flatten_api_data(data):
    data["order"] = data["order"][data["order"]['items'].apply(lambda x: x is not None and len(x) > 0)]
    data["order_item"] = data["order"].explode("items", ignore_index=True)[["id", "items"]]
    order_ids = data["order_item"]["id"]
    order_items = data["order_item"]["items"].apply(pd.Series)
    data["order_item"] = pd.concat([order_ids, order_items], axis=1).rename(columns={"id": "orderId"})
    data["order_item"]["id"] = data["order_item"].index
    if "quantity" not in data["order_item"].columns:
        data["order_item"]["quantity"] = -1
    if "unitPrice" not in data["order_item"].columns:
        data["order_item"]["unitPrice"] = -1
    if "productId" not in data["order_item"].columns:
        data["order_item"]["productId"] = -1

    data["order"] = data["order"][["id", "status", "orderDate"]].copy()
    data["order"]["customerId"] = None
    data["customer"] = None


def add_prefix_safe(df, column_name, prefix):
    if df is not None and column_name in df.columns:
        df[column_name] = df[column_name].map(lambda x: f"{prefix}_{int(x)}" if pd.notnull(x) else None)


def merge(sql_data, api_data):
    datasets = [('sql', sql_data), ('api', api_data)]
    for prefix, dataset in datasets:
        add_prefix_safe(dataset['order_item'], 'order_id', prefix)
        add_prefix_safe(dataset['order'], 'customer_id', prefix)
        add_prefix_safe(dataset['order_item'], 'product_id', prefix)
        for df in dataset.values():
            add_prefix_safe(df, 'id', prefix)

    merged_data = {'customer': pd.concat([sql_data['customer'], api_data['customer']], ignore_index=True),
                   'product': pd.concat([sql_data['product'], api_data['product']], ignore_index=True),
                   'order': pd.concat([sql_data['order'], api_data['order']], ignore_index=True),
                   'order_item': pd.concat([sql_data['order_item'], api_data['order_item']], ignore_index=True)}
    return merged_data


def transform(sql_data, api_data):
    api_data['order']['items'] = api_data['order']['items']
    flatten_api_data(api_data)
    for data in (api_data, sql_data):
        map_field_names(data)
        normalize(data)
        validate(data)
        filter_data(data)
    merged_data = merge(sql_data, api_data)
    add_dim_date(merged_data)
    add_total_price(merged_data)
    add_customer_metrics(merged_data)
    add_product_metrics(merged_data)
    filter_columns(merged_data)
    return merged_data
