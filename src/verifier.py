import random

import networkx as nx

from src.commitments import check_opening


class Verifier:

    def __init__(self, graph, seed=None):
        self._graph = graph
        self._seed = seed
        self._random = random.SystemRandom() if seed is None else random.Random(seed)
        self._pending_commitments = None
        self._pending_edge = None


    def choose_edge(self, commitment: nx.Graph) -> tuple:
        """Returns the edge to be opened."""
        edges = list(commitment.edges())
        if not edges:
            raise ValueError("No edges available to open.")

        self._pending_commitments = commitment
        self._pending_edge = self._random.choice(edges)
        return self._pending_edge


    def verify_edge(self, key: dict) -> bool:
        """Open and verify the edge.

        Return True for a valid edge, False for an invalid edge.

        The session should be terminated when an invalid edge is found."""
        if self._pending_commitments is None:
            raise ValueError("No commitment round has been selected yet.")

        edge = key.get("edge", self._pending_edge)
        openings = key.get("openings", {})
        u, v = edge

        if u not in openings or v not in openings:
            return False

        opening_u = openings[u]
        opening_v = openings[v]

        color_u = opening_u["color"]
        color_v = opening_v["color"]
        nonce_u = opening_u["nonce"]
        nonce_v = opening_v["nonce"]

        if color_u == color_v:
            return False

        if not check_opening(self._pending_commitments.nodes[u]["commitment"], color_u, nonce_u):
            return False
        if not check_opening(self._pending_commitments.nodes[v]["commitment"], color_v, nonce_v):
            return False

        return True