#learn python OS and urllib. Read url, import to txt and parse data into a dictionary.

from urllib.request import urlretrieve
import os


#EMI calculation
import math

def loan_emi(amount, duration, rate, down_payment=0):
    """Calculates the equal montly installment (EMI) for a loan.

    Arguments:
        amount - Total amount to be spent (loan + down payment)
        duration - Duration of the loan (in months)
        rate - Rate of interest (monthly)
        down_payment (optional) - Optional intial payment (deducted from amount)
    """
    loan_amount = amount - down_payment
    try:
        emi = loan_amount * rate * ((1+rate)**duration) / (((1+rate)**duration)-1)
    except ZeroDivisionError:
        emi = loan_amount / duration
    emi = math.ceil(emi)
    return emi

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

#function adds emi value to list of dictionary lines.
def addEmi(resultAbove):
    for result in resultAbove:
        result['emi'] = str(loan_emi(result['amount'], result['duration'],result['rate'],result['down_payment']))


os.makedirs('./data', exist_ok=True)

url2 = 'https://gist.githubusercontent.com/aakashns/257f6e6c8719c17d0e498ea287d1a386/raw/7def9ef4234ddf0bc82f855ad67dac8b971852ef/loans2.txt'
urlretrieve(url2, './data/loans2.txt')

loans2 = read_csv('./data/loans2.txt')
addEmi(loans2)

# write loans2 to a csv file
def toCSVfile(datas, path):
    with open(path, 'w') as f:
        if len(datas) == 0:
            return None
        header = list(datas[0].keys())
        f.write(','.join(header) + '\n')

        for data in datas[0:]:
            values = []
            for head in header:
                values.append(str(data[head]))
            f.write(','.join(values) + '\n')



toCSVfile(loans2, './data/loans2.csv')

#pandas dataframe
import pandas as pd

print(pd.read_csv('./data/loans2.csv'))

#second method of csv.

pd.DataFrame(loans2).to_csv('./data/loans2COPY.csv', index = None)