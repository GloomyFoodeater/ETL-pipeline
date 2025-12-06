from datetime import datetime

import pandas as pd
import yaml

from etl.extract import extract
from utils.console import print_centered


def map_and_filter_columns(data: dict[str, pd.DataFrame]):
    with open("../config/mappings.yaml", "r", encoding="utf-8") as f:
        columns = yaml.safe_load(f)
        for key, df in data.items():
            mapping = columns[key]
            if mapping:
                col_to_keep = mapping.keys()
                col_to_rename = {k: v for k, v in mapping.items() if v is not None}
                # TODO: Decide whether to filter columns
                data[key] = df[col_to_keep].rename(columns=col_to_rename)


def add_total_price(data: dict[str, pd.DataFrame]):
    fact_order = data['fact_order']
    fact_order_item = data['fact_order_item']

    fact_order_item['total_price'] = fact_order_item['quantity'] * fact_order_item['unit_price']
    data['fact_order'] = fact_order_item \
        .groupby('order_id')['total_price'] \
        .sum() \
        .reset_index() \
        .merge(fact_order, right_on='id', left_on='order_id', how='right')


def add_product_id(data: dict[str, pd.DataFrame]):
    # TODO: Decide what to do with product id (id is taken as it is, sku can be used as a foreign key)
    # data['dim_product']['id'] = range(1, len(data['dim_product']) + 1)
    data['fact_order_item'] = data['fact_order_item'].merge(
        data['dim_product'][['id', 'sku']],
        left_on='product_sku',
        right_on='sku',
        how='left'
    ).rename(columns={'id_x': 'id', 'id_y': 'product_id'})


def get_season(month):
    if month in (12, 1, 2):
        return 'Winter'
    elif month in (3, 4, 5):
        return 'Spring'
    elif month in (6, 7, 8):
        return 'Summer'
    else:  # 9, 10, 11
        return 'Autumn'


def add_dim_date(data: dict[str, pd.DataFrame]):
    dates = data['fact_order']['created_at'].dt
    data['fact_order']['created_at_id'] = dates.strftime('%Y%m%d%H%M%S').astype(int)
    data['dim_date'] = pd.DataFrame({
        'id': data['fact_order']['created_at_id'],
        'full_date': data['fact_order']['created_at'],
        'quarter': dates.quarter,
        'year': dates.year,
        'month': dates.month,
        'month_name': dates.strftime('%B'),
        'day': dates.day,
        'day_of_week': dates.dayofweek + 1,  # ISO: Monday=1
        'day_name': dates.strftime('%A'),
        'week_of_year': dates.isocalendar().week,
        'season': dates.month.map(get_season),
        'is_weekend': dates.dayofweek >= 5
    })


def calculate_rfm(data: dict[str, pd.DataFrame]):
    today = datetime.today()
    orders = data['fact_order']

    # TODO: Set period for metrics calculation
    # TODO: Decide whether metrics should be stored data
    # TODO: Decide whether metrics are updated only once a day
    data['customer_rfm'] = orders.groupby('customer_id').agg(
        recency=pd.NamedAgg(column='created_at', aggfunc=lambda x: (today - x.max()).days),
        frequency=pd.NamedAgg(column='order_id', aggfunc='count'),
        monetary=pd.NamedAgg(column='total_price', aggfunc='sum')
    ).reset_index()

    # TODO: Decide whether to fill rfm with NULLs for customers without orders
    # data['customer_rfm'] = data['dim_customer'].merge(data['customer_rfm'], left_on='id', right_on='customer_id', how='left')


def transform(data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    map_and_filter_columns(data)
    add_total_price(data)
    add_product_id(data)
    add_dim_date(data)
    calculate_rfm(data)

    return data


if __name__ == "__main__":
    print_centered('Extracting data...')
    data = extract()
    print_centered('Transforming data...')
    data = transform(data)
    if data:
        print_centered('Transformed data')
        for (k, df) in data.items():
            print_centered(k)
            print(df.head())
    print_centered('Done!')
