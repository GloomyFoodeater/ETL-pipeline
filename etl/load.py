# TODO: Remake id generation logic
import os

import pandas as pd
import yaml
from sqlalchemy import create_engine, MetaData, Table, Column, String, CheckConstraint, ForeignKey, Date
from sqlalchemy.dialects.mysql import INTEGER, SMALLINT, TINYINT, BIGINT
from sqlalchemy_utils import database_exists, create_database, drop_database

from etl.extract import extract
from etl.transform import transform


def create_schema(engine):
    metadata_obj = MetaData()
    Table(
        'dim_customer',
        metadata_obj,
        Column('id', INTEGER(unsigned=True), primary_key=True),
        Column('last_name', String(50), nullable=False),
        Column('first_name', String(50), nullable=False),
        Column('email', String(100), nullable=False),
        Column('recency', INTEGER(unsigned=True)),
        Column('frequency', INTEGER(unsigned=True), nullable=False),
        Column('monetary', INTEGER(unsigned=True), nullable=False),
        Column('r_score', SMALLINT(unsigned=True), nullable=False),
        Column('f_score', SMALLINT(unsigned=True), nullable=False),
        Column('m_score', SMALLINT(unsigned=True), nullable=False),
        Column('rfm_code', String(3), nullable=False),
        Column('segment', String(50), nullable=False),
        CheckConstraint('r_score >= 0 AND r_score <= 5', name='r_score_check'),
        CheckConstraint('f_score >= 0 AND f_score <= 5', name='f_score_check'),
        CheckConstraint('m_score >= 0 AND m_score <= 5', name='m_score_check')
    )
    Table(
        'dim_date',
        metadata_obj,
        Column('id', BIGINT(unsigned=True), primary_key=True, autoincrement=False),
        Column('full_date', Date, nullable=False),
        Column('year', SMALLINT(unsigned=True), nullable=False),
        Column('month', TINYINT(unsigned=True), nullable=False),
        Column('day', TINYINT(unsigned=True), nullable=False)
    )
    Table(
        'dim_product',
        metadata_obj,
        Column('id', INTEGER(unsigned=True), primary_key=True),
        Column('sku', String(20), nullable=False),
        Column('category', String(50), nullable=False),
        Column('name', String(50), nullable=False),
        Column('price', SMALLINT(unsigned=True), nullable=False),
        Column('sales_count', INTEGER(unsigned=True), nullable=False),
        Column('turnover', INTEGER(unsigned=True), nullable=False)
    )
    Table(
        'fact_order',
        metadata_obj,
        Column('id', INTEGER(unsigned=True), primary_key=True),
        Column('customer_id', ForeignKey('dim_customer.id'), nullable=False),
        Column('created_at_id', ForeignKey('dim_date.id'), nullable=False),
        Column('total_price', INTEGER(unsigned=True), nullable=False)
    )
    Table(
        'fact_order_item',
        metadata_obj,
        Column('id', INTEGER(unsigned=True), primary_key=True),
        Column('order_id', ForeignKey('fact_order.id'), nullable=False),
        Column('product_id', ForeignKey('dim_product.id'), nullable=False),
        Column('quantity', SMALLINT(unsigned=True), nullable=False),
        Column('unit_price', SMALLINT(unsigned=True), nullable=False),
        Column('total_price', INTEGER(unsigned=True), nullable=False)
    )

    metadata_obj.create_all(engine)


def load(clean_data: dict[str, pd.DataFrame]) -> None:
    with open('./../config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    engine = create_engine(config['data_warehouse_url'])

    if os.getenv('env') == 'dev' and database_exists(engine.url):
        print('Dropping existing database...')
        drop_database(engine.url)

    if not database_exists(engine.url):
        print('Creating new database...')
        create_database(engine.url)
        create_schema(engine)

    with engine.begin() as connection:
        table_order = ['dim_date', 'dim_customer', 'dim_product', 'fact_order', 'fact_order_item']
        for table_name in table_order:
            clean_data[table_name].to_sql(table_name, con=connection, if_exists='append', index=False)


if __name__ == "__main__":
    print('Extracting data...')
    data = extract()
    print('Transforming data...')
    transform(data)
    load(data)
