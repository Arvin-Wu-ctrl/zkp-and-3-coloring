"""Rebuild the 50-node examples: python -m tools.generate_graph_examples.

All five cases share vertex colors and drawing positions. Bad edges are sampled
from all same-color pairs; there is no clustering constraint. Graph JSON files
contain no private colors; matching *_coloring.json files hold the witnesses.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import networkx as nx

from src.graphs import (
    generate_invalid_graph, generate_valid_graph, load_graph,
    save_graph_example,
)


def main():
    directory = Path(__file__).resolve().parents[1] / "examples"
    figures = directory / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    # Sample once under the strictest good-edge capacity used by these cases.
    # Reusing it avoids a different conditional coloring in each experiment.
    _, coloring = generate_valid_graph(50, 750, seed=42)
    cases = []
    for edges, bad in [(75, 0), (300, 0), (750, 0), (300, 5), (300, 50)]:
        if bad:
            graph, colors = generate_invalid_graph(
                50, edges, bad, seed=42, coloring=coloring,
            )
        else:
            graph, colors = generate_valid_graph(50, edges, seed=42, coloring=coloring)
        assert colors == coloring
        assert nx.is_connected(graph)
        assert graph.number_of_edges() == edges
        assert sum(colors[u] == colors[v] for u, v in graph.edges) == bad
        kind = "invalid" if bad else "valid"
        name = f"{kind}_n50_m{edges}_bad{bad}"
        graph_path, _ = save_graph_example(graph, colors, name, directory)
        assert nx.utils.graphs_equal(load_graph(graph_path), graph)
        cases.append((name, graph, edges, bad))

    # A circle preserves readable node spacing even for disconnected cases.
    positions = nx.circular_layout(cases[0][1])
    palette = ["#118a80", "#7661bc", "#c58b20"]
    handles = [Line2D([], [], marker="o", linestyle="", color=color,
                      label=f"Color {i} ({coloring.count(i)} nodes)")
               for i, color in enumerate(palette)]
    handles.append(Line2D([], [], color="#d62728", label="Bad edge (same color)"))

    def draw(axis, graph, edges, bad):
        good_edges = [(u, v) for u, v in graph.edges if coloring[u] != coloring[v]]
        bad_edges = [(u, v) for u, v in graph.edges if coloring[u] == coloring[v]]
        nx.draw_networkx_edges(graph, positions, edgelist=good_edges, ax=axis,
                               edge_color="#64748b", alpha=.18, width=.65)
        nx.draw_networkx_edges(graph, positions, edgelist=bad_edges, ax=axis,
                               edge_color="#d62728", alpha=.85, width=1.6)
        nx.draw_networkx_nodes(graph, positions, ax=axis, node_size=110,
                               node_color=[palette[c] for c in coloring],
                               edgecolors="white", linewidths=.6)
        axis.set_title(f"50 nodes | {edges} edges | {bad} bad edges")
        axis.set_axis_off()

    overview, axes = plt.subplots(2, 3, figsize=(18, 11))
    for axis, (name, graph, edges, bad) in zip(axes.flat, cases):
        draw(axis, graph, edges, bad)
        figure, single_axis = plt.subplots(figsize=(10, 8))
        draw(single_axis, graph, edges, bad)
        figure.legend(handles=handles, loc="lower center", ncol=2, frameon=False)
        figure.tight_layout(rect=(0, .08, 1, 1))
        figure.savefig(figures / f"{name}.png", dpi=180)
        plt.close(figure)
        print(f"{name}: verified; colors unchanged")
    axes.flat[-1].set_axis_off()
    axes.flat[-1].legend(handles=handles, loc="center", frameon=False, fontsize=12)
    overview.suptitle("Fixed coloring and positions across all five examples | seed 42", fontsize=17)
    overview.tight_layout(rect=(0, 0, 1, .95))
    overview.savefig(figures / "n50_exact_edges_overview.png", dpi=160)
    plt.close(overview)


if __name__ == "__main__":
    main()
