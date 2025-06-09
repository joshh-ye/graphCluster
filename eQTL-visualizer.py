import streamlit as st
import requests
import pandas as pd

urlDataset = 'https://www.ebi.ac.uk/eqtl/api/v2/datasets'
r = requests.get(urlDataset)
datasets = r.json()

final = pd.DataFrame(datasets)

st.write(final)

urlData = 'https://www.ebi.ac.uk/eqtl/api/v2/datasets/QTD000001/associations'
r = requests.get(urlData)
eQTL_Data = r.json()
final2 = pd.DataFrame(eQTL_Data)

st.write(final2)

urlData = 'https://www.ebi.ac.uk/eqtl/api/v2/datasets/QTD000001'
r = requests.get(urlData)
eQTL_Data = r.json()
final2 = pd.DataFrame(eQTL_Data)