from urllib.request import urlretrieve
import os

url2 = 'https://gist.githubusercontent.com/aakashns/257f6e6c8719c17d0e498ea287d1a386/raw/7def9ef4234ddf0bc82f855ad67dac8b971852ef/loans2.txt'
urlretrieve(url2, './data/loans2.txt')

