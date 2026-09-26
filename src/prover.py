import networkx as nx

class Prover:

    def __init__(
            self, graph: nx.Graph, witness: nx.Graph = None,
            search_budget: int = 10, seed = 0
        ):
        self._graph = graph
        self._witness = witness
        self._seed = seed

        valid = False
        if witness is not None:
            valid = self._check_coloring()
        if not valid:
            self._solve_three_color(search_budget)
    
        raise NotImplementedError


    def commit_round(self) -> nx.Graph:
        """Commit a color permutation of the witness, along with nonce.

        Return a graph of the hash values.
        """
        raise NotImplementedError


    def send_key(self, edge: tuple) -> int:
        """Send the key to unlock the given edge."""
        raise NotImplementedError


    def _check_coloring(self):
        raise NotImplementedError


    def _solve_three_color(self, search_budget: int):
        raise NotImplementedError