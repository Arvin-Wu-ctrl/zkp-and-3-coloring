import json
from pathlib import Path

import networkx as nx
import pytest
from copy import deepcopy

from src.graphs import (
    color_separated,
    generate_3_colorable_graph,
    generate_3_colorable_witness_with_edge_count,
    generate_corrupted_witness,
    generate_corrupted_witness_with_edge_counts,
    witness_graph,
    load_graph,
    load_graph_from_data,
    number_of_bad_edges,
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


########## generate_corrupted_witness ##########

@pytest.mark.parametrize("bad_edge_ratio, tolerance", [
    (0, .1),
    (.5, .000001),
])
def test_generate_corrupted_witness_with_invalid_coloring(bad_edge_ratio, tolerance):
    valid_graph, coloring = generate_3_colorable_graph(12, 0.3, seed=11)
    valid_witness = witness_graph(valid_graph, coloring)

    invalid_witness = generate_corrupted_witness(
        valid_witness, 
        bad_edge_ratio=bad_edge_ratio, 
        tolerance=tolerance,
        seed=11
    )
    invalid_graph, invalid_coloring = color_separated(invalid_witness)

    assert nx.is_connected(invalid_witness)
    assert Prover(invalid_graph, invalid_witness)._check_coloring() is False


@pytest.mark.parametrize("expected_ratio, tolerance", [(0.5, 0.1)])
def test_generate_corrupted_witness_control_bad_edge_ratio(expected_ratio, tolerance):
    valid_graph, coloring = generate_3_colorable_graph(12, 0.3, seed=11)
    valid_witness = witness_graph(valid_graph, coloring)

    invalid_witness = generate_corrupted_witness(valid_witness, expected_ratio, seed=11)

    actual_ratio = number_of_bad_edges(invalid_witness) / invalid_witness.number_of_edges()
    assert abs(actual_ratio - expected_ratio) <= tolerance


def test_generate_corrupted_witness_is_seeded():
    valid_graph, coloring = generate_3_colorable_graph(12, 0.3, seed=11)
    valid_witness = witness_graph(valid_graph, coloring)

    witness1 = generate_corrupted_witness(valid_witness, 0.5, seed=11)
    witness2 = generate_corrupted_witness(valid_witness, 0.5, seed=11)
    witness3 = generate_corrupted_witness(valid_witness, 0.5, seed=12)

    assert nx.utils.graphs_equal(witness1, witness2)
    assert not nx.utils.graphs_equal(witness1, witness3)


def test_generate_corrupted_witness_not_change_original_graph():
    valid_graph, coloring = generate_3_colorable_graph(12, 0.3, seed=11)
    valid_witness = witness_graph(valid_graph, coloring)
    original = deepcopy(valid_witness)

    invalid_witness = generate_corrupted_witness(valid_witness, 0.5, seed=11)

    assert nx.utils.graphs_equal(original, valid_witness)

########## generate_3_colorable_witness_with_edge_count ##########

@pytest.mark.parametrize("num_vertices, num_edges", [
    (2, 1),
    (3, 3),
    (10, 9),
    (10, 20),
    (20, 100),
])
def test_generate_3_colorable_witness_with_edge_count_valid_coloring(
        num_vertices, num_edges):

    graph = generate_3_colorable_witness_with_edge_count(
        num_vertices, num_edges, seed=11)

    assert graph.number_of_nodes() == num_vertices
    assert nx.is_connected(graph)
    assert number_of_bad_edges(graph) == 0

def test_generate_witness_with_edge_count_is_reproducible_with_seed():
    graph1 = generate_3_colorable_witness_with_edge_count(13, 12, seed=11)
    graph2 = generate_3_colorable_witness_with_edge_count(13, 12, seed=11)
    assert set(graph1.edges) == set(graph2.edges)

@pytest.mark.parametrize("num_vertices, num_edges", [
    (2, 1),
    (3, 3),
    (10, 9),
    (10, 20),
])
def test_generate_witness_with_edge_count_correct_number_of_edges(
    num_vertices, num_edges):
    graph = generate_3_colorable_witness_with_edge_count(
        num_vertices, num_edges, seed=11)
    assert graph.number_of_edges() == num_edges
