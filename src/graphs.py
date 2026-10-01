import json
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import random
import typing

type Graph = nx.Graph

def load_graph_from_data(data):
    """Build a NetworkX graph from a Python dictionary."""
    if not isinstance(data, dict):
        raise ValueError("Graph JSON must contain an object.")

    vertices = data.get("vertices", [])
    edges = data.get("edges", [])

    if not isinstance(vertices, list):
        raise ValueError("The 'vertices' field must be a list.")

    if not isinstance(edges, list):
        raise ValueError("The 'edges' field must be a list.")

    graph = nx.Graph()
    graph.add_nodes_from(vertices)

    for edge in edges:
        if not isinstance(edge, (list, tuple)) or len(edge) != 2:
            raise ValueError(f"Each edge must be a pair like [u, v]; got {edge!r}.")

        u, v = edge
        if u not in graph or v not in graph:
            missing = u if u not in graph else v
            raise ValueError(f"Edge {edge!r} references a missing vertex: {missing}.")

        graph.add_edge(u, v)

    return graph


def load_graph(filepath):
    """Load a graph from a JSON file in the project format.

    Expected structure:
    {
        "vertices": [0, 1, 2],
        "edges": [[0, 1], [1, 2], [2, 0]]
    }
    """
    path = Path(filepath)

    with path.open("r", encoding="utf-8") as graph_file:
        data = json.load(graph_file)

    return load_graph_from_data(data)


def make_triangle():
    graph = nx.Graph()
    graph.add_nodes_from([0, 1, 2])
    graph.add_edges_from([
        (0, 1),
        (1, 2),
        (0, 2),
    ])
    return graph


def make_k4():
    return nx.complete_graph(4)


def draw_graph(
    graph,
    title,
    show_labels=None,
    save_path=None,
    positions=None,
):
    """Draw an uncolored graph and optionally save a 300 DPI image."""
    node_count = graph.number_of_nodes()
    show_labels = node_count <= 30 if show_labels is None else show_labels
    node_size = max(45, min(600, 16000 / max(node_count, 1)))
    if positions is None:
        positions = nx.spring_layout(
            graph,
            seed=7,
            k=2 / max(node_count, 1) ** 0.5,
            iterations=150,
        )

    figure, axis = plt.subplots(figsize=(10, 8))
    nx.draw_networkx_edges(
        graph,
        positions,
        ax=axis,
        edge_color="#555555",
        width=0.7,
        alpha=0.25,
    )
    nx.draw_networkx_nodes(
        graph,
        positions,
        ax=axis,
        node_color="#8a8a8a",
        node_size=node_size,
        edgecolors="white",
        linewidths=0.5,
    )
    if show_labels:
        nx.draw_networkx_labels(graph, positions, ax=axis, font_size=8)

    axis.set_title(title, fontsize=16)
    axis.set_axis_off()
    figure.tight_layout()
    if save_path is not None:
        figure.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.show()
    return figure


def draw_colored_graph(
    graph: Graph,
    coloring: typing.List[int],
    title: str,
    colors=None,
    default_color: str = "#bbbbbb",
    show_labels=None,
    save_path=None,
    positions=None,
):
    """Draw a colored graph with a layout that remains readable at larger sizes.

    Labels are hidden automatically for graphs with more than 30 vertices.
    Set ``show_labels`` explicitly to override that behavior. If ``save_path``
    is provided, a 300 DPI copy suitable for a report is saved as well.
    """
    if colors is None:
        colors = ["#118a80", "#7661bc", "#c58b20"]

    node_count = graph.number_of_nodes()
    show_labels = node_count <= 30 if show_labels is None else show_labels
    node_size = max(45, min(600, 16000 / max(node_count, 1)))
    if positions is None:
        positions = nx.spring_layout(
            graph,
            seed=7,
            k=2 / max(node_count, 1) ** 0.5,
            iterations=150,
        )

    node_colors = []
    for node in graph.nodes:
        color_index = coloring[node] if 0 <= node < len(coloring) else -1
        if 0 <= color_index < len(colors):
            node_colors.append(colors[color_index])
        else:
            node_colors.append(default_color)

    figure, axis = plt.subplots(figsize=(10, 8))
    nx.draw_networkx_edges(
        graph,
        positions,
        ax=axis,
        edge_color="#555555",
        width=0.7,
        alpha=0.25,
    )
    nx.draw_networkx_nodes(
        graph,
        positions,
        ax=axis,
        node_color=node_colors,
        node_size=node_size,
        edgecolors="white",
        linewidths=0.5,
    )
    if show_labels:
        nx.draw_networkx_labels(
            graph,
            positions,
            ax=axis,
            font_size=8 if node_count > 15 else 11,
        )

    legend_handles = [
        plt.Line2D(
            [], [], marker="o", linestyle="", color=color,
            label=f"Color {index}", markersize=8,
        )
        for index, color in enumerate(colors)
        if index in coloring
    ]
    if legend_handles:
        axis.legend(handles=legend_handles, frameon=False, loc="upper right")

    axis.set_title(title, fontsize=16)
    axis.set_axis_off()
    figure.tight_layout()
    if save_path is not None:
        figure.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.show()
    return figure


def generate_3_colorable_graph(
    num_vertices, edge_probability: float = 1,
    seed=None, visualize: bool = False) -> typing.Tuple[Graph, list]:
    """Generate a 3-colorable graph.
    # Parameters
    - num_vertices : int
        - The number of the vertices in the graph.
    - edge_probability : float = 1
        - 0.0 <= X <= 1.0
        - The chance for there to be an edge between two differently-colored 
        nodes.
        - Even if the probability is set to 0, an edge is still created 
        in the following cases:
            - The first three nodes are always connected.
            - All nodes has at least one edge to keep the graph connected.
    - seed : int
        - The seed used to initialize the random number generator.
        - If a is omitted or None, the current system time is used. 
        See `random.seed()` for the behavior.
    - visualize : bool = False
        - Display the generated graph with its coloring when True.

    # Return
    - (graph, coloring) : tuple
        - graph : NetworkX.Graph
            - A connected 3-colorable graph.
            - The node values will be integers from 0 to `num_vertices` - 1.
        - coloring : list[int]
            - A list representing one valid 3-coloring of the graph.
            - The value at index `i` is the color of the node with value `i`.
            - The color is represented by a number that is either 0, 1, or 2.
    """

    if num_vertices < 0:
        raise ValueError("Number of vertices cannot be negative.")
    if not 0 <= edge_probability <= 1:
        raise ValueError("Edge probability must be between 0 and 1.")
    
    _random = random.Random(seed)
    graph: Graph = nx.complete_graph(min(num_vertices, 3))
    
    if num_vertices <= 3:
        coloring = list(range(num_vertices))
        if visualize:
            draw_colored_graph(graph, coloring, "Generated 3-Colorable Graph")
        return graph, coloring
    
    coloring = list(range(num_vertices)) # index: node value
    valid_neighbors_by_color = ([1, 2], [0, 2], [0, 1]) # index: color number

    for node in range(3, num_vertices):
        graph.add_node(node)
        color = _random.choice((0, 1, 2))
        coloring[node] = color

        for other_color in range(3):
            if other_color != color:
                valid_neighbors_by_color[other_color].append(node)

        connected = False
        for valid_neighbor in valid_neighbors_by_color[color]:
            if _random.random() < edge_probability:
                graph.add_edge(node, valid_neighbor)
                connected = True

        if not connected:
            graph.add_edge(node, 
                _random.choice(valid_neighbors_by_color[color]))

    if visualize:
        draw_colored_graph(graph, coloring, "Generated 3-Colorable Graph")

    return graph, coloring


def save_graph_example(graph, coloring, name, directory="examples"):
    """Save a generated graph and its private coloring as separate JSON files."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)

    graph_path = directory / f"{name}.json"
    coloring_path = directory / f"{name}_coloring.json"

    graph_data = {
        "vertices": list(graph.nodes),
        "edges": [list(edge) for edge in graph.edges],
    }
    coloring_data = {
        "colors": {str(node): coloring[node] for node in graph.nodes},
    }

    with graph_path.open("w", encoding="utf-8") as graph_file:
        json.dump(graph_data, graph_file, indent=2)
        graph_file.write("\n")

    with coloring_path.open("w", encoding="utf-8") as coloring_file:
        json.dump(coloring_data, coloring_file, indent=2)
        coloring_file.write("\n")

    return graph_path, coloring_path


def _test_load_graph():
    triangle = load_graph("examples/triangle.json")
    k4 = load_graph("examples/k4.json")

    print("triangle nodes:", list(triangle.nodes))
    print("triangle edges:", list(triangle.edges))
    print("k4 nodes:", list(k4.nodes))
    print("k4 edges:", list(k4.edges))

    draw_graph(triangle, "Triangle")
    draw_graph(k4, "K4")


def _test_generate_3_colorable_graph():
    generated, coloring = generate_3_colorable_graph(20, 0.5, 1)
    print(f"generated valid coloring: {coloring}")
    draw_colored_graph(generated, coloring, "Generated Colored Graph")

if __name__ == "__main__":
    _test_load_graph()
    _test_generate_3_colorable_graph()