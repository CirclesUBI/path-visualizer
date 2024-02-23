import streamlit as st
import os
from pathfinder import Pathfinder
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Pathfinder
pathfinder = Pathfinder()

# Set page to wide layout
st.set_page_config(layout="wide")

# Set the title of the app
st.title('Circles Pathfinder Viewer')

# Navigation in the sidebar
with st.sidebar:
    st.header("Navigation")
    # Simple navigation link - for now, it's just a static display since there's only one page
    st.markdown("Path Viewer")


# Use Streamlit's sidebar for input fields
with st.sidebar:
    st.header("Input Parameters")
    # Circles address or username inputs
    user_source = st.text_input("From (Username or Address)", value=os.getenv('SOURCE_ADDRESS', ''))
    user_sink = st.text_input("To (Username or Address)", value=os.getenv('SINK_ADDRESS', ''))
    amount = st.text_input("Amount", value=os.getenv('AMOUNT'))
    # Button to trigger Sankey diagram generation
    generate_button = st.button('Generate Sankey Data')

# Function to resolve input to address
def resolve_input_to_address(user_input):
    if user_input.startswith('0x'):
        return user_input  # Assume it's an address
    elif user_input.strip() != "":  # Check if input is not just whitespace
        return pathfinder.resolve_username_to_address(user_input)  # Assume it's a username
    else:
        return None

# Main page layout for displaying the chart
if generate_button:
    # Resolve source and sink inputs to addresses
    source_address = resolve_input_to_address(user_source)
    if not source_address:
        st.error(f"Could not resolve source: {user_source}")
        st.stop()

    sink_address = resolve_input_to_address(user_sink)
    if not sink_address:
        st.error(f"Could not resolve sink: {user_sink}")
        st.stop()

    # Validate and convert amount to integer
    try:
        amount_int = int(amount)
    except ValueError:
        st.error("Please enter a valid amount.")
        st.stop()

    # Use the get_args_for_path method to start with
    token_owner, srcs, dests, wads, capacity = pathfinder.get_args_for_path(source_address, sink_address, amount_int)
    if not token_owner:
        st.error("Failed to generate path. Please check the inputs.")
        st.stop()

    # Use the get_shanky method to generate the data needed for the Sankey diagram
    source_, target_, value_, flow_labels, labels = pathfinder.get_shanky(token_owner, srcs, dests, wads)
    
    # Generate and display a visual Sankey diagram
    fig = pathfinder.draw_shanky(source_, target_, value_, flow_labels, labels)
    st.plotly_chart(fig, use_container_width=True)  # Display the figure in the Streamlit app, using the full width of the container