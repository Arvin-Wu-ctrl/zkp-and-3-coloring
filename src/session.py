import networkx as nx
from copy import deepcopy

from src.prover import Prover
from src.verifier import Verifier


def run_session(graph: nx.Graph, rounds: int, witness: nx.Graph = None):

    prover = Prover(deepcopy(graph), witness)
    verifier = Verifier(deepcopy(graph))

    for i in range(1, rounds + 1):
        passed = run_round(graph, prover, verifier)
        if not passed:
            break


def run_round(graph: nx.Graph, prover: Prover, verifier: Verifier) -> bool:
    commitment: nx.Graph = prover.commit_round()
    edge: tuple = verifier.choose_edge(commitment)
    key: dict = prover.send_key(edge)
    passed: bool = verifier.verify_edge(key)
    return passed


if __name__ == "__main__":
    run_session(nx.Graph(), 1)
    raise NotImplementedError