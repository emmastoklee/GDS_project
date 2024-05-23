import streamlit as st
import pandas as pd
import geopandas as gpd
import pickle

from tools.ui_utils import (
    add_logo,
    ui_setup
)

from tools.utils import (
    plot_neighborhood_graph
)

add_logo()
ui_setup()

st.subheader("Detailed neighbourhood analysis")
st.write("Make your data input in the sidebar and wait for the analysis to run.") 
st.write("The output **graph plot** can help you to **find the best areas within each neighbourhood depending on your amenity of interest**.")


st.divider()
st.write("The plot displays:")
st.write("**Time in minutes** to reach the **nearest selected amenity by selected mode of transportation**.")

# store all neighborhoods
amenities_with_neighborhood = gpd.read_file('dataframes/amenities_with_neighborhood.geojson')

neighbourhoods = list(amenities_with_neighborhood['Arrondissement'].unique())[:-1]
neighbourhoods = sorted([item.split(',')[0] for item in neighbourhoods])

amenities = sorted(amenities_with_neighborhood.amenity.unique())

# store distances in session state for use in plotting
if "distances_dict" not in st.session_state:

    walking_distances = pd.read_parquet('distances/walking_distances.parquet')
    biking_distances = pd.read_parquet('distances/biking_distances.parquet')
    driving_distances = pd.read_parquet('distances/driving_distances.parquet')

    # distances to dict
    st.session_state["distances_dict"] = {
        "walking": walking_distances,
        "biking": biking_distances,
        "driving": driving_distances
    }

# store graphs in session state for use in plotting
if "graphs_dict" not in st.session_state:
    
    biking_graphs_file = 'graphs/biking_graphs.pkl'
    walking_graphs_file = 'graphs/walking_graphs.pkl'
    driving_graphs_file = 'graphs/driving_graphs.pkl'
    with open(driving_graphs_file, 'rb') as file:
        driving_graphs = pickle.load(file)    
    with open(walking_graphs_file, 'rb') as file:
        walking_graphs = pickle.load(file)
    with open(biking_graphs_file, 'rb') as file:
        biking_graphs = pickle.load(file)

    # graphs dict
    st.session_state["graphs_dict"] = {
        "walking": walking_graphs,
        "biking": biking_graphs,
        "driving": driving_graphs
    }


with st.sidebar:
    st.session_state["mode_of_transportation"] = st.selectbox("Mode of transportation",
                                                            ("walking", "biking", "driving",),
                                                            placeholder = "Select a mode of transportation.")
    st.session_state["amenity"] = st.selectbox("Amenity",
                                            amenities,
                                            placeholder="Select your amenity of interest.")
    
    st.session_state["neighbourhood"] = st.selectbox("Neighbourhood",
                                                    neighbourhoods,
                                                    placeholder="Select a neighbourhood.")
    
    start_button = st.button("Start analysis 🚀")

# kicking off the plotting in the app
if start_button:
    with st.spinner("Your analysis is running in the background."):
        
        plot_neighborhood_graph(
                                transportation_type=st.session_state["mode_of_transportation"],
                                neighbourhood=st.session_state["neighbourhood"],
                                distances_by_transportation=st.session_state.distances_dict[st.session_state["mode_of_transportation"]],
                                graphs_dict=st.session_state.graphs_dict,
                                amenity=st.session_state["amenity"]
                                )
        
        st.write("*Note 1: Nodes represent intersections of lanes (as stored in OpenStreetMap) and edges represent lanes/streets. Node colouring will always reflect a 0-15 minutes scale. And if nodes are coloured black, travel times exceed 15 minutes.*")

st.sidebar.write("Choose different site options above.")