import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database, drop_database

from etl.extract import extract
from etl.transform import transform
from utils.console import print_centered


def load(clean_data: dict[str, pd.DataFrame]) -> None:
    engine = create_engine("mysql://root:admin@localhost:3306/e_commerce_dw")
    # TODO: To dev this
    if database_exists(engine.url):
        drop_database(engine.url)
    if not database_exists(engine.url):
        create_database(engine.url)
    with engine.begin() as connection:
        for table_name, df in clean_data.items():
            df.to_sql(table_name, con=connection, if_exists='replace', index=False)

if __name__ == "__main__":
    print_centered('Extracting data...')
    data = extract()
    print_centered('Transforming data...')
    data = transform(data)
    load(data)