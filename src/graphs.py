import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import random
import typing

from copy import deepcopy

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


def _validate_count(name, value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer.")


def _color_class_options(n, good_count, bad_count):
    """Yield ordered class sizes and their multinomial assignment weights.

    Nodes 0, 1, 2 are anchored to colors 0, 1, 2. For sizes x, y, z,
    w = (n-3)! / ((x-1)! (y-1)! (z-1)!)
      = comb(n-3, x-1) * comb(n-x-2, y-1).
    Equal probability per feasible size triple would bias the coloring law.
    """
    total = n * (n - 1) // 2
    for x in range(1, n - 1):
        for y in range(1, n - x):
            z = n - x - y
            good_capacity = x * y + x * z + y * z
            if good_capacity >= good_count and total - good_capacity >= bad_count:
                weight = math.comb(n - 3, x - 1) * math.comb(n - x - 2, y - 1)
                yield (x, y, z), weight


def _sample_capacity_coloring(n, good_count, bad_count, rng):
    # Weighted reservoir sampling retains only one triple, with exact integer
    # weights. This scans O(n**2) size triples, not O(n**2) candidate edges.
    sizes = None
    total_weight = 0
    for candidate, weight in _color_class_options(n, good_count, bad_count):
        total_weight += weight
        if rng.randrange(total_weight) < weight:
            sizes = candidate
    if sizes is None:
        raise ValueError("No anchored 3-color assignment can realize these edge counts.")
    tail = [color for color, size in enumerate(sizes) for _ in range(size - 1)]
    rng.shuffle(tail)
    return [0, 1, 2] + tail


def _generate_exact_graph(num_vertices, num_edges, num_bad_edges, seed, coloring=None):
    _validate_count("num_vertices", num_vertices)
    _validate_count("num_edges", num_edges)
    _validate_count("num_bad_edges", num_bad_edges)
    if num_vertices < 3:
        raise ValueError("The triangle-backbone generator requires at least 3 vertices.")
    if num_bad_edges > num_edges:
        raise ValueError("num_bad_edges cannot exceed num_edges.")
    if num_edges > num_vertices * (num_vertices - 1) // 2:
        raise ValueError("num_edges exceeds the capacity of a simple graph.")
    good_count = num_edges - num_bad_edges
    if good_count < num_vertices:
        raise ValueError("The connected triangle backbone requires at least num_vertices good edges.")
    rng = random.Random(seed)
    if coloring is None:
        coloring = _sample_capacity_coloring(num_vertices, good_count, num_bad_edges, rng)
    else:
        if not isinstance(coloring, (list, tuple)) or len(coloring) != num_vertices:
            raise ValueError("coloring must contain one color per vertex.")
        if any(type(color) is not int or color not in (0, 1, 2) for color in coloring):
            raise ValueError("Each color must be an integer in {0, 1, 2}.")
        if len(set(coloring[:3])) != 3:
            raise ValueError("The supplied coloring must give nodes 0, 1, 2 distinct colors.")
        coloring = list(coloring)
    return _sample_exact_edges(coloring, good_count, num_bad_edges, rng)


def _decode_good_edge(edge_id, groups):
    # Rectangular blocks A x B, A x C, B x C.
    for left, right in ((0, 1), (0, 2), (1, 2)):
        size = len(groups[left]) * len(groups[right])
        if edge_id < size:
            i, j = divmod(edge_id, len(groups[right]))
            return groups[left][i], groups[right][j]
        edge_id -= size
    raise ValueError("Good-edge ID is outside the candidate range.")


def _decode_bad_edge(edge_id, groups):
    # Three triangular blocks, one for each same-color class. Binary search
    # locates a row without constructing all pairs (O(log n) per bad edge).
    for group in groups:
        size = len(group)
        capacity = size * (size - 1) // 2
        if edge_id >= capacity:
            edge_id -= capacity
            continue
        low, high = 0, size - 1
        while low + 1 < high:
            mid = (low + high) // 2
            if mid * (2 * size - mid - 1) // 2 <= edge_id:
                low = mid
            else:
                high = mid
        row_start = low * (2 * size - low - 1) // 2
        return group[low], group[low + 1 + edge_id - row_start]
    raise ValueError("Bad-edge ID is outside the candidate range.")


def _sample_exact_edges(coloring, good_count, num_bad_edges, rng):
    n = len(coloring)
    groups = [[], [], []]
    index_in_group = [0] * n
    for node, color in enumerate(coloring):
        index_in_group[node] = len(groups[color])
        groups[color].append(node)
    x, y, z = map(len, groups)
    good_capacity = x * y + x * z + y * z
    bad_capacity = sum(len(group) * (len(group) - 1) // 2 for group in groups)
    if good_count > good_capacity or num_bad_edges > bad_capacity:
        raise ValueError("The supplied coloring cannot realize these edge counts.")

    def encode_good_edge(u, v):
        a, b = coloring[u], coloring[v]
        if a > b:
            u, v, a, b = v, u, b, a
        offset = 0 if (a, b) == (0, 1) else x * y
        if (a, b) == (1, 2):
            offset += x * z
        return offset + index_in_group[u] * len(groups[b]) + index_in_group[v]

    graph = nx.empty_graph(n)
    graph.add_edges_from(((0, 1), (0, 2), (1, 2)))
    previous = [[], [], []]
    for node in range(3):
        previous[coloring[node]].append(node)
    for node in range(3, n):
        other_colors = [c for c in range(3) if c != coloring[node]]
        left, right = (previous[c] for c in other_colors)
        rank = rng.randrange(len(left) + len(right))
        parent = left[rank] if rank < len(left) else right[rank - len(left)]
        graph.add_edge(node, parent)
        previous[coloring[node]].append(node)

    backbone_ids = {encode_good_edge(u, v) for u, v in graph.edges}
    needed = good_count - len(backbone_ids)
    if needed:
        # At most n sampled IDs are in the backbone. Sampling good_count IDs
        # therefore leaves at least good_count-n usable IDs, without retries.
        # Their first needed entries uniformly sample the remaining good edges.
        for edge_id in rng.sample(range(good_capacity), good_count):
            if edge_id in backbone_ids:
                continue
            graph.add_edge(*_decode_good_edge(edge_id, groups))
            needed -= 1
            if needed == 0:
                break
    for edge_id in rng.sample(range(bad_capacity), num_bad_edges):
        graph.add_edge(*_decode_bad_edge(edge_id, groups))
    return graph, coloring


def generate_valid_graph(
    num_vertices, num_edges, seed=None, visualize=False, *, coloring=None,
):
    """Return a connected simple graph with exact edges and a valid coloring.

    Requires n >= 3 and n <= num_edges <= floor(n**2/3). Vertices are
    0..n-1; colors are 0, 1, 2. Infeasible requests raise ValueError.
    A local RNG makes equal seeds reproducible without changing global state.

    Without coloring, anchor the first three nodes to 0, 1, 2 and sample the
    remaining colors uniformly conditional on sufficient edge capacity. The
    size triples are weighted by their multinomial counts, not uniformly or
    forced to balance. Capacity conditioning necessarily changes the original
    distribution when some color assignments cannot fit the requested edges.

    A supplied coloring list/tuple is copied without recoloring; the first
    three colors must be distinct and its edge capacity must suffice. Pass
    the same coloring to both generators to fix colors across experiments.

    Build a triangle and one good edge per later node (n backbone edges),
    then sample integer edge IDs without constructing all candidate pairs.
    Color-size enumeration takes O(n**2) iterations with exact integer weights;
    edge construction takes O(n+m) space, including the graph. Graphs are not
    uniform over all connected graphs. Set visualize=True to draw the result.

    Example:
        graph, colors = generate_valid_graph(50, 300, seed=42)
    """
    graph, coloring = _generate_exact_graph(num_vertices, num_edges, 0, seed, coloring)
    if visualize:
        draw_colored_graph(graph, coloring, "Generated Valid Graph")
    return graph, coloring


def generate_invalid_graph(
    num_vertices, num_edges, num_bad_edges, seed=None, visualize=False, *, coloring=None,
):
    """Return a connected graph and coloring with exact total and bad edges.

    A bad edge has equal endpoint colors. Requires n >= 3, num_bad_edges >= 1,
    and num_edges-num_bad_edges >= n for the all-good triangle backbone.
    Both same-color and different-color capacities must suffice; otherwise
    raise ValueError. This deliberately excludes graphs outside that backbone
    model, even if another construction could realize their edge counts.

    Use the weighted conditional color sampler and good-edge backbone from
    generate_valid_graph, then sample bad-edge IDs from same-color triangular
    blocks. No full candidate-edge lists or unbounded rejection loops are used.
    Bad-edge decoding takes O(log n) per edge. The supplied coloring, seed,
    visualization and distribution conventions match generate_valid_graph.
    Invalid refers to this coloring; the graph may admit another valid one.

    Example:
        graph, colors = generate_invalid_graph(50, 300, 50, seed=42)
    """
    _validate_count("num_bad_edges", num_bad_edges)
    if num_bad_edges == 0:
        raise ValueError("num_bad_edges must be at least 1 for an invalid coloring.")
    graph, coloring = _generate_exact_graph(
        num_vertices, num_edges, num_bad_edges, seed, coloring,
    )
    if visualize:
        draw_colored_graph(graph, coloring, "Generated Invalid Coloring")
    return graph, coloring


# Legacy probability-based API; use generate_valid_graph for exact edge counts.
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


# Legacy ratio-based API; use generate_invalid_graph for exact bad-edge counts.
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
        if graph.nodes[u]['color'] == graph.nodes[v]['color']:
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

if __name__ == "__main__":
    # _demo_load_graph()
    # _demo_generate_3_colorable_graph()
    _demo_generate_corrupted_graph()
