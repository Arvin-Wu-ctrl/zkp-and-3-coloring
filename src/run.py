import json
from pathlib import Path
from collections import namedtuple

from src.session import run_session
from src.graphs import (
    generate_invalid_graph,
	generate_valid_graph,
    witness_graph,
)

def main():
    config_path = _get_config_path(argv)
    config = _load_config(config_path)

    if "output" in config:
        output_path = Path(config["output"])
    else:
        output_path = Path(f"./results/{config_path.stem}-report.json")
    if "sessions" not in config:
        raise ValueError("Key sessions must be defined.")
    sessions = config["sessions"]

    report = {
        "sessions": {},
    }

    for session_name, session_config in sessions.items():
        params = _setup_session(session_config)
        
        record = run_session(*params)
        
        record = record.copy()
        record.update(session_config)

        report["sessions"][session_name] = record

    _analyze_sessions(report)
    _save_report(output_path, report)


def _get_config_path(argv) -> Path:
    DEFAULT_CONFIG_PATH = Path("./experiments/compare_1_each.json")
    match len(argv):
        case 1:
            print("No config file provided, " +
                f"loading default from {DEFAULT_CONFIG_PATH}")
            return DEFAULT_CONFIG_PATH
        case 2:
            return Path(argv[1])
        case _:
            print("Incorrect number of arguments, " +
                f"loading default from {DEFAULT_CONFIG_PATH}")
            return DEFAULT_CONFIG_PATH


def _load_config(path) -> dict:
    with open(path, 'r') as file:
        return json.load(file)


def _save_report(output_path, report):
    with open(output_path, 'w') as file:
        json.dump(report, file, indent=2)

    print(f"Experimentation succeeded, report written to {output_path}")


def _analyze_sessions(report):
    """include empirical acceptance, theoretical acceptance, better with a confidence interval"""
    for data in report["sessions"].values(): # session data
        bad_edges = data["bad_edges"]
        edges = data["edges"]
        max_rounds = data["max_rounds"]

        data["theoretical_acceptance"] = (1 - bad_edges/edges)**max_rounds


SessionParameters = namedtuple("SessionParameters", 
    ["graph", "rounds", "witness"])
def _setup_session(config: dict) -> SessionParameters:
    nodes = config["nodes"]
    edges = config["edges"]
    bad_edges = config["bad_edges"]
    seed = config["seed"]
    rounds = config["max_rounds"]

    if bad_edges == 0:
        graph, coloring = generate_valid_graph(
            nodes, edges, seed=seed, visualize=False)
    else:
        graph, coloring = generate_invalid_graph(
            nodes, edges, bad_edges, seed=seed)

    witness = witness_graph(graph, coloring)

    return SessionParameters(graph, rounds, witness)


if __name__ == "__main__":
    from sys import argv
    main()