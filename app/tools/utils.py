import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import osmnx as ox
import geopandas as gpd
import streamlit as st 
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image


# support function
def get_amenity_data():
    pois = gpd.read_file("dataframes/clean_pois_montreal.geojson")
    pois['geometry'] = pois['geometry'].centroid
    
    polygons = gpd.read_file("dataframes/district_polygons.geojson")
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


# used in welcome page
def neighbourhood_map():
    df2 = gpd.read_file('dataframes/quartiers_sociologiques_2014.geojson') # quartier data
    
    df2 = df2.to_crs(crs=4326)
    district_centroids_2 = df2.copy()
    district_centroids_2['centroid'] = district_centroids_2['geometry'].centroid
    df2 = df2.to_crs(crs=4326)
    district_centroids_2 = district_centroids_2.groupby('Abreviation').agg(
        arrondissement=('Arrondissement', 'first'),
        id=('id', 'first'),
        centroid=('centroid', 'first')
    ).reset_index()
    
    fig = px.choropleth_mapbox(df2, geojson=df2.geometry.__geo_interface__, locations=df2.index, color="Arrondissement",
                            center={"lat": 45.55, "lon": -73.65},
                            mapbox_style="carto-positron", 
                            zoom=9.4)

    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig, use_container_width=True)


# used in statistics view
def amenity_dataframe():
    st.divider()
    
    amenities_with_neighborhood, polygons = get_amenity_data()
    amenities_with_neighborhood.drop(columns=["element_type", "osmid", "direction", "geometry", "index_right", "distance_to_centroid"], inplace=True)
    df = pd.DataFrame(amenities_with_neighborhood)
    df.rename(columns={"Arrondissement": "neighbourhood", "distance_in_m": "distance_in_m_from_center"}, inplace=True)
    
    amenities_with_neighborhood = gpd.read_file('dataframes/amenities_with_neighborhood.geojson')

    neighbourhoods = list(amenities_with_neighborhood['Arrondissement'].unique())[:-1]
    neighbourhoods = sorted([item.split(',')[0] for item in neighbourhoods])

    amenities = sorted(amenities_with_neighborhood.amenity.unique())
    
    categories = sorted(amenities_with_neighborhood.category.dropna().unique())
    
    st.write("Here you have to possibility to browse through all amenity and neighbourhood data below.")

    # columns for the filter type, specific filter, and reset button
    col1, col2 = st.columns([1, 3])

    with col1:
        filter_type = st.radio("Filter by:", ("Amenity", "Category"), key="filter_type")
        
        if filter_type == "Amenity":
            amenity_selectbox = st.selectbox("Select Amenity:", [''] + amenities, key="amenity_selectbox")
            filtered_df = df[df['amenity'] == amenity_selectbox] if amenity_selectbox else df
        else:
            category_selectbox = st.selectbox("Select Category:", [''] + categories, key="category_selectbox")
            filtered_df = df[df['category'] == category_selectbox] if category_selectbox else df
        
        neighbourhood_selectbox = st.selectbox("Select Neighbourhood:", [''] + neighbourhoods, key="neighbourhood_selectbox")
        if neighbourhood_selectbox:
            filtered_df = filtered_df[filtered_df['neighbourhood'] == neighbourhood_selectbox]

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
    
    amenities_with_neighborhood = gpd.read_file('dataframes/amenities_with_neighborhood.geojson')

    neighbourhoods = list(amenities_with_neighborhood['Arrondissement'].unique())[:-1]
    neighbourhoods = sorted([item.split(',')[0] for item in neighbourhoods])
    
    amenities = sorted(amenities_with_neighborhood.amenity.unique())
    
    categories = sorted(amenities_with_neighborhood.category.dropna().unique())
    
    col1, col2 = st.columns(2)

    with col1:
        filter_type = st.radio("Filter by:", ("Amenity", "Category"))

    with col2:
        if filter_type == "Amenity":
            selected_filter = st.selectbox("Select Amenity:", [''] + amenities)
            filtered_df = df[df['amenity'] == selected_filter] if selected_filter else df
        else:
            selected_filter = st.selectbox("Select Category:", [''] + categories)
            filtered_df = df[df['category'] == selected_filter] if selected_filter else df

    # occurrences based on the selected filter and neighborhood
    count_df = filtered_df.groupby(['neighbourhood', filter_type.lower()]).size().reset_index(name='count')    
    
    # plotting
    fig = px.bar(count_df, x='neighbourhood', y='count', color=filter_type.lower(),
                color_discrete_sequence=px.colors.qualitative.Set3,
                category_orders={'neighbourhood': df['neighbourhood'].unique()})

    # chart layout
    fig.update_layout(
        title=f"Count of {filter_type}s by Neighborhood",
        xaxis_title="Neighborhood",
        yaxis_title="Count",
        showlegend=True,
        legend_title=filter_type,
        xaxis={'categoryorder': 'array', 'categoryarray': df['neighbourhood'].unique()}
    )

    st.plotly_chart(fig, use_container_width=True)


# used in map view analysis
def amenity_neighbourhood_map():
    amenities_with_neighborhood, polygons = get_amenity_data()
    amenities_count = amenities_with_neighborhood.groupby('Arrondissement').size().reset_index(name='amenities_count')
    cloropleth_df = pd.merge(amenities_count, polygons, left_on='Arrondissement', right_on='Arrondissement', how='left')
    
    # convert the df to geodataframe
    cloropleth_gdf = gpd.GeoDataFrame(cloropleth_df, geometry='geometry')

    # create a choropleth map of the count of amenities in each neighbourhood
    fig = go.Figure()

    # Add choropleth map trace
    fig.add_trace(go.Choroplethmapbox(
        geojson=cloropleth_gdf.geometry.__geo_interface__,
        locations=cloropleth_gdf.index,
        z=cloropleth_gdf['amenities_count'],
        colorscale='Viridis',
        colorbar=dict(title='Number of Amenities'),
        marker_opacity=0.7,
        marker_line_width=0,
        text=cloropleth_gdf['Arrondissement'],
        hoverinfo='text+z',
        reversescale=True # comment out for reversed color scale
    ))

    # Update layout
    fig.update_layout(
        title='Number of Amenities in Montreal by Neighbourhood',
        mapbox=dict(
            style="carto-positron",
            zoom=9.4,
            center=dict(lat=45.55, lon=-73.6),
        ),
        margin=dict(l=0, r=0, t=50, b=0),
    )

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

        result_df = pd.DataFrame(average_distances, columns=['Category', 'Neighbourhood', 'Average Distance'])
        return result_df

    ave_distance_df = calculate_average_distance(amenities_with_neighborhood)

    cloropleth_df = pd.merge(ave_distance_df, polygons, left_on='Neighbourhood', right_on='Arrondissement', how='left')

    # redundant 'Arrondissement' column
    cloropleth_df.drop('Arrondissement', axis=1, inplace=True)

    # set nan values in the 'Average Distance' column to 0
    cloropleth_df['Average Distance'] = cloropleth_df['Average Distance'].fillna(0)
    cloropleth_df = cloropleth_df.dropna()

    # convert to geodataframe
    cloropleth_gdf = gpd.GeoDataFrame(cloropleth_df, geometry='geometry')

    categories = cloropleth_gdf['Category'].unique()

    initial_category = categories[0]
    initial_category_df = cloropleth_gdf[cloropleth_gdf['Category'] == initial_category]

    # Create a custom colorscale
    custom_colorscale = [
        [0.0, "yellow"],  # Color for zero
        [0.000001, "#440154"],  # Viridis scale starts
        [0.1, "#482878"],
        [0.2, "#3e4989"],
        [0.3, "#31688e"],
        [0.4, "#26838f"],
        [0.5, "#1f9d8a"],
        [0.6, "#6cce5a"],
        [0.7, "#b6de2b"],
        [0.8, "#fee825"],
        [1.0, "#fdea45"]
    ]

    # Create choropleth map figure
    fig = go.Figure()

    # Add initial choropleth map trace
    fig.add_trace(go.Choroplethmapbox(
        geojson=initial_category_df.geometry.__geo_interface__,
        locations=initial_category_df.index,
        z=initial_category_df['Average Distance'],
        colorscale=custom_colorscale,
        colorbar=dict(title='Average Distance (m)'),
        marker_opacity=0.7,
        marker_line_width=0,
        text=initial_category_df['Neighbourhood'],
        hoverinfo='text+z',
        zmin=0,
        zmax=5500  # Set the maximum value for the legend as there are 6 outliers about the distance
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
    # # plotting
    # fig = go.Figure()

    # # initial choropleth map trace
    # fig.add_trace(go.Choroplethmapbox(
    #     geojson=initial_category_df.geometry.__geo_interface__,
    #     locations=initial_category_df.index,
    #     z=initial_category_df['Average Distance'],
    #     colorscale='Viridis',
    #     colorbar=dict(title='Average Distance (m)'),
    #     marker_opacity=0.7,
    #     marker_line_width=0,
    #     text=initial_category_df['Neighbourhood'],
    #     hoverinfo='text+z',
    #     zmin=0,
    #     zmax=5500 # legend values
    # ))

    # fig.update_layout(
    #     title=f'Average Distance to Amenity in Montreal',
    #     mapbox=dict(
    #         style="carto-positron",
    #         zoom=9.4,
    #         center=dict(lat=45.55, lon=-73.6),
    #     ),
    #     margin=dict(l=0, r=0, t=0, b=0),
    # )

    # # dropdown menu
    # dropdown_menu = []
    # for category in categories:
    #     category_df = cloropleth_gdf[cloropleth_gdf['Category'] == category]
    #     dropdown_menu.append(
    #         dict(
    #             args=[{'z': [category_df['Average Distance']],
    #                 'text': [category_df['Neighbourhood']],
    #                 'hoverinfo': 'text+z',
    #                 'title': f'Average Distance to Centroid for {category} in Montreal'}],
    #             label=category,
    #             method='restyle'
    #         )
    #     )

    # # dropdown menu to the figure
    # fig.update_layout(updatemenus=[dict(
    #     buttons=dropdown_menu,
    #     direction="down",
    #     pad={"r": 10, "t": 10},
    #     showactive=True,
    #     x=0.95,  # Adjust the position to the right
    #     xanchor="right",  # Align to the right
    #     y=1.15,
    #     yanchor="top"
    # )])

    st.plotly_chart(fig, use_container_width=True)


# used in neighbourhood analysis
def plot_neighborhood_graph(transportation_type, neighbourhood, distances_by_transportation, graphs_dict, amenity):
    
    # appropriate graph based on the transportation type
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
    
    # plot graph
    fig, ax = ox.plot_graph(G_proj, figsize=(10, 8), bgcolor='white', edge_color='#CCCCCC', edge_linewidth=0.5, node_size=0, show=False, close=False)
    
    nodes_proj = ox.graph_to_gdfs(G_proj, edges=False)
    
    # scatter
    sc = ax.scatter(x=nodes_proj['x'], y=nodes_proj['y'], c=distances['travel_time'], s=30, cmap='inferno_r', alpha=0.8, vmin=0, vmax=15)
    
    # create colourbar
    cbar = plt.colorbar(sc, ax=ax, shrink=0.7)
    cbar.set_ticks(range(0, 16))
    cbar.set_ticklabels(range(0, 16))
    
    st.pyplot(fig)


# used in conclusions
def neighbourhood_characteristics():
    st.write("**Neighbourhoods and their characteristics**")
    
    details_toggle = st.toggle("Show neighbourhood details", False)
    
    if details_toggle:
        st.write("**Ahuntsic-Cartierville**: Known for its family-friendly environment, this neighborhood boasts riverside parks, bike paths, and sports facilities. It offers a mix of action and tranquility, with a significant presence of green spaces and a variety of birds and aquatic wildlife")
        st.write("**Anjou**: Strategically located at the crossroads of major highways, Anjou features quiet streets, an abundance of single-family homes, and shopping centers like Place Versailles and Les Galeries d’Anjou, providing convenience and a suburban feel")
        st.write("**Côte-des-Neiges–Notre-Dame-de-Grâce**: This neighborhood offers a multicultural experience with a diverse range of homes, including historical houses. It is known for its vibrant community, educational institutions, and healthcare facilities, making it ideal for students and individuals seeking quality education and healthcare")
        st.write("**L'Île-Bizard–Sainte-Geneviève / Pierrefonds-Roxboro**: Characterized by tranquility and a wide range of outdoor activities, this area is suitable for families looking for a peaceful environment. It has space for new residential buildings and offers a suburban lifestyle close to nature")
        st.write("**LaSalle**: Located between the St. Lawrence River and the Lachine Canal, LaSalle provides a variety of homes, including condominiums and retirement homes. It is known for its waterfront living and recreational opportunities")
        st.write("**Lachine**: With a rich arts and recreational scene, Lachine offers a quality of life with rental homes and new buildings, appealing to young families. It is known for its historical significance and industrial heritage")
        st.write("**Le Plateau-Mont-Royal**: This neighborhood is known for its intense neighborhood life, urban charm, and proximity to busy streets. It features multiplexes with colorful staircases and a network of green lanes, attracting a diverse population including students and artists")
        st.write("**Le Sud-Ouest**: Appreciated for its urban yet friendly lifestyle, Le Sud-Ouest is known for its converted industrial buildings and recent developments along the Lachine Canal. It offers a blend of historic charm and modern amenities")
        st.write("**Mercier–Hochelaga-Maisonneuve**: This neighborhood is experiencing renewal with a rich industrial history. It offers a wide range of homes, commercial streets, and amenities like a public market, appealing to a diverse community")
        st.write("**Montréal-Nord**: Undergoing transformation, Montréal-Nord offers affordable housing options and is located on the shores of the Rivière des Prairies. It is known for its cultural diversity and community engagement")
        st.write("**Outremont**: Known for its beautiful historical homes and urban forest, Outremont offers a vast choice of housing and a delightful neighborhood life, appealing to those seeking upscale living")
        st.write("**Rivière-des-Prairies–Pointe-aux-Trembles**: With stunning settings on the shores of rivers, this neighborhood offers regional parks and affordable housing, attracting couples, families, and businesspeople looking for a suburban lifestyle")
        st.write("**Rosemont–La Petite-Patrie**: Features a number of distinct neighborhoods with lively atmospheres. It offers a vast choice of homes and is known for its family-friendly environment and community events")
        st.write("**Saint-Laurent**: Home to one of Canada’s largest industrial centers, Saint-Laurent offers diverse housing options and is close to public transportation. It is recognized for its multicultural community and economic development")
        st.write("**Saint-Léonard**: Known for its multiplexes and apartment towers, Saint-Léonard has a lively neighborhood life with a strong sense of community and cultural diversity")
        st.write("**Verdun**: An ideal place for young families, Verdun offers green spaces, family homes, rentals, co-owned homes, and a stunning beach, providing a waterfront lifestyle")
        st.write("**Ville-Marie**: Offers peaceful residential neighborhoods next to downtown's hustle and bustle. It is a hub of arts, culture, and economic activity, appealing to those seeking a vibrant urban environment")
        st.write("**Villeray–Saint-Michel–Parc-Extension**: Known for its unique vibe, parks, and rental homes, this neighborhood is accessible and filled with commercial streets at the heart of real neighborhoods, attracting a diverse population")


# used in conclusions
def neighbourhoods_by_group():
    
    col1, col2, col3 = st.columns([5, 1, 9])
    
    with col1:
        group_radio = st.radio("Select the group you are interested to explore.", ["Families with children", "Young adults", "Young professionals", "Elderly"])
        
        if group_radio == "Young adults":
            image = Image.open("visuals/young_adults.png")
            st.image(image, width=250)
        
        if group_radio == "Families with children":
            image = Image.open("visuals/families.png")
            st.image(image, width=250)
        
        if group_radio == "Young professionals":
            image = Image.open("visuals/young-professionals.png")
            st.image(image, width=250)
        
        if group_radio == "Elderly":
            image = Image.open("visuals/elderly.png")
            st.image(image, width=250)
        
    with col3:
        if group_radio == "Young adults":
            st.write("**Potential interests**: Career advancement, education, socializing, dating, exploring personal identity, adventure.")
            st.write("**Potential needs**: Higher education or vocational training, job opportunities, financial independence, relationship building, autonomy, self-discovery.")

            st.write("*Winning neighbourhoods with accessible further education, nightlife, and entertainment by bike or by foot:*")
            st.markdown("1. Ville-Marie")
            st.markdown("2. Le Plateau-Mont-Royal")
            st.markdown("3. Côte-des-Neiges–Notre-Dame-de-Grâce")

            st.markdown('''
            <style>
            [data-testid="stMarkdownContainer"] ul{
                list-style-position: inside;
            }
            </style>
            ''', unsafe_allow_html=True)
            
        if group_radio == "Families with children":
            st.write("**Potential interests**: Family activities, child development, community involvement, recreation, play, exploration.")
            st.write("**Potential needs**: Childcare, quality education, family-friendly environment, recreational facilities, safety, social support, work-life balance, parental guidance.")
            
            st.write("*Winning neighbourhoods with accessible child support, schools, and public services by car or electric cargo bike*:")
            st.markdown("1. Rosemont–La Petite-Patrie")
            st.markdown("2. Côte-des-Neiges–Notre-Dame-de-Grâce")
            st.markdown("3. Villeray–Saint-Michel–Parc-Extension")

            st.markdown('''
            <style>
            [data-testid="stMarkdownContainer"] ul{
                list-style-position: inside;
            }
            </style>
            ''', unsafe_allow_html=True)
            
        if group_radio == "Young professionals":
            st.write("**Potential interests**: Job opportunities, family, personal growth, hobbies, community involvement, maintaining health and well-being.")
            st.write("**Potential needs**: Career progression or stability, family support, financial security, health care, stress management, maintaining social connections.")

            st.write("*Winning neighbourhoods with entertainment, restaurants, and culture accessible with all transport options*:")
            st.markdown("1. Saint-Laurent")
            st.markdown("2. Saint-Léonard")
            st.markdown("3. Ville-Marie")

            st.markdown('''
            <style>
            [data-testid="stMarkdownContainer"] ul{
                list-style-position: inside;
            }
            </style>
            ''', unsafe_allow_html=True)
            
        if group_radio == "Elderly":
            st.write("**Potential interests**: Retirement activities, leisure pursuits, spending time with family and friends, lifelong learning, travel, culture.")
            st.write("**Potential needs**: Health care, financial stability, social support, access to age-appropriate services, opportunities for continued personal growth and engagement.")
            
            st.write("*Winning neighbourhoods with public services, healthcare, and restaurants/cafés accessible in no time with a car*:")
            st.markdown("1. Côte-des-Neiges–Notre-Dame-de-Grâce")
            st.markdown("2. Ahuntsic-Cartierville")
            st.markdown("3. Rosemont–La Petite-Patrie")

            st.markdown('''
            <style>
            [data-testid="stMarkdownContainer"] ul{
                list-style-position: inside;
            }
            </style>
            ''', unsafe_allow_html=True)