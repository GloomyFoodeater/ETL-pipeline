from extract import extract
from load import load
from transform import transform

if __name__ == '__main__':
    print("Extracting data...")
    data = extract()
    print("Transforming data...")
    transform(data)
    print("Saving data...")
    load(data)
    print("Done!")
