import networkx as nx
from copy import deepcopy
import typing
import os
import json

from src.prover import Prover
from src.verifier import Verifier

def run_session(graph: nx.Graph, rounds: int, witness: nx.Graph = None,
    transcript: typing.TextIO = None, log_rounds: bool = True
):
    if transcript is None:
        with open(os.devnull, 'w') as null_file:
            return run_session(graph, rounds,
                    witness=witness, transcript=null_file, log_rounds=False)
    round_transcript = transcript if log_rounds else open(os.devnull, 'w')
    transcript.writelines((
        f"Graph: {graph}\n",
        f"Number of rounds: {rounds}\n\n"
    ))

    prover = Prover(deepcopy(graph), witness)
    verifier = Verifier(deepcopy(graph))

    passed = True # vacuously true
    for i in range(1, rounds + 1):
        round_transcript.write(f"Round {i}:\n")

        passed = run_round(graph, prover, verifier, transcript=round_transcript)

        if not passed:
            round_transcript.write("The edge is invalid.\n\n")
            break
        round_transcript.write("The edge is valid.\n\n")

    if not log_rounds: round_transcript.close()

    if passed:
        transcript.write(f"All {rounds} rounds are passed.\n")
    else:
        transcript.write(f"The verification failed in round {i}.\n")


def run_round(graph: nx.Graph, prover: Prover, verifier: Verifier,
    transcript: typing.TextIO = None
) -> bool:
    if transcript is None:
        with open(os.devnull, 'w') as null_file:
            return run_round(graph, prover, verifier, 
                    transcript=null_file)
    
    commitment: nx.Graph = prover.commit_round()
    transcript.write(f"Prover committed {commitment}.\n")

    edge: tuple = verifier.choose_edge(commitment)
    transcript.write(f"Verifier chosen edge {edge}.\n")

    key: dict = prover.send_key(edge)
    transcript.write(
        f"Prover send key\n" \
        + json.dumps(key, indent=4) \
        + ".\n")

    passed: bool = verifier.verify_edge(key)
    transcript.write(f"Verifier verified edge {edge}.\n")

    return passed


if __name__ == "__main__":
    import sys
    from src.graphs import (
        generate_3_colorable_graph,
        make_k4
    )
    
    graph, coloring = generate_3_colorable_graph(10, .5, 0)
    run_session(graph, 4, transcript=sys.stdout, log_rounds=False)
    run_session(graph, 4, transcript=sys.stdout, log_rounds=True)
