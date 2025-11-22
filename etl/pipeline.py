from etl.extract import extract
from etl.load import load
from etl.transform import transform
from utils.console import print_centered

if __name__ == '__main__':
    print_centered('Extracting data...')
    raw_data = extract()
    print_centered('Transforming data...')
    clean_data = transform(raw_data)
    print_centered('Saving data...')
    load(clean_data)
    print_centered('Done!')
