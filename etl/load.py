# TODO: Remake id generation logic
import os

import pandas as pd
import yaml
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database, drop_database

from etl.extract import extract
from etl.transform import transform


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
    with engine.begin() as connection:
        for table_name, df in clean_data.items():
            df.to_sql(table_name, con=connection, if_exists='replace', index=False)


if __name__ == "__main__":
    print('Extracting data...')
    data = extract()
    print('Transforming data...')
    transform(data)
    load(data)
