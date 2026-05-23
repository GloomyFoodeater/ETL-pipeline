from datetime import datetime, timedelta
from airflow.decorators import dag, task

from etl.extract import extract_api_source
from extract import extract_sql_source
from load import load
from transform import transform

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

@dag(
    dag_id='etl_pipeline_dag',
    default_args=default_args,
    description='ETL pipeline using SQL and API sources',
    schedule_interval='@daily',
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['etl'],
)
def etl_pipeline():
    @task()
    def extract_sql():
        print("Extracting SQL data...")
        return extract_sql_source()

    @task()
    def extract_api():
        print("Extracting API data...")
        return extract_api_source()

    @task()
    def transform_data(sql_data, api_data):
        print("Transforming data...")
        return transform(sql_data, api_data)

    @task()
    def load_data(transformed_data):
        print("Saving data...")
        load(transformed_data)
        print("Done!")

    sql_res = extract_sql()
    api_res = extract_api()
    transformed_res = transform_data(sql_res, api_res)
    load_data(transformed_res)

etl_dag = etl_pipeline()
