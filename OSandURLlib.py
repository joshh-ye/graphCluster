#learn python OS and urllib. Read url, import to txt and parse data into a dictionary.

from urllib.request import urlretrieve
import os


def parse_headers(header_line):
    return header_line.strip().split(',')


def parse_values(data_line):
    values = []
    for item in data_line.strip().split(','):
        if item == '':
            values.append(0.0)
        else:
            try:
                values.append(float(item))
            except ValueError:
                values.append(item)
    return values


def create_item_dict(values, headers):
    result = {}
    for value, header in zip(values, headers):
        result[header] = value
    return result


def read_csv(path):
    result = []
    # Open the file in read mode
    with open(path, 'r') as f:
        # Get a list of lines
        lines = f.readlines()
        # Parse the header
        headers = parse_headers(lines[0])
        # Loop over the remaining lines
        for data_line in lines[1:]:
            # Parse the values
            values = parse_values(data_line)
            # Create a dictionary using values & headers
            item_dict = create_item_dict(values, headers)
            # Add the dictionary to the result
            result.append(item_dict)
    return result

os.makedirs('./data', exist_ok=True)

url2 = 'https://gist.githubusercontent.com/aakashns/257f6e6c8719c17d0e498ea287d1a386/raw/7def9ef4234ddf0bc82f855ad67dac8b971852ef/loans2.txt'
urlretrieve(url2, './data/loans2.txt')

print(read_csv('./data/loans2.txt'))