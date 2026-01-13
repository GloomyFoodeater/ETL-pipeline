from datetime import datetime

import pandas as pd
import yaml

from pandera.pandas import Column, DataFrameSchema, Check


def map_field_names(data):
    with open('config.yaml', 'r', encoding='utf-8') as f:
        mappings = yaml.safe_load(f)['mappings']
        for key, df in data.items():
            columns = mappings[key]
            if columns:
                df.rename(columns=columns, inplace=True)


def normalize(data):
    customers = data['dim_customer']
    customers['first_name'] = customers['first_name'].str.strip()
    customers['last_name'] = customers["last_name"].str.strip()
    customers['email'] = customers['email'].str.strip()

    products = data['dim_product']
    products['category'] = products['category'].str.strip().str.capitalize()
    products['name'] = products['name'].str.strip()

    orders = data['fact_order']
    orders['status'] = orders['status'].str.strip().str.lower()


def validate(data):
    schema = DataFrameSchema({
        'id': Column(int, nullable=False),
        'email': Column(str, Check.str_matches(r'^[^@]+@[^@]+\.[^@]+$'), nullable=False),
        'first_name': Column(str, Check.str_matches(r'^[A-Za-z]{1,50}$'), nullable=False),
        'last_name': Column(str, Check.str_matches(r'^[A-Za-z]{1,50}$'), nullable=False)
    }, drop_invalid_rows=True)
    data['dim_customer'] = schema.validate(data['dim_customer'], lazy=True)

    schema = DataFrameSchema({
        'id': Column(int, nullable=False),
        'sku': Column(str, Check.str_length(20, 20), nullable=False),
        'category': Column(str, Check.str_length(1, 50), nullable=False),
        'name': Column(str, Check.str_length(1, 50), nullable=False),
        'price': Column(int, Check.gt(0), nullable=False)
    }, drop_invalid_rows=True)
    data['dim_product'] = schema.validate(data['dim_product'], lazy=True)

    schema = DataFrameSchema({
        'id': Column(int, nullable=False),
        'status': Column(str, Check.eq('delivered'), nullable=False),
        'created_at': Column(datetime, Check.le(pd.Timestamp.now()), nullable=False)
    }, drop_invalid_rows=True)
    data['fact_order'] = schema.validate(data['fact_order'], lazy=True)

    schema = DataFrameSchema({
        'id': Column(int, nullable=False),
        'quantity': Column(int, Check.gt(0), nullable=False),
        'unit_price': Column(int, Check.gt(0), nullable=False)
    }, drop_invalid_rows=True)
    data['fact_order_item'] = schema.validate(data['fact_order_item'], lazy=True)


def filter_data(data):
    valid_customer_ids = data['dim_customer']['id']
    valid_product_ids = data['dim_product']['id']
    data['fact_order'] = data['fact_order'][
        (data['fact_order']['status'] == 'delivered') &
        (data['fact_order']['customer_id'].isin(valid_customer_ids))
        ]
    valid_order_ids = data['fact_order']['id']
    data['fact_order_item'] = data['fact_order_item'][
        (data['fact_order_item']['order_id'].isin(valid_order_ids)) &
        (data['fact_order_item']['product_id'].isin(valid_product_ids))
        ].copy()
    orders_with_items = data['fact_order_item']['order_id'].unique()
    data['fact_order'] = data['fact_order'][
        data['fact_order']['id'].isin(orders_with_items)
    ].copy()


def add_total_price(data):
    order_items = data['fact_order_item']
    order_items['total_price'] = order_items['quantity'] * order_items['unit_price']
    data['fact_order'] = (order_items
                          .groupby('order_id')['total_price']
                          .sum()
                          .reset_index()
                          .merge(data['fact_order'], right_on='id', left_on='order_id', how='right'))


def add_dim_date(data):
    dt = data['fact_order']['created_at'].dt
    data['fact_order']['created_at_id'] = dt.strftime('%Y%m%d').astype(int)
    data['dim_date'] = pd.DataFrame({
        'id': data['fact_order']['created_at_id'],
        'full_date': dt.date,
        'year': dt.year,
        'month': dt.month,
        'day': dt.day,
    })
    data['dim_date'].drop_duplicates(subset=['id'], inplace=True)


def get_score(series, ascending=True, tiles=5):
    bins = pd.qcut(series, tiles, duplicates='drop')
    n = len(bins.cat.categories)
    start, end = tiles - n + 1, tiles + 1
    labels = list(range(start, end))
    if not ascending:
        labels = labels[::-1]
    return bins.cat.rename_categories(labels).astype(int)


def add_customer_metrics(data):
    today = datetime.today()
    r_agg = pd.NamedAgg(column='created_at', aggfunc=lambda dates: (today - dates.max()).days)
    f_agg = pd.NamedAgg(column='order_id', aggfunc='count')
    m_agg = pd.NamedAgg(column='total_price', aggfunc='sum')
    rfm = (data['fact_order']
           .groupby('customer_id')
           .agg(recency=r_agg, frequency=f_agg, monetary=m_agg)
           .reset_index())

    rfm['r_score'] = get_score(rfm['recency'], ascending=False)
    rfm['f_score'] = get_score(rfm['frequency'])
    rfm['m_score'] = get_score(rfm['monetary'])

    data['dim_customer'] = (data['dim_customer']
                            .merge(rfm, left_on='id', right_on='customer_id', how='left')
                            .reset_index()
                            .fillna({'r_score': 0, 'f_score': 0, 'm_score': 0, 'frequency': 0, 'monetary': 0}))

    data['dim_customer']['rfm_code'] = (
            data['dim_customer']['r_score'].astype(int).astype(str) +
            data['dim_customer']['f_score'].astype(int).astype(str) +
            data['dim_customer']['m_score'].astype(int).astype(str)
    )


def add_product_metrics(data):
    t_agg = pd.NamedAgg(column='total_price', aggfunc='sum')
    s_agg = pd.NamedAgg(column='quantity', aggfunc='sum')
    metrics = (data['fact_order_item']
               .groupby('product_id')
               .agg(turnover=t_agg, sales_count=s_agg)
               .reset_index())
    data['dim_product'] = (data['dim_product']
                           .merge(metrics, left_on='id', right_on='product_id', how='left')
                           .fillna({'turnover': 0, 'sales_count': 0}))


def filter_columns(data):
    data['dim_customer'] = data['dim_customer'][[
        'id',
        'last_name',
        'first_name',
        'email',
        'recency',
        'frequency',
        'monetary',
        'rfm_code'
    ]]
    data['dim_product'] = data['dim_product'][[
        'id',
        'sku',
        'name',
        'category',
        'price',
        'turnover',
        'sales_count'
    ]]
    data['fact_order'] = data['fact_order'][[
        'id',
        'created_at_id',
        'customer_id',
        'total_price'
    ]]
    data['fact_order_item'] = data['fact_order_item'][[
        'id',
        'order_id',
        'product_id',
        'quantity',
        'unit_price',
        'total_price'
    ]]


def transform(data: dict[str, pd.DataFrame]):
    map_field_names(data)
    normalize(data)
    validate(data)
    filter_data(data)
    add_dim_date(data)
    add_total_price(data)
    add_customer_metrics(data)
    add_product_metrics(data)
    filter_columns(data)
