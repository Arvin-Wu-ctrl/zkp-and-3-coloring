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


def draw_graph(graph, title):
    positions = nx.spring_layout(graph, seed=7)

    nx.draw(
        graph,
        positions,
        with_labels=True,
        node_color="#65c3ba",
        node_size=1200,
        font_size=12,
        edge_color="#555555",
    )

    plt.title(title)
    plt.show()


def draw_colored_graph(graph: Graph, coloring: typing.List[int], title: str, 
    colors: list = ["#118a80", "#7661bc", "#c58b20"], 
    default_color: str = "#bbbbbb"):
    """
    Draw the colored graph in `NetworkX.circular_layout` and show it with 
    `mathplotlib.pyplot`.
    # Parameters
    - graph : networkx.Graph
        - A NetworkX Graph with the node value being the index to locate the 
        color in the `coloring` argument.
    - coloring : list[int]
        - A list consists of integer representing the colors with integers. 
        - The list is indexed by the node values.
        - A color represented by integer `n` is displayed with the `n`th item 
        of the `colors` argument.
    - title : str
    - colors : list[str]
        - A list consists of the hexadecimal representation of the displayed 
        colors.
    - default_color : str
        - The hexadecimal representation of the color to be used for color 
        indices beyond the list given in the `colors` argument.
    """
    
    # positions = nx.spring_layout(graph, seed=7)
    positions = nx.circular_layout(graph)

    node_color = []
    for node in graph.nodes:
        color_index = coloring[node] if 0 <= node < len(coloring) else -1
        if 0 <= color_index < len(colors):
            node_color.append(colors[color_index])
        else:
            node_color.append(default_color)

    nx.draw(
        graph,
        positions,
        with_labels=True,
        node_color=node_color,
        node_size=600,
        font_size=12,
        edge_color="#555555",
    )

    plt.title(title)
    plt.show()


def generate_3_colorable_graph(
    num_vertices, edge_probability: float = 1, 
    seed=None) -> typing.Tuple[Graph, list]:
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
    
    _random = random.Random(seed)
    graph: Graph = nx.complete_graph(min(num_vertices, 3))
    
    if num_vertices <= 3:
        return graph, list(range(num_vertices))
    
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

    return graph, coloring


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