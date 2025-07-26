import pandas as pd
import plotly.express as px
import requests
import streamlit as st

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