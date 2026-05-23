import os

import yaml
from sqlalchemy import create_engine, MetaData, Table, Column, String, ForeignKey, Date, text
from sqlalchemy.dialects.mysql import INTEGER, SMALLINT, TINYINT, BIGINT
from sqlalchemy_utils import database_exists, create_database, drop_database


def create_schema(engine):
    metadata_obj = MetaData()
    Table(
        "dim_customer",
        metadata_obj,
        Column("id", String(50), primary_key=True),
        Column("last_name", String(50), nullable=False),
        Column("first_name", String(50), nullable=False),
        Column("email", String(100), nullable=False),
        Column("recency", INTEGER(unsigned=True)),
        Column("frequency", INTEGER(unsigned=True), nullable=False),
        Column("monetary", INTEGER(unsigned=True), nullable=False),
        Column("rfm_code", String(3), nullable=False)
    )
    Table(
        "dim_date",
        metadata_obj,
        Column("id", BIGINT(unsigned=True), primary_key=True, autoincrement=False),
        Column("full_date", Date, nullable=False),
        Column("year", SMALLINT(unsigned=True), nullable=False),
        Column("month", TINYINT(unsigned=True), nullable=False),
        Column("day", TINYINT(unsigned=True), nullable=False)
    )
    Table(
        "dim_product",
        metadata_obj,
        Column("id", String(50), primary_key=True),
        Column("sku", String(20), nullable=False),
        Column("category", String(50), nullable=False),
        Column("name", String(50), nullable=False),
        Column("price", SMALLINT(unsigned=True), nullable=False),
        Column("sales_count", INTEGER(unsigned=True), nullable=False),
        Column("turnover", INTEGER(unsigned=True), nullable=False)
    )
    Table(
        "fact_order",
        metadata_obj,
        Column("id", String(50), primary_key=True),
        Column("customer_id", ForeignKey("dim_customer.id"), nullable=True),
        Column("created_at_id", ForeignKey("dim_date.id"), nullable=False),
        Column("total_price", INTEGER(unsigned=True), nullable=False)
    )
    Table(
        "fact_order_item",
        metadata_obj,
        Column("id", String(50), primary_key=True),
        Column("order_id", ForeignKey("fact_order.id"), nullable=False),
        Column("product_id", ForeignKey("dim_product.id"), nullable=False),
        Column("quantity", SMALLINT(unsigned=True), nullable=False),
        Column("unit_price", SMALLINT(unsigned=True), nullable=False),
        Column("total_price", INTEGER(unsigned=True), nullable=False)
    )

    metadata_obj.create_all(engine)


def load(data):
    data = {
        "dim_customer": data["customer"],
        "dim_product": data["product"],
        "fact_order": data["order"],
        "fact_order_item": data["order_item"],
        "dim_date": data["dim_date"],
    }
    
    with open("../config.yaml", "r") as f:
        config = yaml.safe_load(f)

    engine = create_engine(config["data_warehouse_url"])

    if os.getenv("env") == "dev" and database_exists(engine.url):
        print("Dropping existing database...")
        drop_database(engine.url)

    if not database_exists(engine.url):
        print("Creating new database...")
        create_database(engine.url)
        create_schema(engine)

    with engine.begin() as connection:
        if engine.dialect.name == "mysql":
            connection.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        truncate_order = ["fact_order_item", "fact_order", "dim_product", "dim_customer", "dim_date"]
        for table_name in truncate_order:
            connection.execute(text(f"TRUNCATE TABLE {table_name}"))
        if engine.dialect.name == "mysql":
            connection.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

        table_order = ["dim_date", "dim_customer", "dim_product", "fact_order", "fact_order_item"]
        for table_name in table_order:
            data[table_name].to_sql(table_name, con=connection, if_exists="append", index=False)
