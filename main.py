import streamlit as st
import numpy as np
import time
import pandas as pd
import requests
import plotly.express as px
import streamlit.components.v1 as components
import networkx as nx
from pyvis.network import Network
import tempfile
import os

st.title("Graphing tools")

# tab1, tab2, tab3, tab4, tab5 = st.tabs(
#     ["Drug knowledge graph", "eQTL visualizer", "eQTL browser", "Random graph generator", "CSV to graph converter"])

tab1, tab2, tab3, tab4 = st.tabs(
    ["eQTL browser", "Drug knowledge graph", "Random graph generator", "CSV to graph converter"])

with tab2:
    @st.cache_data
    def load_graph():
        df = pd.read_csv("data/kg.csv", low_memory=False)

        # Create directed graph
        G = nx.DiGraph()

        # Add nodes
        source_nodes = df[['x_id', 'x_name', 'x_type']].drop_duplicates()
        target_nodes = df[['y_id', 'y_name', 'y_type']].drop_duplicates()
        all_nodes = pd.concat([
            source_nodes.rename(columns={'x_id': 'id', 'x_name': 'name', 'x_type': 'type'}),
            target_nodes.rename(columns={'y_id': 'id', 'y_name': 'name', 'y_type': 'type'})
        ]).drop_duplicates('id')

        for _, row in all_nodes.iterrows():
            G.add_node(row['id'], label=row['name'], type=row['type'])

        # Add edges
        for _, row in df.iterrows():
            G.add_edge(row['x_id'], row['y_id'], label=row['relation'])

        return G


    def draw_graph(G):
        net = Network(height="750px", width="100%", directed=True)
        for node, data in G.nodes(data=True):
            net.add_node(node, label=data.get("label", node))
        for u, v, data in G.edges(data=True):
            net.add_edge(u, v, label=data.get("label", ""))

        # Create a temp file and immediately close it so it's not locked
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
        tmp_path = tmp.name
        tmp.close()

        # Let PyVis write to it
        net.save_graph(tmp_path)

        # Read, delete, and render
        with open(tmp_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        os.unlink(tmp_path)

        st.components.v1.html(html_content, height=800, scrolling=True)


    # App interface
    st.title("Drug ADE Knowledge Graph")
    G = load_graph()
    draw_graph(G)

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

# with tab3:
#     components.iframe(
#         "https://shiny.odap-ico.org/clx/eQTL/",
#         width=800,
#         height=600,
#         scrolling=True
#     )

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
