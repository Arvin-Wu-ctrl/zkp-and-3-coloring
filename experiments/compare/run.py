# Goal
# Run every experiment condition from one config and save a reproducible summary.

# Expected behavior
# compare honest and corrupted colorings across chosen round counts
# record graph/case info, seeds, m, b, trials, accepts, rejects, etc.
# include empirical acceptance, theoretical acceptance, better with a confidence interval
# save config + JSON results
# small automated smoke test; full run stays outside pytest

import json

from pathlib import Path

from src.session import run_session
from src.graphs import (
	color_separated,
	draw_colored_graph,
	generate_3_colorable_graph,
	generate_3_colorable_witness_with_edge_count,
	generate_corrupted_witness,
	make_triangle,
	witness_graph,
)

SEED = 10182026
# experiment_dir = 

def main(experiment_dir: Path):
	n = 20
	m = 100
	b = 10
	rounds = 10
	report = {}
	
	valid_witness = generate_3_colorable_witness_with_edge_count(
		n, m, seed=SEED)
	valid_graph, valid_coloring = color_separated(valid_witness)

	# base_graph, base_coloring = generate_3_colorable_graph(
	# 	m - b, 0.125, seed=SEED)
	# base_witness = witness_graph(base_graph, base_coloring)
	# corrupted_witness = generate_corrupted_witness(base_witness, b/m)
	# corrupted_graph, corrupted_color = color_separated(corrupted_witness)

	draw_colored_graph(
		valid_graph, valid_coloring, "valid", 
		save_path=experiment_dir / "valid.png", show=False)
	# draw_colored_graph(
	# 	*color_separated(corrupted_witness), "corrupted", 
	# 	save_path=experiment_dir / "corrupted.png", show=False)

	transcript = run_session(valid_graph, rounds, valid_witness)
	report["valid"] = {
		"m": m,
		"b": b,
		"rounds": rounds,
		"transcript": transcript,
		# graph
	}

	# transcript = run_session(corrupted_graph, rounds, corrupted_witness)
	# report["corrupted"] = {
	# 	"m": m,
	# 	"b": b,
	# 	"rounds": rounds,
	# 	"transcript": transcript,
	# 	# graph
	# }

	with open(experiment_dir / "report.json", 'w') as file:
		json.dump(report, file, indent=2)

	

if __name__ == "__main__":
	main(Path(__file__).resolve().parent)