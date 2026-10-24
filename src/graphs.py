import json
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import random
import typing
import itertools
import math

from copy import deepcopy
from collections import namedtuple

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
    show: bool=True
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
    if show:
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


def generate_corrupted_witness(orig_witness: Graph, bad_edge_ratio: float=0,
    tolerance: float=None, seed: int=None, 
    visualize: bool = False) -> Graph:
    """
    Create a witness graph with invalid edges by adding new nodes or new 
    connections between same color nodes.

    The ratio of invalid edges 
    to total edges be within the range of `ratio + tolerance`.

    Do not guarantee that the resulting graph is not 3-colorable.
    # Parameter
    - orig_witness : NetworkX.Graph
        - The witness graph of of the original graph.
        - All nodes must have the attribute 'color'.
    - bad_edge_ratio : float
        - The ratio of invalid edges / total edges
        - The returned graph is guaranteed to have at least 1 invalid edge even 
        if this ratio is set to 0.
    - tolerance : float
        - The acceptable variance of the actual bad edge ratio from the given 
        `bad_edge_ratio`.
        - Must be nonzero
    - seed : float
        - For `random.Random` from the built-in `random` library.
    - visualize : bool = False
        - Display the generated graph with its coloring when True.
    #
    """

    if not (0 <= bad_edge_ratio < 1):
        raise ValueError(
            "Bad edge ratio must be between 0 and 1, and not 1.")

    if orig_witness.number_of_edges() == 0:
        raise ValueError("The graph must have at least 1 edge.")
    for node in orig_witness.nodes():
        if 'color' not in orig_witness.nodes[node]:
            raise ValueError(
                "The nodes of the graph must have the attribute 'color'")
        if not (0 <= orig_witness.nodes[node]['color'] < 3):
            raise ValueError(
                "All nodes must have a color value of 0, 1, or 2"
            )

    if tolerance is None:
        tolerance = 1 / orig_witness.number_of_edges()
    if not (0 < tolerance <= 1):
        raise ValueError("Tolerance must be between 0 and 1, and not 0.")
    # end of input validation

    # 0 ratio
    # 0 edges
    # connect to existing edges

    witness = deepcopy(orig_witness)    
    _random = random.Random(seed)

    bad_edges = number_of_bad_edges(witness)
    nodes = list(witness.nodes.keys())
    current_ratio = bad_edges / witness.number_of_edges()

    # guarantee an invalid edge is added
    if bad_edges == 0:
        current_ratio = -2
    while not (abs(current_ratio - bad_edge_ratio) <= tolerance):
        parent = _random.choice(nodes)
        leaf = witness.number_of_nodes() # nodes are 0-indexed
        witness.add_node(leaf)

        if current_ratio < bad_edge_ratio:
            witness.nodes[leaf]['color'] = witness.nodes[parent]['color']

        elif current_ratio > bad_edge_ratio:
            witness.nodes[leaf]['color'] = (witness.nodes[parent]['color'] + 1) % 3
        
        nodes.append(leaf)
        witness.add_edge(parent, leaf)

        bad_edges += 1

        current_ratio = bad_edges / witness.number_of_edges()


    if visualize:
        _, coloring = color_separated(witness)
        draw_colored_graph(witness, coloring, "Corrupted Graph")

    return witness


def witness_graph(graph: Graph, coloring: list) -> Graph:
    """
    Generate a graph with the 'color' attribute set for every node.
    # Parameter
    - graph : NetworkX.Graph
        - The argument is unchanged
    - coloring : list[int]
        - The list of colors indexed by the node values.
    # Return
    - NetworkX.Graph
        - A new graph with the 'color' attribute set for every node."""
    if graph.number_of_nodes() != len(coloring):
        raise ValueError(
            "The number of nodes in the graph and "
            "the number of values in coloring must be the same.")
    witness = deepcopy(graph)
    nx.set_node_attributes(
        witness,
        {node: coloring[node] for node in graph.nodes},
        "color",
    )
    return witness


def number_of_bad_edges(graph: Graph) -> int:
    """
    Count the number of bad edges (where the two nodes have the same color).
    # Parameter
    - graph : NetworkX.Graph
        - All nodes of the graph must have the 'color' attribute set.
    # Return
    - int
        - The number of bad edges.
    """
    for node in graph.nodes:
        if 'color' not in graph.nodes[node]:
            raise ValueError(
                "All nodes of the graph must have the 'color' attribute.")
    # end of input validation

    bad_edges = 0
    for u, v in graph.edges:
        if graph.nodes[u] == graph.nodes[v]:
            bad_edges += 1
    return bad_edges


def color_separated(witness: Graph) -> typing.Tuple[Graph, list[int]]:
    """
    Returns the uncolored graph and list of colors separately

    Useful for getting a public graph without the witness.
    # Parameter
    - witness : NetworkX.Graph
        - All nodes of the graph must have the 'color' attribute set.
    # Return
    - Graph
        - The graph without the 'color' attributes.
    - list[int]
        - A list of the values of the 'color' attributes"""
    coloring = [0] * witness.number_of_nodes()
    for node in witness.nodes:
        coloring[node] = witness.nodes[node]['color']

    uncolored_graph = nx.Graph()
    uncolored_graph.add_edges_from(witness.edges)
    return uncolored_graph, coloring


class ColorSeparated(namedtuple("ColorSeparated", ("graph", "coloring"))):
    def __init__(self, witness):
        super().__init__(*color_separated(witness))

def generate_3_colorable_witness_with_edge_count(
    num_vertices: int, num_edges: int,
    seed=None, visualize: bool = False) -> Graph:

    if num_vertices < 1:
        raise ValueError("Number of vertices must be at least 1.")
    if num_edges < num_vertices - 1:
        raise ValueError("Not enough edges to form a connected graph.")

    _random = random.Random(seed)
    config  = _choose_3_colorable_color_configuration(
        num_vertices, num_edges, _random)
    print(config)

    if config is None:
        raise ValueError(
            "Number of edges impossible for the specified number of nodes")

    if num_vertices <= 3:
        graph:Graph = nx.complete_graph(num_vertices)
        coloring = list(range(num_vertices))
        if num_edges == 2:
            graph.remove_edge(0, 1)
        return witness_graph(graph, coloring)

    c0, c1, c2 = config
    graph = nx.Graph()
    graph.add_nodes_from(range(num_vertices))
    coloring = [0]*c0 + [1]*c1 + [2]*c2
    _random.shuffle(coloring)

    nodes_by_color = [[], [], []]
    _ensure_connectedness(
        num_vertices, _random, graph, coloring, c0, c1, c2, nodes_by_color)

    incomplete_nodes = list(graph.nodes)
    while graph.number_of_edges() < num_edges:
        u = _random.choice(incomplete_nodes)
        # print(u, graph.degree(u))
        if graph.degree[u] == num_vertices - len(nodes_by_color[coloring[u]]):
            incomplete_nodes.remove(u)
        v = random.choice(incomplete_nodes)
        i = 0
        while u == v or graph.has_edge(u, v) \
        or coloring[u] == coloring[v]:
            v = (v + 1) % num_vertices
            i += 1
            if i == 1000:
                break
        graph.add_edge(u, v)

    if visualize:
        draw_colored_graph(graph, coloring, "Generated 3-Colorable Graph")
        
    return witness_graph(graph, coloring)

def _ensure_connectedness(
    num_vertices, _random, graph, coloring, c0, c1, c2, nodes_by_color):
    for u in range(num_vertices):
        color = coloring[u]
        nodes_by_color[color].append(u)

    connected_by_color = [0, 0, 0]
    if c0 != 0:
        connected_by_color[0] += 1
        if c1 != 0:
            graph.add_edge(nodes_by_color[0][0], nodes_by_color[1][0])
            connected_by_color[1] += 1
            if c2 != 0:
                graph.add_edge(nodes_by_color[1][0], nodes_by_color[2][0])
                connected_by_color[2] += 1
        elif c2 != 0:
            graph.add_edge(nodes_by_color[0][0], nodes_by_color[2][0])
            connected_by_color[2] += 1

    elif c1 != 0:
        connected_by_color[1] += 1
        if c2 != 0:
            graph.add_edge(nodes_by_color[1][0], nodes_by_color[2][0])
            connected_by_color[2] += 1

    unconnected = nodes_by_color[0][connected_by_color[0]:] \
        + nodes_by_color[1][connected_by_color[1]:] \
        + nodes_by_color[2][connected_by_color[2]:]        
    for u in unconnected:
        color = coloring[u]

        possible_neighbors = []
        for other_color in range(3):
            if other_color == color:
                continue
            connected = connected_by_color[other_color]
            possible_neighbors += nodes_by_color[other_color][:connected]

        neighbor = _random.choice(possible_neighbors)
        graph.add_edge(u, neighbor)
        connected_by_color[color] += 1
    

def _choose_3_colorable_color_configuration(nodes, edges, _random: random.Random
) -> typing.Tuple[int, int, int] | None:
    if nodes <= 0:
        return None
    
    # redundant checks, but bounded
    if nodes < 9:
        lattices = list(itertools.product(range(0, nodes + 1), repeat=3))
        _random.shuffle(lattices)

        for x, y, z in lattices:
            if not _valid_3_color_configuration(x, y, z, nodes, edges):
                continue
            return (x, y, z)

    population = tuple(range(0, nodes + 1))
    x, y = _random.choices(population, 
        [1 / len(population)**3] + [abs(1/(nodes/3+.01-n)) for n in population[1:]], k=2)

    argmax = nodes / 3
    maxima = itertools.product(
        (math.ceil(argmax), math.floor(argmax)), repeat=3)
    maxima = set(maxima)
    z = nodes - x - y

    while (x, y, z) not in maxima:
        z = nodes - x - y
        if _valid_3_color_configuration(x, y, z, nodes, edges):
            return (int(x), int(y), int(z))
        x = (x + argmax) // 2
        y = (y + argmax) // 2

    for x, y, z in maxima:
        if _valid_3_color_configuration(x, y, z, nodes, edges):
            return (x, y, z)

    return None

def _valid_3_color_configuration(x, y, z, nodes, edges):
    return x + y + z == nodes \
        and x*y + y*z + z*x >= edges \
        and x >= 0 and y >= 0 and z >= 0


def generate_corrupted_witness_with_edge_counts(
    num_vertices: int, total_edges: int, num_invalid_edges: int,
    seed: int=None, visualize: bool = False) -> Graph:
    pass


def _demo_load_graph():
    triangle = load_graph("examples/triangle.json")
    k4 = load_graph("examples/k4.json")

    print("triangle nodes:", list(triangle.nodes))
    print("triangle edges:", list(triangle.edges))
    print("k4 nodes:", list(k4.nodes))
    print("k4 edges:", list(k4.edges))

    draw_graph(triangle, "Triangle")
    draw_graph(k4, "K4")


def _demo_generate_3_colorable_graph():
    generated, coloring = generate_3_colorable_graph(20, 0.5, 1)
    print(f"generated valid coloring: {coloring}")
    draw_colored_graph(generated, coloring, "Generated Colored Graph")

def _demo_generate_corrupted_graph():
    valid_graph, valid_coloring = generate_3_colorable_graph(
        20, 0.5, 1)
    witness = witness_graph(valid_graph, valid_coloring)
    generate_corrupted_witness(witness, 0, .1, seed=11, visualize=True)
    generate_corrupted_witness(witness, 0.5, .1, seed=11, visualize=True)

def _demo_generate_3_colorable_witness_with_edge_count():
    # generate_3_colorable_witness_with_edge_count(8, 5)
    generate_3_colorable_witness_with_edge_count(20, 100, seed=11, visualize=True)
    nodes = 100
    count = [0] * nodes
    for i in range(100):
        # _choose_3_colorable_color_configuration(20, 30, random.Random(i))
        config = _choose_3_colorable_color_configuration(
            nodes, 30, random.Random(i))
        for j in config:
            count[j] += 1
    print(count)


if __name__ == "__main__":
    # _demo_load_graph()
    # _demo_generate_3_colorable_graph()
    # _demo_generate_corrupted_graph()
    _demo_generate_3_colorable_witness_with_edge_count()