import streamlit as st
import numpy as np
import time
import pandas as pd
import requests
import plotly.express as px
import streamlit.components.v1 as components

st.title("Graphing tools")

tab1, tab2, tab3, tab4 = st.tabs(
    ["eQTL visualizer", "eQTL browser", "Random graph generator", "CSV to graph converter"])

with tab1:
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
            df['-log10_p'] = -np.log10(df['pvalue'])
            df_filtered = df[df['pvalue'] <= pval_thresh]

            st.subheader("Top eQTL Associations")
            st.dataframe(
                df_filtered[['variant', 'beta', 'pvalue', '-log10_p', 'r2', 'maf']].sort_values('pvalue').head(20))

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

            st.subheader("Manhattan-style Plot")
            df_filtered['chr'], df_filtered['pos'] = df_filtered['variant'].str.split('_').str[0], \
                df_filtered['variant'].str.split('_').str[1].astype(int)
            fig2 = px.scatter(
                df_filtered,
                x='pos',
                y='-log10_p',
                color='chr',
                hover_data=['variant'],
                title=f"SNP Significance by Genomic Position",
                labels={"pos": "Position", "-log10_p": "-log10(p-value)"},
            )
            st.plotly_chart(fig2, use_container_width=True)

with tab2:
    components.iframe(
        "https://shiny.odap-ico.org/clx/eQTL/",
        width=800,
        height=600,
        scrolling=True
    )

with tab3:
    st.subheader("random graph generator")

    if st.button("Start"):
        coord = np.random.rand(1, 1)
        chart = st.line_chart(coord)

        with st.spinner("please wait...", show_time=True):
            progressbar = st.progress(0)
            for i in range(1, 30):
                new_coord = coord[-1] + np.random.rand(1, 1) * 2 - 1
                chart.add_rows(new_coord)
                coord = new_coord

                progressbar.progress(i / 30)
                time.sleep(0.1)

        progressbar.empty()

with tab4:
    st.subheader("CSV to graph converter")

    file = st.file_uploader("choose CSV file", type="csv")

    if file is not None:
        df = pd.read_csv(file)

        st.subheader("Data preview")
        st.write(df.head())

        st.write(df.describe())

        st.subheader("filter data")
        filteredColumns = st.selectbox("Choose column to filter", ['--choose column--'] + list(df.columns))

        if filteredColumns != '--choose column--':
            unique = df[filteredColumns].unique()

            value = st.selectbox("Choose value from filtered column", unique)
            final = df[df[filteredColumns] == value]
            st.write(final)

            x_value = st.selectbox("choose x values", df.columns)
            y_value = st.selectbox("choose y values", df.columns)

            if st.button("Generate plot"):
                st.line_chart(final.set_index(x_value)[y_value])
