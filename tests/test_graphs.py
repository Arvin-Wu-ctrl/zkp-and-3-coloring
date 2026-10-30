import json
import itertools
import random
from pathlib import Path

import networkx as nx
import pytest
from copy import deepcopy

from src.graphs import (
    color_separated,
    generate_3_colorable_graph,
    generate_corrupted_witness,
    generate_valid_graph,
    generate_invalid_graph,
    _color_class_options,
    _decode_good_edge,
    _decode_bad_edge,
    witness_graph,
    load_graph,
    load_graph_from_data,
    number_of_bad_edges,
    save_graph_example,
)
from src.prover import Prover


@pytest.mark.parametrize("n", range(6))
def test_exact_generators_cover_all_small_feasible_counts(n):
    # Independent oracle: enumerate colorings rather than class-size partitions.
    capacities = set()
    pairs = list(itertools.combinations(range(n), 2))
    tails = itertools.product(range(3), repeat=n - 3) if n >= 3 else []
    for tail in tails:
        coloring = (0, 1, 2) + tail
        bad = sum(coloring[u] == coloring[v] for u, v in pairs)
        capacities.add((len(pairs) - bad, bad))
    for total in range(len(pairs) + 1):
        for bad in range(total + 1):
            feasible = total - bad >= n and any(
                g >= total - bad and b >= bad for g, b in capacities
            )
            generate = generate_valid_graph if bad == 0 else generate_invalid_graph
            args = (n, total) if bad == 0 else (n, total, bad)
            if not feasible:
                with pytest.raises(ValueError):
                    generate(*args, seed=11)
                continue
            graph, coloring = generate(*args, seed=11)
            assert list(graph.nodes) == list(range(n))
            assert len(coloring) == n
            assert set(coloring) <= {0, 1, 2}
            assert graph.number_of_edges() == total
            assert nx.number_of_selfloops(graph) == 0
            assert nx.is_connected(graph)
            assert coloring[:3] == [0, 1, 2]
            assert graph.has_edge(0, 1) and graph.has_edge(0, 2) and graph.has_edge(1, 2)
            assert sum(coloring[u] == coloring[v] for u, v in graph.edges) == bad


@pytest.mark.parametrize("generate,args", [
    (generate_valid_graph, (20, 60)),
    (generate_invalid_graph, (20, 60, 15)),
])
def test_exact_generators_seed_and_global_random_state(generate, args):
    state = random.getstate()
    first, colors = generate(*args, seed=42)
    second, other_colors = generate(*args, seed=42)
    assert nx.utils.graphs_equal(first, second)
    assert colors == other_colors
    assert random.getstate() == state
    assert number_of_bad_edges(witness_graph(first, colors)) == (
        args[2] if len(args) == 3 else 0
    )


@pytest.mark.parametrize("args", [(-1, 0), (3, -1), (3.0, 2), (3, True), (2, 2)])
def test_exact_valid_rejects_invalid_counts(args):
    with pytest.raises(ValueError):
        generate_valid_graph(*args)


@pytest.mark.parametrize("args", [
    (3, 2, 0), (3, 2, -1), (3, 2, 3), (3, 2, 1.5),
    (3, 3, 2), (0, 1, 1), (3, 2, True),
])
def test_exact_invalid_rejects_invalid_counts(args):
    with pytest.raises(ValueError):
        generate_invalid_graph(*args)


@pytest.mark.parametrize("generate,args", [
    (generate_valid_graph, (5, 5)),
    (generate_invalid_graph, (5, 7, 2)),
])
def test_exact_generators_optional_visualization(monkeypatch, generate, args):
    calls = []
    monkeypatch.setattr("src.graphs.draw_colored_graph", lambda *args: calls.append(args))
    generate(*args, seed=1)
    assert calls == []
    graph, coloring = generate(*args, seed=1, visualize=True)
    assert calls[0][:2] == (graph, coloring)


def test_bad_edge_count_compares_colors_only():
    graph = nx.Graph()
    graph.add_node(0, color=1, label="a")
    graph.add_node(1, color=1, label="b")
    graph.add_edge(0, 1)
    assert number_of_bad_edges(graph) == 1


def test_fixed_coloring_preserved_across_edge_counts_and_generators():
    coloring = [0, 1, 2] * 4
    original = coloring.copy()
    for total, bad in [(12, 0), (20, 0), (48, 0), (20, 3), (30, 18)]:
        generate = generate_valid_graph if bad == 0 else generate_invalid_graph
        args = (12, total) if bad == 0 else (12, total, bad)
        graph, returned = generate(*args, seed=42, coloring=coloring)
        repeated, repeated_colors = generate(*args, seed=42, coloring=coloring)
        assert nx.utils.graphs_equal(graph, repeated)
        assert returned == repeated_colors == original == coloring
        assert returned is not coloring
        assert graph.number_of_edges() == total
        assert sum(returned[u] == returned[v] for u, v in graph.edges) == bad


@pytest.mark.parametrize("coloring", [[0], [0, 1, 3], [0, 1, True], [0, 1, 1.0]])
def test_supplied_coloring_is_validated(coloring):
    with pytest.raises(ValueError):
        generate_valid_graph(3, 3, coloring=coloring)
    with pytest.raises(ValueError):
        generate_invalid_graph(3, 4, 1, coloring=coloring)


def test_fixed_coloring_infeasible_counts_do_not_recolor():
    with pytest.raises(ValueError, match="supplied coloring"):
        generate_valid_graph(4, 4, coloring=[0, 0, 0, 0])
    with pytest.raises(ValueError, match="supplied coloring"):
        generate_invalid_graph(4, 6, 2, coloring=[0, 1, 2, 0])


@pytest.mark.parametrize("n", range(3, 8))
def test_color_weights_match_exhaustive_conditional_assignments(n):
    from collections import Counter

    for good, bad in [(n, 0), (n, 1), (n * n // 3, 0)]:
        counts = Counter()
        for tail in itertools.product(range(3), repeat=n - 3):
            colors = (0, 1, 2) + tail
            sizes = tuple(colors.count(c) for c in range(3))
            good_capacity = sum(sizes[i] * sizes[j] for i in range(3) for j in range(i + 1, 3))
            if good_capacity >= good and n * (n - 1) // 2 - good_capacity >= bad:
                counts[sizes] += 1
        assert dict(_color_class_options(n, good, bad)) == dict(counts)


@pytest.mark.parametrize("sizes", list(itertools.product(range(1, 5), repeat=3)))
def test_integer_edge_decoders_cover_each_candidate_once(sizes):
    groups = []
    offset = 0
    for size in sizes:
        groups.append(list(range(offset, offset + size)))
        offset += size
    good = {tuple(sorted((u, v))) for a, b in itertools.combinations(groups, 2)
            for u in a for v in b}
    bad = {pair for group in groups for pair in itertools.combinations(group, 2)}
    decoded_good = [tuple(sorted(_decode_good_edge(i, groups))) for i in range(len(good))]
    decoded_bad = [tuple(sorted(_decode_bad_edge(i, groups))) for i in range(len(bad))]
    assert len(set(decoded_good)) == len(good)
    assert set(decoded_good) == good
    assert len(set(decoded_bad)) == len(bad)
    assert set(decoded_bad) == bad


@pytest.mark.parametrize("seed", range(10))
def test_connected_sampler_sparse_dense_and_bad_capacity_boundaries(seed):
    # Fixed, deliberately unbalanced classes exercise all ID blocks.
    colors = [2, 0, 1] + [0] * 5 + [1] * 2
    sizes = [colors.count(c) for c in range(3)]
    good_capacity = sum(sizes[i] * sizes[j] for i in range(3) for j in range(i + 1, 3))
    bad_capacity = sum(s * (s - 1) // 2 for s in sizes)
    for good in (len(colors), len(colors) + 1, good_capacity):
        for bad in (0, 1, bad_capacity):
            args = (len(colors), good + bad)
            if bad:
                graph, returned = generate_invalid_graph(*args, bad, seed=seed, coloring=colors)
            else:
                graph, returned = generate_valid_graph(*args, seed=seed, coloring=colors)
            assert returned == colors
            assert nx.is_connected(graph)
            assert graph.number_of_edges() == good + bad
            assert sum(colors[u] == colors[v] for u, v in graph.edges) == bad


def test_sparse_edge_sampling_uses_integer_ranges(monkeypatch):
    populations = []
    original = random.Random.sample

    def record_sample(rng, population, k):
        assert isinstance(population, range)
        populations.append((len(population), k))
        return original(rng, population, k)

    monkeypatch.setattr(random.Random, "sample", record_sample)
    colors = [0, 1, 2] * 20
    graph, _ = generate_invalid_graph(60, 63, 2, seed=42, coloring=colors)
    assert populations == [(1200, 61), (570, 2)]
    assert graph.number_of_edges() == 63


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

