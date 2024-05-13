import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import osmnx as ox
import geopandas as gpd
import streamlit as st 
import plotly.graph_objects as go
import plotly.express as px


# support function
def get_amenity_data():
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
    return amenities_with_neighborhood, polygons


# used in statistics view
def amenity_dataframe():
    st.divider()
    
    amenities_with_neighborhood, polygons = get_amenity_data()
    amenities_with_neighborhood.drop(columns=["element_type", "osmid", "direction", "geometry", "index_right", "distance_to_centroid"], inplace=True)
    df = pd.DataFrame(amenities_with_neighborhood)
    df.rename(columns={"Arrondissement": "neighbourhood", "distance_in_m": "distance_in_m_from_center"}, inplace=True)
    
    amenities = df['amenity'].unique().tolist()
    categories = df['category'].unique().tolist()
    neighbourhoods = df['neighbourhood'].unique().tolist()
    
    # use streamlit columns to include all selectboxes in one row
    st.write("Here you have to possibility to browse through all amenity and neighbourhood data below.")
    st.write("**Filter by category, amenity, and neighbourhood, if you like.**")


    # Create columns for the filter type, specific filter, and reset button
    col1, col2 = st.columns([1, 3])

    # Create a radio button for selecting the filter type
    with col1:
        filter_type = st.radio("Filter by:", ("Amenity", "Category"), key="filter_type")
        
        if filter_type == "Amenity":
            amenity_selectbox = st.selectbox("Select Amenity:", [''] + df['amenity'].unique().tolist(), key="amenity_selectbox")
            filtered_df = df[df['amenity'] == amenity_selectbox] if amenity_selectbox else df
        else:
            category_selectbox = st.selectbox("Select Category:", [''] + df['category'].unique().tolist(), key="category_selectbox")
            filtered_df = df[df['category'] == category_selectbox] if category_selectbox else df
        
        neighbourhood_selectbox = st.selectbox("Select Neighbourhood:", [''] + df['neighbourhood'].unique().tolist(), key="neighbourhood_selectbox")
        if neighbourhood_selectbox:
            filtered_df = filtered_df[filtered_df['neighbourhood'] == neighbourhood_selectbox]

    # Create a selectbox for choosing the specific amenity or category
    with col2:
        st.dataframe(data=filtered_df, hide_index=True, use_container_width=True)

    st.divider()
    
    st.page_link(page = "https://www.google.com/maps/@45.5508466,-73.6543288,10.75z?entry=ttu", label="Open Google Maps for location lookup.", icon="📍")


# used in statistics view
def amenity_plot():

    amenities_with_neighborhood, polygons = get_amenity_data()
    amenities_with_neighborhood.drop(columns=["element_type", "osmid", "direction", "geometry", "index_right", "distance_to_centroid"], inplace=True)
    df = pd.DataFrame(amenities_with_neighborhood)
    df.rename(columns={"Arrondissement": "neighbourhood", "distance_in_m": "distance_in_m_from_center"}, inplace=True)
    
    # Create columns for the filter type and specific filter
    col1, col2 = st.columns(2)

    # Create a radio button for selecting the filter type
    with col1:
        filter_type = st.radio("Filter by:", ("Amenity", "Category"))

    # Create a selectbox for choosing the specific amenity or category
    with col2:
        if filter_type == "Amenity":
            selected_filter = st.selectbox("Select Amenity:", [''] + df['amenity'].unique().tolist())
            filtered_df = df[df['amenity'] == selected_filter] if selected_filter else df
        else:
            selected_filter = st.selectbox("Select Category:", [''] + df['category'].unique().tolist())
            filtered_df = df[df['category'] == selected_filter] if selected_filter else df

    # Count the occurrences based on the selected filter and neighborhood
    count_df = filtered_df.groupby(['neighbourhood', filter_type.lower()]).size().reset_index(name='count')    
    
    # Create the Plotly bar chart
    fig = px.bar(count_df, x='neighbourhood', y='count', color=filter_type.lower(),
                color_discrete_sequence=px.colors.qualitative.Set3,
                category_orders={'neighbourhood': df['neighbourhood'].unique()})

    # Customize the chart layout
    fig.update_layout(
        title=f"Count of {filter_type}s by Neighborhood",
        xaxis_title="Neighborhood",
        yaxis_title="Count",
        showlegend=True,
        legend_title=filter_type,
        xaxis={'categoryorder': 'array', 'categoryarray': df['neighbourhood'].unique()}
    )

    # Display the chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)


# used in map view analysis
def amenity_distances_map():
    amenities_with_neighborhood, polygons = get_amenity_data()

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


# used in neighbourhood analysis
# def plot_neighborhood_graph(transportation_type, neighbourhood, distances_by_transportation, graphs_dict, amenity):
    
#     # Load the appropriate graph based on the transportation type
#     if transportation_type == "walking":
#         G = graphs_dict["walking"][f"{neighbourhood}, Montreal, Canada"]
#     elif transportation_type == "driving":
#         G = graphs_dict["driving"][f"{neighbourhood}, Montreal, Canada"]
#     elif transportation_type == "biking":
#         G = graphs_dict["biking"][f"{neighbourhood}, Montreal, Canada"]
    
#     # CRS
#     G_proj = ox.project_graph(G)
    
#     distances = distances_by_transportation[distances_by_transportation["amenity"] == amenity]
#     distances = distances[distances["neighborhood"] == f"{neighbourhood}, Montreal, Canada"]
#     # distances = distances_by_transportation[amenity][f"{neighbourhood}, Montreal, Canada"]
    
#     # Plot the graph with a light background
#     fig, ax = ox.plot_graph(G_proj, figsize=(10, 8), bgcolor='white', edge_color='#CCCCCC', edge_linewidth=0.5, node_size=0, show=False, close=False)
    
#     # Assuming 'nodes_anjou' is a DataFrame containing node positions and 'distances_anjou' contains the data to plot
#     nodes_proj = ox.graph_to_gdfs(G_proj, edges=False)
    
#     # Scatter plot on the same Axes instance
#     sc = ax.scatter(x=nodes_proj["x"], y=nodes_proj["y"], c=distances['travel_time'], s=30, cmap='inferno_r', alpha=0.8)
    
#     # Add colorbar
#     plt.colorbar(sc, ax=ax, shrink=0.7)
    
#     # Show the plot
#     st.pyplot(fig)
    
def plot_neighborhood_graph(transportation_type, neighbourhood, distances_by_transportation, graphs_dict, amenity):
    
    # Load the appropriate graph based on the transportation type
    if transportation_type == "walking":
        G = graphs_dict["walking"][f"{neighbourhood}, Montreal, Canada"]
    elif transportation_type == "driving":
        G = graphs_dict["driving"][f"{neighbourhood}, Montreal, Canada"]
    elif transportation_type == "biking":
        G = graphs_dict["biking"][f"{neighbourhood}, Montreal, Canada"]
    
    # CRS
    G_proj = ox.project_graph(G)
    
    distances = distances_by_transportation[distances_by_transportation["amenity"] == amenity]
    distances = distances[distances["neighborhood"] == f"{neighbourhood}, Montreal, Canada"]
    
    # Plot the graph with a light background
    fig, ax = ox.plot_graph(G_proj, figsize=(10, 8), bgcolor='white', edge_color='#CCCCCC', edge_linewidth=0.5, node_size=0, show=False, close=False)
    
    nodes_proj = ox.graph_to_gdfs(G_proj, edges=False)
    
    # Merge the nodes_proj and distances DataFrames based on a common key
    # merged_data = nodes_proj.merge(distances, left_on='osmid', right_on='node')
    
    # Scatter plot on the same Axes instance
    sc = ax.scatter(x=nodes_proj["x"], y=nodes_proj["y"], c=distances['travel_time'], s=30, cmap='inferno_r', alpha=0.8)
    
    # Add colorbar
    plt.colorbar(sc, ax=ax, shrink=0.7)
    
    # Show the plot
    st.pyplot(fig)

    
# #OLD VERSION
# def plot_neighborhood_graph(mot, mot_distances, neighbourhood, amenity, graphs_dict):
#     # Load the graph from the specified place and network type
#     # G = mot_graph
#     # Load the appropriate graph based on the transportation type
#     if mot == "walking":
#         G = graphs_dict["walking"][f"{neighbourhood}, Montreal, Canada"]
#     elif mot == "driving":
#         G = graphs_dict["driving"][f"{neighbourhood}, Montreal, Canada"]
#     elif mot == "biking":
#         G = graphs_dict["biking"][f"{neighbourhood}, Montreal, Canada"]
    
#     st.write(G)
    
#     # CRS
#     G_proj = ox.project_graph(G)
    
#     distances = mot_distances[mot_distances["amenity"] == amenity]
#     distances = distances[f"{neighbourhood}, Montreal, Canada"]
    
#     # Plot the graph with a light background
#     fig, ax = ox.plot_graph(G_proj, figsize=(10, 8), bgcolor='white', edge_color='#CCCCCC', edge_linewidth=0.5, node_size=0, show=False, close=False)
    
#     # Assuming 'nodes_anjou' is a DataFrame containing node positions and 'distances_anjou' contains the data to plot
#     nodes_proj = ox.graph_to_gdfs(G_proj, edges=False)
    
#     # Scatter plot on the same Axes instance
#     sc = ax.scatter(x=nodes_proj["x"], y=nodes_proj["y"], c=distances['travel_time'], s=50, cmap='inferno_r', alpha=0.8)
    
#     # Add colorbar
#     plt.colorbar(sc, ax=ax, shrink=0.7)
    
#     # Show the plot
#     st.pyplot(fig)

#     # example usage
#     # plot_neighborhood_graph(G_walk_anjou, 'Anjou')