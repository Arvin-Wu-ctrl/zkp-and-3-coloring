import json
from pathlib import Path
from collections import namedtuple

from src.session import run_session
from src.graphs import (
    color_separated,
    generate_invalid_graph,
	generate_valid_graph,
    load_graph,
    witness_graph,
)

def main():
    config_path = _get_config_path(argv)
    config = _load_config(config_path)
    graphs = _load_graphs(config["graphs"])

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
        params_list = _session_parameters(session_config, graphs)

        if len(params_list) == 1:
            record = _run_session(session_config, params_list[0])
            report["sessions"][session_name] = record
            continue

        for i, params in enumerate(params_list):
            record = _run_session(session_config, params)
            report["sessions"][f"{session_name}_{i}"] = record
        

    _analyze_sessions(report)
    _save_report(output_path, report)


def _run_session(session_config, params) -> dict:
    record = run_session(*params)
    record = record.copy()
    record.update(session_config)
    return record


def _load_graphs(graph_data: dict) -> dict:
    graphs = {}
    for name, config in graph_data.items():

        if "source" in config and "coloring" in config:
            graph_path = Path(config["source"])
            color_path = Path(config["coloring"])
            graph = load_graph(graph_path)
            coloring = _load_coloring(color_path)
            graphs[name] = witness_graph(graph, coloring)

        else:
            nodes = config["nodes"]
            edges = config["edges"]
            bad_edges = config["bad_edges"]
            seed = config["seed"]
            if bad_edges == 0:
                graph, coloring = generate_valid_graph(nodes, edges, seed=seed)
            else:
                graph, coloring = generate_invalid_graph(
                    nodes, edges, bad_edges, seed=seed)
            graphs[name] = witness_graph(graph, coloring)

    return graphs


def _load_coloring(coloring_path) -> list:
    with open(coloring_path, 'r') as file:
        data = json.load(file)
    coloring = data["colors"]
    
    if isinstance(coloring, list):
        return coloring
    if isinstance(coloring, dict):
        return [v for k, v in sorted(coloring.items())]
    raise ValueError("`colors` can only be either a list or a dictionary.")


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
    accepted = 0
    for data in report["sessions"].values(): # session data
        if data["accepted"]:
            accepted += 1
        
    report["acceptance"] = accepted / len(report["sessions"])


SessionParameters = namedtuple("SessionParameters", 
    ["graph", "rounds", "witness", "seeds"])
def _session_parameters(config: dict, graphs: dict) -> list[SessionParameters]:
    graph_name = config["graph"]
    witness = graphs[graph_name]
    uncolored_graph, coloring = color_separated(witness)
    rounds = config["max_rounds"]

    if "seeds" in config:
        seeds = config["seeds"]
    else:
        seeds = [config.get("seed", 0)]

    return [
        SessionParameters(uncolored_graph, rounds, witness, seed)
        for seed in seeds
    ]


if __name__ == "__main__":
    from sys import argv
    main()