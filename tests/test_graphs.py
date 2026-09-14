import json
from pathlib import Path

import pytest

from src.graphs import load_graph, load_graph_from_data


@pytest.fixture
def triangle_json_path():
    return Path(__file__).resolve().parents[1] / "examples" / "triangle.json"


def test_load_graph_reads_vertices_and_edges(triangle_json_path):
    graph = load_graph(triangle_json_path)

    assert set(graph.nodes) == {0, 1, 2}
    assert set(graph.edges) == {(0, 1), (1, 2), (0, 2)}


def test_load_graph_accepts_string_path(triangle_json_path):
    graph = load_graph(str(triangle_json_path))

    assert graph.number_of_nodes() == 3
    assert graph.number_of_edges() == 3


def test_load_graph_works_for_k4():
    graph = load_graph("examples/k4.json")

    assert graph.number_of_nodes() == 4
    assert graph.number_of_edges() == 6


def test_load_graph_rejects_edge_with_missing_vertex():
    bad_graph = {
        "vertices": [0, 1],
        "edges": [[0, 2]],
    }

    with pytest.raises(ValueError, match="missing vertex"):
        load_graph_from_data(bad_graph)
