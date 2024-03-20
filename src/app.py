import streamlit as st
from streamlit_option_menu import option_menu
import os
import subprocess
import json
from dotenv import load_dotenv
from pathfinder import Pathfinder
from streamlit_d3graph import d3graph

# Load environment variables and initialize Pathfinder
load_dotenv()
pathfinder = Pathfinder()

# Set page config
st.set_page_config(layout="wide")
st.title('Circles Pathfinder Viewer')

def resolve_input_to_address(user_input):
    if user_input.startswith('0x'):
        return user_input
    elif user_input.strip() != "":
        return pathfinder.resolve_username_to_address(user_input)
    else:
        return None

# Sidebar navigation and form inputs
with st.sidebar:
    selected = option_menu("Main Menu", ["Path Viewer", "Explore Trust Graph"],
                           icons=["graph-up", "diagram-3"], menu_icon="cast", default_index=0)

    # Path Viewer inputs
    if selected == "Path Viewer":
        st.header("Path Viewer Inputs")
        user_source = st.text_input("From (Username or address)", value="Martin", key="pv_user_source")
        user_sink = st.text_input("To (Username or address)", value="shorn", key="pv_user_sink")
        amount = "999999999999999999999999999"
        generate_chart_button = st.button('Generate Chart', key='generate_chart')

    # Network Graph input
    if selected == "Explore Trust Graph":
        
        st.header("Explore the Trust Graph")
        user_source = st.text_input("From (Username or address)", value="shorn", key="ng_user_source")
        visualize_network_button = st.button('Generate Graph', key='visualize_network')

# Path Viewer logic
if selected == "Path Viewer" and generate_chart_button:
    with st.spinner('Generating chart... Please wait'):
        source_address = resolve_input_to_address(user_source)
        sink_address = resolve_input_to_address(user_sink)

        if source_address and sink_address:
            token_owner, srcs, dests, wads, capacity = pathfinder.get_args_for_path(source_address, sink_address, amount)
            if token_owner:
                fig = pathfinder.draw_sankey(*pathfinder.get_sankey(token_owner, srcs, dests, wads))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Failed to generate path. Please check the inputs.")
        else:
            st.error("Could not resolve address: " + user_address)
    
# Network Graph logic
if selected == "Explore Trust Graph" and visualize_network_button:
    resolved_address = resolve_input_to_address(user_source)
    if resolved_address:
        trust_connections = pathfinder.fetch_trust_connections(resolved_address)
        if trust_connections:
            trust_data = pathfinder.process_data_for_visualization(trust_connections, resolved_address)
            container = st.empty()
            d3 = d3graph()
            d3.graph(trust_data)
            container.html(d3.html)
        else:
            st.error("Failed to fetch trust connections or no connections found.")
    else:
        st.error("Could not resolve address: " + user_source)
