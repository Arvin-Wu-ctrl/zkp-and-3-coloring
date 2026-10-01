import json
from pathlib import Path

import networkx as nx
import pytest

from src.graphs import (
    generate_3_colorable_graph,
    load_graph,
    load_graph_from_data,
    save_graph_example,
)
from src.prover import Prover


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


def test_generate_larger_graph_with_valid_coloring():
    graph, coloring = generate_3_colorable_graph(12, 0.3, seed=11)

    witness = graph.copy()
    nx.set_node_attributes(
        witness,
        {node: coloring[node] for node in graph.nodes},
        "color",
    )

    assert graph.number_of_nodes() == 12
    assert nx.is_connected(graph)
    assert Prover(graph, witness)._check_coloring() is True


def test_generate_graph_is_reproducible_with_seed():
    first_graph, first_coloring = generate_3_colorable_graph(12, 0.3, seed=11)
    second_graph, second_coloring = generate_3_colorable_graph(12, 0.3, seed=11)

    assert first_coloring == second_coloring
    assert set(first_graph.edges) == set(second_graph.edges)


@pytest.mark.parametrize("edge_probability", [-0.1, 1.1])
def test_generate_graph_rejects_invalid_edge_probability(edge_probability):
    with pytest.raises(ValueError, match="between 0 and 1"):
        generate_3_colorable_graph(12, edge_probability, seed=11)


def test_generate_graph_can_optionally_visualize(monkeypatch):
    visualized = []

    def record_visualization(graph, coloring, title):
        visualized.append((graph, coloring, title))

    monkeypatch.setattr("src.graphs.draw_colored_graph", record_visualization)

    generate_3_colorable_graph(12, 0.3, seed=11)
    assert visualized == []

    graph, coloring = generate_3_colorable_graph(
        12, 0.3, seed=11, visualize=True
    )
    assert visualized == [(graph, coloring, "Generated 3-Colorable Graph")]


def test_save_graph_example_keeps_graph_and_coloring_separate(tmp_path):
    graph, coloring = generate_3_colorable_graph(12, 0.3, seed=11)

    graph_path, coloring_path = save_graph_example(
        graph, coloring, "generated_test", directory=tmp_path
    )

    saved_graph = load_graph(graph_path)
    saved_coloring = json.loads(coloring_path.read_text(encoding="utf-8"))

    assert set(saved_graph.nodes) == set(graph.nodes)
    assert set(saved_graph.edges) == set(graph.edges)
    assert saved_coloring["colors"] == {
        str(node): coloring[node] for node in graph.nodes
    }
