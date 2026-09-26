import networkx as nx

class Verifier:

    def __init__(self, graph, seed: int = 0):
        self._graph = graph
        self._seed = seed


    def choose_edge(self, commitment: nx.Graph) -> tuple:
        """Returns the edge to be opened."""
        raise NotImplementedError


    def verify_edge(self, key: int) -> bool:
        """Open and verify the edge.

        Return True for a valid edge, False for an invalid edge.

        The session should be terminated when an invalid edge is found."""
        raise NotImplementedError