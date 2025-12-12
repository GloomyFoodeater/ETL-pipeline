from etl.extract import extract
from etl.load import load
from etl.transform import transform

if __name__ == '__main__':
    print('Extracting data...')
    data = extract()
    print('Transforming data...')
    transform(data)
    print('Saving data...')
    load(data)
    print('Done!')
