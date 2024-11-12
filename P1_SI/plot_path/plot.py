"""
Plot the graph using the corresponding library.
"""


###############################################################################
# Imports
###############################################################################

# Standard
from pathlib import Path
import glob
import json
import sys
import warnings

# Third party
import contextily as ctx
import matplotlib.pyplot as plt
import matplotlib
import osmnx as ox

# Filter future warnings
action = "ignore"
warnings.simplefilter(action)


###############################################################################
# Functions
###############################################################################

def plot(path, route = None, show = True):
    """
    Plots the graph within the file and optionally shows node names, edge names, and a route path.
    """
    with open(path) as file:
        # Extract address, distance, and initial and final identifiers information for graph plotting
        graph = json.load(file)
        address = graph["address"]
        dist = graph["distance"]
        initial = graph["initial"]
        final = graph["final"]

    # Load graph using address and distance
    network_type = "drive"
    graph = ox.graph_from_address(address, dist, network_type = network_type)

    # Get the nodes
    nodes = True
    edges = False
    nodes = ox.graph_to_gdfs(graph, nodes, edges)

    # Plot the graph
    node_color = "red"
    node_size = s = 20
    edge_linewidth = 0
    show = False
    close = False
    figure, axis = ox.plot_graph(graph, node_color = node_color, node_size = node_size, edge_linewidth = edge_linewidth, show = show, close = close)

    # Add the basemap to the plot
    crs = graph.graph["crs"]
    source = ctx.providers.OpenStreetMap.Mapnik
    ctx.add_basemap(axis, crs = crs, source = source)

    # Define the offset for the node text
    offset = 0.000025

    for identifier, data in graph.nodes(data = True):
        # Extract the node's geometry
        x = data["x"] 
        y = data["y"] 

        # Add the node identifier as text to the plot at the specified position
        s = identifier
        color = "black"
        fontsize = 7
        font = {"color": color, "fontsize": fontsize}
        axis.text(x + offset, y + offset, s, **font)

        if identifier in {initial, final}:
            # Replace the initial and final node colors
            c = "green" if identifier == initial else "blue"
            axis.scatter(x, y, c = c)

    if route:
        # Plot the route on the graph
        route_color = "yellow"
        show = False
        close = False
        ox.plot_graph_route(graph, route, route_color, ax = axis, show = show, close = close)

    if show:
        # Show the plot
        matplotlib.use("TkAgg")
    else:
        # Save the plot
        matplotlib.use("Agg")
        return figure


def store(path):
    """
    Stores the plot to the specified path.
    """
    # Define the output path
    path = Path(path)
    output = Path("figures") / path.parent.stem / (path.stem + ".png")
    parents = True
    exist_ok = True
    output.parent.mkdir(parents = parents, exist_ok = exist_ok)

    # Plot the graph
    show = False
    figure = plot(path, show = show)

    # Save the figure
    bbox_inches = "tight"
    pad_inches = 0
    figure.savefig(output, bbox_inches = bbox_inches, pad_inches = pad_inches)
    plt.close(figure)

    print("Graph plotted to:", output)


###############################################################################
# Main
###############################################################################

if __name__ == "__main__":
    # Extract the path to the graph
    path = sys.argv[1]
    path = Path(path)

    # Store the plot of the graph
    store(path)
