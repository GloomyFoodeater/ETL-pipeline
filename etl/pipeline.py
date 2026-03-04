from extract import extract_sql_source
from load import load
from transform import transform

if __name__ == '__main__':
    print("Extracting data...")
    data = extract_sql_source()
    print("Transforming data...")
    transform(data)
    print("Saving data...")
    load(data)
    print("Done!")
