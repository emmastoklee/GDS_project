# caro's plotting goes in here

# select the mode of transportation -> get the right graph for the mode
# select an amenity from preloaded list -> save in session state
# select a neighborhood for closer analysis
# get both in function

import streamlit as st
import pandas as pd
import osmnx as ox
import geopandas as gpd
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

def get_graph(mode_of_transportation, neighbourhood):
    G = ox.graph_from_place(neighbourhood + ', Montreal, Quebec, Canada', network_type=mode_of_transportation)
    return G

# store all neighborhoods
amenities_with_neighborhood = gpd.read_file('../dataframes/amenities_with_neighborhood.geojson')
neighbourhoods = list(amenities_with_neighborhood['Arrondissement'].unique())[:-1]
neighbourhoods = [item.split(',')[0] for item in neighbourhoods]

# read in all pre-calculated distances here already (for walk, drive, bike)
# distances = pd.read_csv('../dataframes/distances.csv')


with st.sidebar:
    st.session_state["mode_of_transportation"] = st.selectbox("Mode of transportation",
                                                            ("Walking", "Biking", "Driving",),
                                                            placeholder = "Select a mode of transportation.")
    st.session_state["amenity"] = st.selectbox("Amenity",
                                            ("Supermarket", "Pharmacy", "General practitioner", "School/university", "Café", "Park/green area", "Public water access", "Library", "Place of worship", "Bar", "Restaurants"),
                                            placeholder="Select your amenity of interest.")
    
    st.session_state["neighbourhood"] = st.selectbox("Neighbourhood",
                                                    neighbourhoods,
                                                    placeholder="Select a neighbourhood.")
    
    start_button = st.button("Use these choices.")
    
if start_button:
    with st.spinner("Your analysis is running in the background."):
        
        # map selected transportation to graph
        G = get_graph(st.session_state["mode_of_transportation"], st.session_state["neighbourhood"])
        
        
        import time
        time.sleep(10)
        st.success("Finished - let's have a look at your best living location in Montreal.")
        
        # map: change of zoom and color possible
        st.map(montreal_map, zoom=10) 
        

st.sidebar.write("Choose different site options above.")