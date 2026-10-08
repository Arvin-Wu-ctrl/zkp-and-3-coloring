import networkx as nx
from copy import deepcopy

from src.prover import Prover
from src.verifier import Verifier


def run_session(graph: nx.Graph, rounds: int, witness: nx.Graph = None):
    """Run up to ``rounds`` rounds, stopping at the first rejection."""
    if not isinstance(rounds, int) or rounds < 0:
        raise ValueError("Rounds must be a non-negative integer.")

    prover = Prover(deepcopy(graph), witness)
    verifier = Verifier(deepcopy(graph))

    # small history, what verifier checked each round
    records = []
    for round_number in range(1, rounds + 1):
        passed, edge = _execute_round(prover, verifier)
        records.append({
            "round": round_number,
            "edge": edge,
            "passed": passed,
        })

        # one round fail -> whole session reject
        if not passed:
            return {"accepted": False, "rounds": records}

    return {"accepted": True, "rounds": records}


def _execute_round(prover: Prover, verifier: Verifier) -> tuple[bool, tuple]:
    # call commit_round again, fresh commitment data each round
    commitment: nx.Graph = prover.commit_round()
    edge: tuple = verifier.choose_edge(commitment)
    key: dict = prover.send_key(edge)
    passed: bool = verifier.verify_edge(key)
    return passed, edge


def run_round(graph: nx.Graph, prover: Prover, verifier: Verifier) -> bool:
    passed, _ = _execute_round(prover, verifier)
    return passed


if __name__ == "__main__":
    run_session(nx.Graph(), 1)
    raise NotImplementedError