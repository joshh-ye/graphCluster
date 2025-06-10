import streamlit as st
import numpy as np
import time
import pandas as pd

st.title("Graphing tools")

tab1, tab2 = st.tabs(["Random graph generator", "CSV to graph converter"])

with tab1:
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

                progressbar.progress(i/30)
                time.sleep(0.1)

        progressbar.empty()


with tab2:
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
