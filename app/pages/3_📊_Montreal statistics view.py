import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from tools.ui_utils import (
    add_logo,
    ui_setup
)

# testing 

add_logo()
ui_setup()
st.subheader("Map view of Montreal")
st.write("Make your data input in the sidebar and wait for the analysis to run.")

montreal_map = pd.DataFrame({
    'lat': [45.5017],
    'lon': [-73.5673]
})

# Hypothetical data for Montreal's districts
data = {
    'District': ['Ville-Marie', 'Plateau Mont-Royal', 'Rosemont-La Petite-Patrie', 'Côte-des-Neiges'],
    'Inhabitants': [84234, 100231, 139834, 165345],  # Hypothetical numbers
    'Supermarkets': [10, 15, 12, 9],  # Hypothetical numbers
    'Pharmacies': [8, 9, 11, 10],  # Hypothetical numbers
    'General practitioners': [20, 18, 22, 25],  # Hypothetical numbers
    'School/university': [5, 3, 4, 6],  # Hypothetical numbers
    'Cafés': [25, 40, 30, 20],  # Hypothetical numbers
    'Parks/green areas': [15, 20, 18, 22],  # Hypothetical numbers
    'Public water access': [2, 1, 0, 3],  # Hypothetical numbers
    'Libraries': [3, 4, 5, 3],  # Hypothetical numbers
    'Places of worship': [10, 12, 8, 15],  # Hypothetical numbers
    'Bars': [30, 45, 25, 20],  # Hypothetical numbers
    'Restaurants': [50, 60, 40, 30]  # Hypothetical numbers
}
df = pd.DataFrame(data)

# create the interactive plotly figure
df_melted = df.melt(id_vars='District', var_name='Amenity', value_name='Count')
amenities = df_melted['Amenity'].unique()
dropdown_options = [{'label': amenity, 'value': amenity} for amenity in amenities]

fig = go.Figure()
for amenity in amenities:
    fig.add_trace(
        go.Bar(
            x=df_melted[df_melted['Amenity'] == amenity]['District'],
            y=df_melted[df_melted['Amenity'] == amenity]['Count'],
            name=amenity,
            visible=(amenity == amenities[0])
        )
    )
# Update layout to include the dropdown menu
fig.update_layout(
    updatemenus=[
        go.layout.Updatemenu(
            buttons=list([
                dict(
                    args=[{"visible": [amenity == option['value'] for amenity in amenities]}],
                    label=option['label'],
                    method="update"
                ) for option in dropdown_options
            ]),
            direction="down",
            pad={"r": 10, "t": 10},
            showactive=True,
            x=0,
            xanchor="left",
            y=1.1,
            yanchor="top"
        ),
    ]
)

st.subheader("Amenity plotted by district")
st.plotly_chart(fig, use_container_width=True)

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