import json
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx


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


if __name__ == "__main__":
    triangle = load_graph("examples/triangle.json")
    k4 = load_graph("examples/k4.json")

    print("triangle nodes:", list(triangle.nodes))
    print("triangle edges:", list(triangle.edges))
    print("k4 nodes:", list(k4.nodes))
    print("k4 edges:", list(k4.edges))

    draw_graph(triangle, "Triangle")
    draw_graph(k4, "K4")