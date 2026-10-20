import random
import secrets

import networkx as nx

from src.commitments import create_commitment


class Prover:

    def __init__(
            self, graph: nx.Graph, witness: nx.Graph = None,
            search_budget: int = 10, seed = 0
        ):
        self._graph = graph.copy()
        self._witness = None if witness is None else witness.copy()
        self._seed = seed
        self._random = random.Random(seed)
        self._current_commitments = {}
        self._current_permutation = {}

        if self._witness is None:
            self._solve_three_color(search_budget)
        # elif not self._check_coloring():
        #     self._solve_three_color(search_budget)


    def _node_colors(self):
        colors = {}
        for node in self._graph.nodes:
            data = self._witness.nodes[node]
            colors[node] = data.get("color")
        return colors


    def commit_round(self) -> nx.Graph:
        """Commit a color permutation of the witness, along with nonce.

        Return a graph of the hash values.
        """
        original_colors = self._node_colors()
        permutation = self._random.sample([0, 1, 2], 3)
        self._current_permutation = {
            original: permuted for original, permuted in enumerate(permutation)
        }
        self._current_commitments = {}

        commitment_graph = nx.Graph()
        commitment_graph.add_nodes_from(self._graph.nodes)
        commitment_graph.add_edges_from(self._graph.edges)

        for node in self._graph.nodes:
            original_color = original_colors[node]
            if original_color not in (0, 1, 2):
                raise ValueError(f"Node {node!r} does not have a valid 3-coloring.")

            hidden_color = self._current_permutation[original_color]
            nonce = secrets.randbits(128)
            commitment = create_commitment(hidden_color, nonce)
            self._current_commitments[node] = {
                "color": hidden_color,
                "nonce": nonce,
                "commitment": commitment,
                "original_color": original_color,
            }
            commitment_graph.nodes[node]["commitment"] = commitment

            """Reveal only the hash, not the color or nonce."""

        return commitment_graph


    def send_key(self, edge: tuple) -> dict:
        """Send the key to unlock the given edge."""
        u, v = edge
        key = {
            "edge": (u, v),
            "openings": {
                u: {
                    "color": self._current_commitments[u]["color"],
                    "nonce": self._current_commitments[u]["nonce"],
                },
                v: {
                    "color": self._current_commitments[v]["color"],
                    "nonce": self._current_commitments[v]["nonce"],
                },
            },
        }
        return key


    def _check_coloring(self):
        colors = self._node_colors()
        for node, color in colors.items():
            if color not in (0, 1, 2):
                return False

        for u, v in self._graph.edges:
            if colors[u] == colors[v]:
                return False

        return True


    def _solve_three_color(self, search_budget: int):
        colors = {}
        order = list(self._graph.nodes())
        self._random.shuffle(order)

        def search(index):
            if index == len(order):
                return True

            node = order[index]
            for color in (0, 1, 2):
                if any(colors.get(neighbor) == color for neighbor in self._graph.neighbors(node)):
                    continue

                colors[node] = color
                if search(index + 1):
                    return True
                colors[node] = None

            return False

        if not search(0):
            raise ValueError("Could not find a valid 3-coloring within the search budget.")

        witness = nx.Graph()
        witness.add_nodes_from(self._graph.nodes)
        witness.add_edges_from(self._graph.edges)
        for node, color in colors.items():
            witness.nodes[node]["color"] = color
        self._witness = witness

        if not self._check_coloring():
            raise ValueError("Solved coloring is invalid.")