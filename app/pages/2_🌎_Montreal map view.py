# basic map viz + emmas distance calc plotting goes in here

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

st.subheader("Map view of Montreal")
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


import plotly.graph_objects as go
import geopandas as gpd
from IPython.display import display

pois = gpd.read_file("../dataframes/clean_pois_montreal.geojson")
pois['geometry'] = pois['geometry'].centroid
polygons = gpd.read_file("../dataframes/district_polygons.geojson")
polygons['centroids'] = polygons['geometry'].centroid
centroids = gpd.GeoDataFrame(polygons, geometry='centroids')
centroids = centroids.drop(columns='geometry').rename(columns={'centroids': 'geometry'})
centroids = gpd.GeoDataFrame(centroids, geometry='geometry')
amenities_with_neighborhood = gpd.sjoin(pois, polygons, how="left", op="within")
amenities_with_neighborhood['distance_to_centroid'] = amenities_with_neighborhood.geometry.distance(polygons.geometry)
# amenities_with_neighborhood.centroid
# amenities_with_neighborhood.geometry
polygons_centroids = amenities_with_neighborhood[['Arrondissement','centroids']].copy()

amenities_with_neighborhood.drop(columns=['centroids'], inplace=True)

amenities_with_neighborhood['distance_to_centroid'] = amenities_with_neighborhood.geometry.distance(polygons_centroids.centroids)

amenities_with_neighborhood['distance_in_m'] = amenities_with_neighborhood['distance_to_centroid']*111195

# create function to loop through each category type and each neighbourhood and calculate average distance_in_m
def calculate_average_distance(df):
    average_distances = []
    for category in df['category'].unique():
        for neighbourhood in df['Arrondissement'].unique():
            average_distance = df[(df['category'] == category) & (df['Arrondissement'] == neighbourhood)]['distance_in_m'].mean()
            average_distances.append([category, neighbourhood, average_distance])
# Create a DataFrame from the list
    result_df = pd.DataFrame(average_distances, columns=['Category', 'Neighbourhood', 'Average Distance'])
    return result_df

ave_distance_df = calculate_average_distance(amenities_with_neighborhood)

cloropleth_df = pd.merge(ave_distance_df, polygons, left_on='Neighbourhood', right_on='Arrondissement', how='left')

# Drop the redundant 'Arrondissement' column
cloropleth_df.drop('Arrondissement', axis=1, inplace=True)

# set nan values in the 'Average Distance' column to 0
cloropleth_df['Average Distance'] = cloropleth_df['Average Distance'].fillna(0)

# drop the rest of the nan values
cloropleth_df = cloropleth_df.dropna()


# Convert the DataFrame to a GeoDataFrame
cloropleth_gdf = gpd.GeoDataFrame(cloropleth_df, geometry='geometry')

# Get unique category types
categories = cloropleth_gdf['Category'].unique()

# Define initial category for the plot
initial_category = categories[0]

# Filter DataFrame for initial category
initial_category_df = cloropleth_gdf[cloropleth_gdf['Category'] == initial_category]

# Create choropleth map figure
fig = go.Figure()

# Add initial choropleth map trace
fig.add_trace(go.Choroplethmapbox(
    geojson=initial_category_df.geometry.__geo_interface__,
    locations=initial_category_df.index,
    z=initial_category_df['Average Distance'],
    colorscale='Viridis',
    colorbar=dict(title='Average Distance (m)'),
    marker_opacity=0.7,
    marker_line_width=0,
    text=initial_category_df['Neighbourhood'],
    hoverinfo='text+z',
    zmin=0,
    zmax=5500  # Set the maximum value for the legend
))

# Update layout
fig.update_layout(
    title=f'Average Distance to Amenity in Montreal',
    mapbox=dict(
        style="carto-positron",
        zoom=9.4,
        center=dict(lat=45.55, lon=-73.6),
    ),
    margin=dict(l=0, r=0, t=0, b=0),
)

# Define dropdown menu
dropdown_menu = []
for category in categories:
    category_df = cloropleth_gdf[cloropleth_gdf['Category'] == category]
    dropdown_menu.append(
        dict(
            args=[{'z': [category_df['Average Distance']],
                'text': [category_df['Neighbourhood']],
                'hoverinfo': 'text+z',
                'title': f'Average Distance to Centroid for {category} in Montreal'}],
            label=category,
            method='restyle'
        )
    )

# Add dropdown menu to the figure
fig.update_layout(updatemenus=[dict(
    buttons=dropdown_menu,
    direction="down",
    pad={"r": 10, "t": 10},
    showactive=True,
    x=0.95,  # Adjust the position to the right
    xanchor="right",  # Align to the right
    y=1.15,
    yanchor="top"
)])

# Display the plot
st.plotly_chart(fig, use_container_width=True)





# import json
# with open("montreal_geojson.txt", "r") as file:
#     montreal_geojson = json.load(file)
# # GET TO KNOW HOW TO DISPLAY THIS IN STREAMLIT!!! ######################################
# fig = px.choropleth(montreal_data,
#                     geojson=montreal_geojson,
#                     locations='District',  # This should match the IDs in your GeoJSON
#                     color='Supermarkets',  # The DataFrame column you want to color by
#                     featureidkey="properties.District",  # Path to the feature ID in the GeoJSON
#                     projection="mercator",
#                     title="Supermarkets in Montreal's Districts")

# # Update the map's layout
# fig.update_geos(fitbounds="locations", visible=False)
# fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

# st.pyplot(fig)