# Zero-Knowledge Proofs and 3-Coloring

A student research project exploring how a prover can convince a verifier that a graph has a valid 3-coloring without sharing the whole coloring.

For the background and a step-by-step explanation of the protocol, see [docs/protocol-walkthrough.md](docs/protocol-walkthrough.md).

## Research Question

How closely does the actual acceptance rate follow the theoretical prediction when we change the number of rounds and the fraction of bad edges?

## Research Method

The experiments are based on a Python simulation.

The idea is to compare honest and invalid colorings across different rounds. Each condition would be tested through several trials, and the results will be compared with the theoretical probability.

## Mathematical Background

For an undirected graph $G=(V,E)$, a valid 3-coloring gives each vertex a color from $\{0,1,2\}$, and every edge must connect two different colors.

- For a valid 3-coloring is known, permuting the three colors still gives a valid 3-coloring.
- If a coloring is not valid, then there must be at least one pair of connected nodes with the same color.

Let $m=|E|$, and $b$ be the number of **bad edges**, where both ends have the same color. For a fixed coloring, we have:

$$
P(\text{accept after }r\text{ rounds})
=\left(1-\frac{b}{m}\right)^r.
$$

Therefore, as we repeat the procedure, an invalid coloring is less likely to pass. For an honest coloring, since $b=0$, every round passes.

## Protocol

In each round:

1. The prover permutes the three color labels of the same graph.
2. The prover commits the color of every node. In this project, commitments are using SHA-256 with a random 128-bit nonce: `SHA256(color || nonce)`. The resulting hashes are public.
3. The verifier chooses an edge to be tested.
4. The prover reveals the color and nonce for each vertex of the selected edge.
5. The verifier recomputes the hashes to verify that they are equal to the commitments and that the two colors are different.

The session ends as soon as a check fails.

### The edge must be chosen after the commitment, because otherwise the prover could change the colors to always pass the test. It should also be chosen randomly so that the prover cannot predict which edge will be checked.

### The color permutation is done so that colors obtained from one round cannot be compared directly to colors from another round to learn the hidden coloring. For a valid coloring, the opened edge shows two different colors, but that would be true of any valid pairs, so the labels used in the very round don't matter.

### This is not intended to be a production cryptographic system or a formal security proof.

## Graph Generation

Since whether an arbitrary graph is 3-colorable is NP-complete, this project generates graphs with colorings to simulate the proof process.

`generate_valid_graph()` returns a connected graph with an exact number of edges and a valid coloring.

`generate_invalid_graph()` allows us to choose exactly how many edges are bad for the returned coloring.

Main steps:

### 1. Sample the colors

We start from a triangle. While adding nodes, the remaining colors are sampled randomly, with enough capacity for the requested good and bad edges.

For color-group sizes $x+y+z=n$, each feasible triple gets weight:

$$
w(x,y,z)
=\binom{n-3}{x-1}
 \binom{n-x-2}{y-1}.
$$

This represents the number of ways the remaining vertices can be assigned to those groups. So we can keep the original random-coloring distribution, conditioned on having enough edge capacity.

The capacity checks:

$$
xy+xz+yz\ge m-b,
\qquad
\binom{x}{2}+\binom{y}{2}+\binom{z}{2}\ge b.
$$

The valid capacity reaches its maximum of $\lfloor n^2/3\rfloor$ when the groups are as balanced as possible. With weighted sampling, the balance between color groups is less of a concern.

### 2. Build a connected backbone

Start with a triangle and then connect each new vertex to an earlier vertex with a different color.

This gives a connected graph with $n$ edges.

### 3. Sample the remaining edges

Possible edges are represented by integer IDs. We sample IDs without replacement and turn them into endpoint pairs, rather than building a list of every possible edge.

Good edges come from pairs of different color groups. Bad edges come from pairs within the same group.

This construction requires $n\ge3$ and $m-b\ge n$. Requests that cannot fit the construction raise `ValueError`. The method does not sample uniformly from all connected graphs.

Using the same seed reproduces the graph and coloring. Passing the same `coloring` keeps every vertex's color fixed across experiments.
