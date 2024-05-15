# caro's plotting goes in here

# select the mode of transportation -> get the right graph for the mode
# select an amenity from preloaded list -> save in session state
# select a neighborhood for closer analysis
# get both in function

import streamlit as st
import pandas as pd
import osmnx as ox
import geopandas as gpd
import os
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
st.write("Make your data input in the sidebar and wait for the analysis to run. The output graph plot can help you find the best areas within each neighbourhood.")


st.divider()
st.write("The plot displays the **time in minutes to reach the nearest selected amenity by selected mode of transportation**.")

# store all neighborhoods
amenities_with_neighborhood = gpd.read_file('../dataframes/amenities_with_neighborhood.geojson')

neighbourhoods = list(amenities_with_neighborhood['Arrondissement'].unique())[:-1]
neighbourhoods = [item.split(',')[0] for item in neighbourhoods]

amenities = amenities_with_neighborhood.amenity.unique()

if "distances_dict" not in st.session_state:

#     def join_large_pickles(read_size=100000000):
#         combined_dict = dict()
#         parts = ['../distances/walking_dist1.pkl','../distances/walking_dist2.pkl']
        
#         for file in parts:
#             input_file = open(file, 'rb')
#             while True:
#                 bytes = input_file.read(read_size)
#                 if not bytes:
#                     break
#                 combined_dict.update(pickle.load(bytes))
#             # with open(file, 'rb') as input_file:
#             #     # Load the dictionary from the pickle file
#             #     part_dict = pickle.load(input_file)
                
#             #     # Merge the dictionaries
#             #     combined_dict.update(part_dict)
        
#         return combined_dict

#     walking_distances = join_large_pickles()
    # walking_distances = st.session_state["walking_distances"]
    # biking_dist_file = '../distances/biking_dist.pkl'
    # driving_dist_file = '../distances/driving_dist.pkl'
    # with open(driving_dist_file, 'rb') as file:
    #     driving_distances = pickle.load(file)    
    # with open(biking_dist_file, 'rb') as file:
    #     biking_distances = pickle.load(file)
    # read in all pre-calculated distances (for walk, drive, bike)
    walking_distances = pd.read_parquet('../distances/walking_distances.parquet')
    biking_distances = pd.read_parquet('../distances/biking_distances.parquet')
    driving_distances = pd.read_parquet('../distances/driving_distances.parquet')

    # distances to dict
    st.session_state["distances_dict"] = {
        "walking": walking_distances,
        "biking": biking_distances,
        "driving": driving_distances
    }

if "graphs_dict" not in st.session_state:
    biking_graphs_file = '../graphs/biking_graphs.pkl'
    walking_graphs_file = '../graphs/walking_graphs.pkl'
    driving_graphs_file = '../graphs/driving_graphs.pkl'
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


if start_button:
    with st.spinner("Your analysis is running in the background."):
        
        plot_neighborhood_graph(
                                transportation_type=st.session_state["mode_of_transportation"],
                                neighbourhood=st.session_state["neighbourhood"],
                                distances_by_transportation=st.session_state.distances_dict[st.session_state["mode_of_transportation"]],
                                graphs_dict=st.session_state.graphs_dict,
                                amenity=st.session_state["amenity"]
                                )
# if start_button:
#     with st.spinner("Your analysis is running in the background."):
#         def get_graph(mode_of_transportation, neighbourhood):
#             G = ox.graph_from_place(neighbourhood + ', Montreal, Quebec, Canada', network_type=mode_of_transportation)
#             return G
#         # map selected transportation to graph
#         G = get_graph(st.session_state["mode_of_transportation"], st.session_state["neighbourhood"])
        
#         # THIS NEEDS TO BE REFINED
#         plot_neighborhood_graph(mode_of_transportation_graph=G, 
#                                 mode_of_transportation_distances = "TO BE FILLED", 
#                                 neighbourhood = st.session_state["neighbourhood"])

st.sidebar.write("Choose different site options above.")