import streamlit as st
from streamlit_option_menu import option_menu
import os
import subprocess
import json
from dotenv import load_dotenv
from pathfinder import Pathfinder
# from streamlit_d3graph import d3graph

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
    selected = option_menu("Main Menu", ["Path Viewer", "Explore My Trust Graph"],
                           icons=["graph-up", "compass"], menu_icon="cast", default_index=0)

    if selected == "Path Viewer":
        st.header("Path Viewer Inputs")
        user_source = st.text_input("From (Username or address)", value="shorn", key="pv_user_source")
        user_sink = st.text_input("To (Username or address)", value="Martin", key="pv_user_sink")
        amount ="999999999999999999999999999"
        generate_chart_button = st.button('Generate Chart', key='generate_chart')

# Path Viewer section logic
if selected == "Path Viewer" and generate_chart_button:
    with st.spinner('Generating chart... Please wait'):
        source_address = resolve_input_to_address(user_source)
        sink_address = resolve_input_to_address(user_sink)

        if source_address and sink_address:
            token_owner, srcs, dests, wads, capacity = pathfinder.get_args_for_path(source_address, sink_address, amount)
            if token_owner:
                fig = pathfinder.draw_shanky(*pathfinder.get_shanky(token_owner, srcs, dests, wads))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Failed to generate path. Please check the inputs.")
        else:
            st.error("Invalid source or sink address.")