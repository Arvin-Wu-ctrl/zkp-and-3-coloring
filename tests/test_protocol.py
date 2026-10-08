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

    prover = Prover(graph, witness)
    verifier = Verifier(graph)

    commitment_graph = prover.commit_round()
    edge = verifier.choose_edge(commitment_graph)
    key = prover.send_key(edge)

    assert verifier.verify_edge(key) is True
    assert check_opening(
        prover._current_commitments[edge[0]]["commitment"],
        prover._current_commitments[edge[0]]["color"],
        prover._current_commitments[edge[0]]["nonce"],
    ) is True


def test_invalid_witness_is_repaired():
    graph = nx.Graph()
    graph.add_edges_from([(0, 1), (1, 2), (2, 0)])

    witness = nx.Graph()
    witness.add_nodes_from(graph.nodes)
    witness.add_edges_from(graph.edges)
    for node, color in {0: 0, 1: 0, 2: 2}.items():
        witness.nodes[node]["color"] = color

    prover = Prover(graph, witness, search_budget=20)

    assert prover._check_coloring() is True
    assert prover._witness[0] != prover._witness[1]


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
