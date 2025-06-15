import streamlit as st
import numpy as np
import pandas as pd
import requests
import plotly.express as px

st.title("eQTL Browser")

# choosing data from list of datasets
dataSetsURL = st.text_input("Enter url to dataset", value='https://www.ebi.ac.uk/eqtl/api/v2/datasets')

dataSetDataFrame = pd.DataFrame(requests.get(dataSetsURL).json())
st.write(dataSetDataFrame)

method = st.selectbox('Choose method', ['--select dataset--'] + list(dataSetDataFrame['quant_method']))

if method != '--select dataset--':

    # Sidebar: Input options
    st.sidebar.header("Query Options")
    gene_id = st.sidebar.text_input("Enter Ensembl Gene ID", value="ENSG00000215014")
    pval_thresh = st.sidebar.slider("P-value threshold", 0.0, 1.0, 1.0, 0.001)

    st.header("dataSet QTD000001")


    # Query eQTL API
    def fetch_eqtl_data(gene_id):
        url = f"https://www.ebi.ac.uk/eqtl/api/v2/datasets/QTD000001/associations"
        r = requests.get(url)
        if r.status_code != 200:
            st.error(f"Failed to retrieve data: {r.status_code}")
            return pd.DataFrame()

        data = r.json()
        df = pd.DataFrame(data)
        return df[df['gene_id'] == 'ENSG00000215014']


    # Load and filter data
    userDict = dataSetDataFrame[dataSetDataFrame['quant_method'] == method]
    df = fetch_eqtl_data(gene_id)
    st.write(df)

    if df.empty:
        st.warning("No data found for the given gene ID.")
    else:

        start, end = st.sidebar.slider(
            label="choose range",
            min_value=-1000,
            max_value=1000,
            value=(-100, 100),
            step=1,
        )

        df['-log10_p'] = -np.log10(df['pvalue'])
        df_filtered = df[df['pvalue'] <= pval_thresh]



        st.subheader("Top eQTL Associations")
        st.dataframe(
            df_filtered[['variant', 'beta', 'pvalue', '-log10_p', 'r2', 'maf']].sort_values('pvalue').head(20))

        plotV = st.checkbox("PLot graphs")

        if plotV:
            st.subheader("Volcano Plot")
            fig = px.scatter(
                df_filtered,
                x='beta',
                y='-log10_p',
                hover_data=['variant'],
                title=f"Volcano Plot for {gene_id}",
                labels={"beta": "Effect Size (β)", "-log10_p": "-log10(p-value)"},
            )
            st.plotly_chart(fig, use_container_width=True)

        plotLD = st.checkbox("PLot LD graph")

        if plotLD:


            # sidebar for LD plot
            median_value = df_filtered['variant'].str.split('_').str[1].astype(int).median()

            st.subheader("LD plot")
            df_filtered['chr'], df_filtered['pos'] = df_filtered['variant'].str.split('_').str[0], \
                df_filtered['variant'].str.split('_').str[1].astype(int)

            fig2 = px.scatter(
                df_filtered,
                x='pos',
                y='r2',
                color='chr',
                hover_data=['variant'],
                title=f"SNP Significance by Genomic Position",
                labels={"pos": "Position", "r2": "r^2"},
                range_x=(median_value + start, median_value + end)

            )
            st.plotly_chart(fig2, use_container_width=True)
