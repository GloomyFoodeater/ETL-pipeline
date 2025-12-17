# TODO: Validate data
from datetime import datetime

import pandas as pd
import yaml

from etl.extract import extract
from utils.console import print_centered


def map_field_names(data):
    with open('../config.yaml', 'r', encoding='utf-8') as f:
        mappings = yaml.safe_load(f)['mappings']
        for key, df in data.items():
            columns = mappings[key]
            if columns:
                df.rename(columns=columns, inplace=True)


def filter_data(data):
    data['fact_order'] = data['fact_order'][data['fact_order']['status'] == 'Delivered']
    valid_order_ids = data['fact_order']['id']
    data['fact_order_item'] = data['fact_order_item'][data['fact_order_item']['order_id'].isin(valid_order_ids)]


def add_total_price(data):
    fact_order = data['fact_order']
    fact_order_item = data['fact_order_item']
    fact_order_item['total_price'] = fact_order_item['quantity'] * fact_order_item['unit_price']
    data['fact_order'] = (fact_order_item
                          .groupby('order_id')['total_price']
                          .sum()
                          .reset_index()
                          .merge(fact_order, right_on='id', left_on='order_id', how='right'))


def add_dim_date(data):
    dt = data['fact_order']['created_at'].dt
    data['fact_order']['created_at_id'] = dt.strftime('%Y%m%d%H%M%S').astype(int)
    data['dim_date'] = pd.DataFrame({
        'id': data['fact_order']['created_at_id'],
        'full_date': data['fact_order']['created_at'],
        'year': dt.year,
        'month': dt.month,
        'day': dt.day,
    })


def get_score(series, ascending=True, tiles=5):
    bins = pd.qcut(series, tiles, duplicates='drop')
    n = len(bins.cat.categories)
    start, end = tiles - n + 1, tiles + 1
    labels = list(range(start, end))
    if not ascending:
        labels = labels[::-1]
    return bins.cat.rename_categories(labels).astype(int)


def reverse_map(source):
    reversed = {}
    for k, values in source.items():
        for v in values:
            reversed[v] = k
    return reversed


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

    code_to_segment = reverse_map({
        'Champions': {'555', '554', '544', '545', '454', '455', '445'},
        'Loyal Customers': {'543', '444', '435', '355', '354', '345', '344', '335'},
        'Potential Loyalists': {'553', '551', '552', '541', '542', '533', '532', '531',
                                '452', '451', '442', '441', '431', '453', '433', '432',
                                '423', '353', '352', '351', '342', '341', '333', '323'},
        'New Customers': {'512', '511', '422', '421', '412', '411', '311'},
        'Promising': {'525', '524', '523', '522', '521', '515', '514', '513',
                      '425', '424', '413', '414', '415', '315', '314', '313'},
        'Need Attention': {'535', '534', '443', '434', '343', '334', '325', '324'},
        'About to sleep': {'331', '321', '312', '221', '213', '231', '241', '251'},
        'Cannot Lose Them': {'155', '154', '144', '214', '215', '115', '114', '113'},
        'At Risk': {'255', '254', '245', '244', '253', '252', '243', '242',
                    '235', '234', '225', '224', '153', '152', '145', '143',
                    '142', '135', '134', '133', '125', '124'},
        'Hibernating': {'332', '322', '233', '232', '223', '222', '132', '123',
                        '122', '212', '211'},
        'Lost Customers': {'111', '112', '121', '131', '141', '151'}
    })
    data['dim_customer']['segment'] = (data['dim_customer']['rfm_code']
                                       .map(code_to_segment)
                                       .fillna('Potential Customers'))


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
        'r_score',
        'f_score',
        'm_score',
        'rfm_code',
        'segment'
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
    filter_data(data)
    add_dim_date(data)
    add_total_price(data)
    add_customer_metrics(data)
    add_product_metrics(data)
    filter_columns(data)


if __name__ == '__main__':
    print('Extracting data...')
    data = extract()
    print('Transforming data...')
    print('Done!')
    transform(data)
    if data:
        print_centered('Transformed data', ' ')
        for (k, df) in data.items():
            print_centered(k)
            print(df.head())
