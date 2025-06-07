import streamlit as st
import numpy as np
import time

st.title("random graph generator")

if st.button("Start"):
    coord = np.random.rand(1, 1)
    chart = st.line_chart(coord)

    with st.spinner("please wait...", show_time=True):
        progressbar = st.sidebar.progress(0)
        for i in range(1, 30):
            new_coord = coord[-1] + np.random.rand(1, 1) * 2 - 1
            chart.add_rows(new_coord)
            coord = new_coord

            progressbar.progress(i/30)
            time.sleep(0.1)

    progressbar.empty()
    st.button("Rerun")