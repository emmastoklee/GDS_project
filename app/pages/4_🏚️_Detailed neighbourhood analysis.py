# caro's plotting goes in here

# select the mode of transportation -> get the right graph for the mode
# select an amenity from preloaded list -> save in session state
# select a neighborhood for closer analysis
# get both in function

import streamlit as st
import pandas as pd
from tools.ui_utils import (
    add_logo,
    ui_setup
)

add_logo()
ui_setup()

st.subheader("Detailed neighbourhood analysis")
st.write("Make your data input in the sidebar and wait for the analysis to run.")

montreal_map = pd.DataFrame({
    'lat': [45.5017],
    'lon': [-73.5673]
})

with st.sidebar:
    st.selectbox("Mode of transportation",("Walking", "Biking", "Driving", "Public transport"))
    st.selectbox("Amenity",("Supermarket", "Pharmacy", "General practitioner", "School/university", "Café", "Park/green area", "Public water access", "Library", "Place of worship", "Bar", "Restaurants"))
    
    start_button = st.button("Use these choices.")
    
if start_button:
    with st.spinner("Your analysis is running in the background."):
        import time
        time.sleep(10)
        st.success("Finished - let's have a look at your best living location in Montreal.")
        
        # map: change of zoom and color possible
        st.map(montreal_map, zoom=10) 
        

st.sidebar.write("Choose different site options above.")