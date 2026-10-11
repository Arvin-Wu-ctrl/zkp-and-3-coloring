import networkx as nx

from src.commitments import check_opening
from src.graphs import load_graph
from src.prover import Prover
from src.session import run_session
from src.verifier import Verifier


def test_prover_accepts_valid_witness():
    graph = nx.Graph()
    graph.add_edges_from([(0, 1), (1, 2), (2, 0)])

    witness = nx.Graph()
    witness.add_nodes_from(graph.nodes)
    witness.add_edges_from(graph.edges)
    for node, color in {0: 0, 1: 1, 2: 2}.items():
        witness.nodes[node]["color"] = color

    prover = Prover(graph, witness)

    assert prover._check_coloring() is True


def test_commit_round_and_verify_edge_round_trip():
    graph = nx.Graph()
    graph.add_edges_from([(0, 1), (1, 2), (2, 0)])

    witness = nx.Graph()
    witness.add_nodes_from(graph.nodes)
    witness.add_edges_from(graph.edges)
    for node, color in {0: 0, 1: 1, 2: 2}.items():
        witness.nodes[node]["color"] = color

    graph_before = graph.copy()
    witness_before = witness.copy()
    prover = Prover(graph, witness, seed=3)
    verifier = Verifier(graph, seed=3)

    commitment_graph = prover.commit_round()
    round_colors = {
        node: prover._current_commitments[node]["color"] for node in graph.nodes
    }
    assert all(round_colors[u] != round_colors[v] for u, v in graph.edges)
    assert nx.utils.graphs_equal(graph, graph_before)
    assert nx.utils.graphs_equal(witness, witness_before)
    assert all(
        set(commitment_graph.nodes[node]) == {"commitment"}
        for node in commitment_graph.nodes
    )
    edge = verifier.choose_edge(commitment_graph)
    key = prover.send_key(edge)

    assert verifier.verify_edge(key) is True
    assert check_opening(
        prover._current_commitments[edge[0]]["commitment"],
        prover._current_commitments[edge[0]]["color"],
        prover._current_commitments[edge[0]]["nonce"],
    ) is True


def test_invalid_witness_is_preserved_and_committed():
    graph = nx.Graph()
    graph.add_edges_from([(0, 1), (1, 2), (2, 0)])

    witness = graph.copy()
    colors = {0: 0, 1: 0, 2: 2}
    nx.set_node_attributes(witness, colors, "color")

    prover = Prover(graph, witness, seed=4)
    prover.commit_round()

    assert prover._check_coloring() is False
    assert prover._node_colors() == colors
    assert (
        prover._current_commitments[0]["color"]
        == prover._current_commitments[1]["color"]
    )
    assert nx.get_node_attributes(witness, "color") == colors


def test_valid_triangle_passes_multiple_rounds():
    graph = load_graph("examples/triangle.json")
    witness = graph.copy()
    nx.set_node_attributes(witness, {0: 0, 1: 1, 2: 2}, "color")

    result = run_session(graph, rounds=8, witness=witness)

    assert result["accepted"] is True
    assert len(result["rounds"]) == 8
    assert all(record["passed"] for record in result["rounds"])
    assert all(graph.has_edge(*record["edge"]) for record in result["rounds"])


def test_session_stops_at_first_failed_round(monkeypatch):
    graph = load_graph("examples/triangle.json")
    witness = graph.copy()
    nx.set_node_attributes(witness, {0: 0, 1: 1, 2: 2}, "color")
    decisions = iter([True, False, True])
    monkeypatch.setattr(
        Verifier,
        "verify_edge",
        lambda self, key: next(decisions),
    )

    result = run_session(graph, rounds=3, witness=witness)

    assert result["accepted"] is False
    assert [record["passed"] for record in result["rounds"]] == [True, False]
