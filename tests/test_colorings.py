import networkx as nx

from src.colorings import relabel_coloring


def test_relabeling_preserves_valid_coloring_without_mutation():
    graph = nx.cycle_graph(3)
    original_edges = set(graph.edges)
    colors = {0: 0, 1: 1, 2: 2}

    relabeled = relabel_coloring(colors, {0: 2, 1: 0, 2: 1})

    assert all(relabeled[u] != relabeled[v] for u, v in graph.edges)
    assert colors == {0: 0, 1: 1, 2: 2}
    assert set(graph.edges) == original_edges


def test_relabeling_accepts_invalid_coloring():
    colors = {0: 0, 1: 0, 2: 2}

    relabeled = relabel_coloring(colors, {0: 1, 1: 2, 2: 0})

    assert relabeled == {0: 1, 1: 1, 2: 0}
    assert colors == {0: 0, 1: 0, 2: 2}
