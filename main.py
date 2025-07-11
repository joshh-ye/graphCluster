import os
import tempfile
import time

import networkx as nx
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

# tab1, tab2, tab3, tab4 = st.tabs(
#     ["eQTL browser", "Drug knowledge graph", "Random graph generator", "CSV to graph converter"])

tab1, tab2 = st.tabs(
    ["eQTL browser", "Drug knowledge graph"])

with tab1:
    st.title("eQTL Browser")
    st.sidebar.title("query paramaters")

    # Sidebar: Input options
    entry_limit = st.sidebar.slider("Choose number of entries for table", 0, 1000, 50)
    search_option = st.sidebar.selectbox("Which search method would you like to use?",
                                         ("gene_id", "RSID", "gene name"), )

    id = ""
    if search_option == "gene_id":
        id = st.sidebar.text_input("Enter Ensembl Gene ID", value="ENSG00000215014")
    else:
        id = st.sidebar.text_input("Enter RSID", value="rs200141179")

    quant_methods = ["ge", "exon", "microarray", "tx", "txrev"]
    selected_method = st.sidebar.selectbox("Choose quantification method", quant_methods, index=0)
    pval_thresh = st.sidebar.slider("P-value threshold", 0.0, 1.0, 0.05, 0.001)

    # Query eQTL API
    query_params = {
        "size": entry_limit,
        "p_upper": pval_thresh,
        "quant_method": selected_method
    }


    @st.cache_data
    def fetch_data(search_option, id, query_params):
        if search_option == "gene_id":
            api_response = requests.get(f'https://www.ebi.ac.uk/eqtl/api/genes/{id}/associations',
                                        params=query_params).json()
        elif search_option == "RSID":
            api_response = requests.get(f'https://www.ebi.ac.uk/eqtl/api/associations/{id}',
                                        params=query_params).json()
        else:
            api_response = 'https://www.ebi.ac.uk/eqtl/api/associations'
        return api_response


    try:
        with st.spinner("Loading data", show_time=True):
            progress_text = "Operation in progress. Please wait."
            my_bar = st.progress(0, text=progress_text)

            total_time=35
            steps=100
            delay=total_time/steps
            for percent_complete in range(100):
                time.sleep(delay)
                my_bar.progress(percent_complete + 1, text=progress_text)
            time.sleep(1)
            my_bar.empty()
            api_response = fetch_data(search_option, id, query_params)

        association_df = pd.DataFrame(list(api_response['_embedded']['associations'].values()))
        st.write(association_df)

        # Compute genomic position range for slider
        pos_min = int(association_df['position'].min())
        pos_max = int(association_df['position'].max())

        if pos_min < pos_max:
            start_pos, end_pos = st.sidebar.slider(
                "Select genomic position range",
                min_value=pos_min,
                max_value=pos_max,
                value=(pos_min, pos_max),
                step=1,
            )
        else:
            # only one unique position: no need to slide
            start_pos = end_pos = pos_min

        st.subheader("Pearson Plot")

        fig = px.scatter(
            association_df,
            x='position',
            y='r2',
            title='r² vs. Genomic Position',
            hover_data=['variant'],
            labels={"position": "Position", "r2": "r²"},
            range_x=(start_pos, end_pos)
        )
        st.plotly_chart(fig)

    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
    except ValueError:
        st.error("Response is not valid JSON.")

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

# with tab3:
#     st.subheader("random graph generator")
#
#     if st.button("Start"):
#         coord = np.random.rand(1, 1)
#         chart = st.line_chart(coord)
#
#         with st.spinner("please wait...", show_time=True):
#             progressbar = st.progress(0)
#             for i in range(1, 30):
#                 new_coord = coord[-1] + np.random.rand(1, 1) * 2 - 1
#                 chart.add_rows(new_coord)
#                 coord = new_coord
#
#                 progressbar.progress(i / 30)
#                 time.sleep(0.1)
#
#         progressbar.empty()
#
# with tab4:
#     st.subheader("CSV to graph converter")
#
#     file = st.file_uploader("choose CSV file", type="csv")
#
#     if file is not None:
#         df = pd.read_csv(file)
#
#         st.subheader("Data preview")
#         st.write(df.head())
#
#         st.write(df.describe())
#
#         st.subheader("filter data")
#         filteredColumns = st.selectbox("Choose column to filter", ['--choose column--'] + list(df.columns))
#
#         if filteredColumns != '--choose column--':
#             unique = df[filteredColumns].unique()
#
#             value = st.selectbox("Choose value from filtered column", unique)
#             final = df[df[filteredColumns] == value]
#             st.write(final)
#
#             x_value = st.selectbox("choose x values", df.columns)
#             y_value = st.selectbox("choose y values", df.columns)
#
#             if st.button("Generate plot"):
#                 st.line_chart(final.set_index(x_value)[y_value])
