import json
import typing
import random
from pathlib import Path
from collections import namedtuple

from src.session import run_session
from src.graphs import (
    color_separated,
    generate_invalid_graph,
	generate_valid_graph,
    Graph,
    load_graph,
    number_of_bad_edges,
    save_graph_example,
    witness_graph,
)

def main():
    config_path = _get_config_path(argv)
    config = _load_config(config_path)
    output_path = _get_output_path(config_path, config)

    graphs, graph_reports = _load_graphs(config["graphs"], output_path)
    sessions = config["sessions"]

    report = {
        "graphs": graph_reports,
        "sessions": {},
    }
    print("Running the experiment...")
    _run_sessions(graphs, sessions, report)
    _analyze_sessions(report)
    _save_report(output_path, report)


def _run_sessions(graphs, sessions, report):
    for session_name, session_config in sessions.items():
        params_list = _get_session_parameters(session_config, graphs)

        if len(params_list) == 1:
            record = _run_session(session_config, params_list[0])
            report["sessions"][session_name] = record
            continue

        for i, params in enumerate(params_list):
            record = _run_session(session_config, params)
            report["sessions"][f"{session_name}_{i}"] = record


def _get_output_path(config_path, config) -> Path:
    if "output" in config:
        return Path(config["output"])
    else:
        return Path(f"./results/{config_path.stem}-report.json")


def _run_session(session_config, params) -> dict:
    record = run_session(*params)
    record = record.copy()
    record.update(session_config)
    return record


def _load_graphs(graph_data: dict, output_path: Path
        ) -> typing.Tuple[dict, dict]:
    
    graphs = {}
    graph_reports = {}
    for graph_name, config in graph_data.items():
        report = {}

        if "source" in config and "coloring" in config:

            graph_path = Path(config["source"])
            color_path = Path(config["coloring"])
            graph = load_graph(graph_path)
            coloring = _load_coloring(color_path)
            witness = graphs[graph_name] = witness_graph(graph, coloring)

            report["source"] = config["source"]
            report["coloring"] = config["coloring"]
            report["nodes"] = witness.number_of_nodes()
            report["edges"] = witness.number_of_nodes()
            report["bad_edges"] = number_of_bad_edges(witness)

        else:
            graph, coloring = _generate_graphs(config)
            graphs[graph_name] = witness_graph(graph, coloring)

            report["nodes"] = config["nodes"]
            report["edges"] = config["edges"]
            report["bad_edges"] = config["bad_edges"]
            report["topology"] = {
                "vertices": list(graph.nodes),
                "edges": [list(edge) for edge in graph.edges],
            }
            report["colors"] = {
                str(node): coloring[node] for node in graph.nodes
            }

        graph_reports[graph_name] = report

    return graphs, graph_reports

def _generate_graphs(config):
    nodes = config["nodes"]
    edges = config["edges"]
    bad_edges = config["bad_edges"]
    seed = config["seed"]
            
    if bad_edges == 0:
        graph, coloring = generate_valid_graph(nodes, edges, seed=seed)
    else:
        graph, coloring = generate_invalid_graph(
            nodes, edges, bad_edges, seed=seed)

    return graph, coloring


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
            print("No configuration file provided, " +
                f"loading default from {DEFAULT_CONFIG_PATH}")
            return DEFAULT_CONFIG_PATH
        case 2:
            path = Path(argv[1])
            print(f"Loading configuration from {path}")
            return Path(path)
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
    accepted_count = {graph_name: 0 for graph_name in report["graphs"]}
    total_count = {graph_name: 0 for graph_name in report["graphs"]}

    for data in report["sessions"].values(): # session data
        graph_name = data["graph"]
        if data["accepted"]:
            accepted_count[graph_name] += 1
        total_count[graph_name] += 1

    for graph_name in report["graphs"]:
        accepted = accepted_count[graph_name]
        total = total_count[graph_name]
        graph_report = report["graphs"][graph_name]
        graph_report["acceptance"] = accepted / total

        bad_edges = graph_report["bad_edges"]
        edges = graph_report["edges"]
        graph_report["theoretical_acceptance"] = (1 - bad_edges/edges)**total


SessionParameters = namedtuple("SessionParameters", 
    ["graph", "rounds", "witness", "seeds"])
def _get_session_parameters(config: dict, graphs: dict) -> list[SessionParameters]:
    graph_name = config["graph"]
    witness = graphs[graph_name]
    uncolored_graph, coloring = color_separated(witness)
    rounds = config["max_rounds"]

    if "seeds" in config:
        seeds = config["seeds"]
        return [
            SessionParameters(uncolored_graph, rounds, witness, seed)
            for seed in seeds
            ]
    else:
        seed = config.get("seed", 0)
        sessions_num = config.get("sessions", 1)
        _random = random.Random(seed)
        return [
            SessionParameters(
                uncolored_graph, rounds, witness, _random.random()
            ) for _ in range(sessions_num)
        ]


if __name__ == "__main__":
    from sys import argv
    main()