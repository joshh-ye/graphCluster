import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import tempfile
import os

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
