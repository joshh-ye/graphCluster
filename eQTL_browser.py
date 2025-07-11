import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.title("eQTL Browser")
st.sidebar.title("query paramaters")

# Sidebar: Input options
entry_limit = st.sidebar.slider("Choose number of entries for table", 0, 1000, 50)
search_option = st.sidebar.selectbox("Which search method would you like to use?", ("gene_id", "RSID", "gene name"), )

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
