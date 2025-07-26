import os
import tempfile
import networkx as nx
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

tab1, tab2, tab3 = st.tabs(
    ["GWAS search", "eQTL browser", "Drug knowledge graph"])

with tab1:
    st.title('GWAS search')
    search_term = st.text_input('Enter gene name or PMID ')
    data = pd.read_csv('CRC risk genelists.csv')

    if search_term:  # Only filter if a search term is provided
        filtered_df = data[data['Genes'].str.contains(search_term, case=False)]
        st.write(filtered_df)
    else:
        st.write(data)

with tab2:
    st.title("eQTL Browser")
    st.sidebar.title("Query Parameters (for eQTL browser")

    # Sidebar: Input options
    entry_limit = st.sidebar.slider("Choose number of entries for table", 0, 1000, 500)
    pval_thresh = st.sidebar.slider("P-value threshold", 0.0, 1.0, 0.05, 0.001)

    # Query eQTL API
    query_params = {
        "size": entry_limit,
    }

    search_option = st.sidebar.selectbox("Which search method would you like to use?",
                                         ("gene_id", "RSID", "gene name"), )

    if search_option == "gene_id":
        gene_id = st.sidebar.text_input("Enter Ensembl Gene ID", value="ENSG00000188157")
        query_params["gene_id"] = gene_id
    elif search_option == "RSID":
        rsid = st.sidebar.text_input("Enter RSID", value="rs200141179")
        query_params["rsid"] = rsid
    else:
        try:
            gene_name = st.sidebar.text_input("Enter gene name (all CAPS)", value="AGRN")
            response = requests.get(
                f'https://rest.ensembl.org/xrefs/symbol/homo_sapiens/{gene_name}?content-type=application/json')
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            st.error(f"HTTP error {response.status_code}: {response.text}")
        studies = response.json()
        query_params["gene_id"] = studies[0]["id"]


    @st.cache_data
    def fetch_data(query_params):
        try:
            response = requests.get('https://www.ebi.ac.uk/eqtl/api/v2/datasets/QTD000370/associations?start=0&size=20',
                                    params=query_params)
            response.raise_for_status()
            try:
                data = response.json()
            except ValueError:
                st.error(f"Failed to parse JSON. Response text: {response.text}")
                return None
            return data
        except requests.exceptions.HTTPError as e:
            st.error(f"HTTP error {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Request error: {e}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")
        return None


    try:
        with st.spinner("Loading data", show_time=True):
            api_response = fetch_data(query_params)

        st.title("All data")
        df = pd.DataFrame(api_response)
        st.write(df)

        # p_value filter
        st.title("Filtered p-value data")
        association_df = df[df['pvalue'] <= pval_thresh]
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

with tab3:
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