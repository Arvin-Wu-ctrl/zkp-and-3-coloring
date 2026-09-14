The structure of the [procedure](#procedure) is best understood knowing what it is trying to achieve, therefore it is preceeded by an explanation of the motivations.

# Motivations of a Zero-Knowledge Proof

The zero knowledge proof (ZKP) process in this project is an interactive process that proves a certain statement to be true while not revealing any information that was not already publicly available in the beginning.

A ZKP is done between 2 parties: a prover and a verifier, where the prover attempts to convince the verifier that some statement is true.



## Proof

A proof aim to convince the verifier that some statement is true, so the procedure below should be convincing, given that the statement is true.

A simple prove would involve following a line of reasoning starting from the assumptions (axioms), through a sequence of evident steps, and finally arriving at the statement to be proven.

This style of a proof is insufficient in certain context, where a zero-knowledge proof is needed.

## Zero Knowledge

There are times where the prover do not want to reveal how exactly the dots are connected.

An example may be an inventor seeking investment on their invention. The inventor wants to prove to the potential investors that the item works, while not giving out how exactly is the item made, so that it cannot be stolen from them. 

There are also times when zero-knowledge-ness protects the interest of both the prover and the verifier. Like in the context of authentication, the verifier wants to distinguish a client from other malicious parties pretending to be the client. The only difference between the real and the fake ones is that the real client holds some secret. If that secret is leaked, any malicious third party can copy the secret and pretend to be the original, and the verifier cannot tell the difference.

> The secret being kept is referred to as the *witness*[^1]

## Confidence (Soundness)

With the requirement of zero knowledge, it will no longer be acceptable to just show every steps of a proof.

The [procedure](#procedure) uses a different method. Instead of promising an explanation of why the statement is true (which inevitably reveal information), the procedure promises that if the statement is false, the verifier would be able to catch the mistake.

# Graph 3-Coloring Problem

The particular statement proved by the following [procedure](#procedure) is about the 3-colorability of a graph.

> A *graph* consists of unique *nodes* connected by *edges*

> Graphically, nodes are represented by dots, and edges are represented by the lines connecting the dots.

> An edge always connect to exactly 2 different nodes, so choosing an edge automatically produce 2 chosen nodes.

In the problem of graph 3-colorability, each node is assigned one of three colors. The question is whether there is a configuration of colors such that no two nodes connected by an edge have the same color (or that every pair of connected nodes have different colors). A configuration of this kind is called *valid*.


- Fact 1: If a valid 3-coloring is known, permuting the 3 colors still gives rise to a valid 3-coloring. I.e. Coloring all red vertices blue and coloring all blue vertices red gives a valid 3-coloring.
  
  - That also means that, by knowing 1 valid coloring, you can easily produce 5 more different, but nonetheless valid colorings.

- Fact 2: If a coloring is not valid, then there must be at least one pair of connected nodes with the same color[^1].

# Procedure

This section will go over each step of the procedure and explain why it is necessary for attain the goals of a zero-knowledge proof

To clarify the setup, we have 2 parties involved in the basic proof

- A *prover* who has a valid 3-coloring of the graph

- A *verifier* who wants to confidently determine if the prover truly has a valid 3-coloring

The explanation largely derive from videos on YouTube by Numberphile[^2] and Polylog[^3].

## Color Permutation

The prover permutes the 3 color labels to obtain a new coloring of the same graph.

- Note that the new coloring is also [guaranteed](#graph-3-coloring-problem) to be valid

- This is done so that the colors obtained from one round cannot be compared to colors from another round to get new knowledge of the hidden coloring. (see [Confidence](#confidence) below for reason for doing multiple rounds, and [Why is it Zero-Knowledge](#why-is-it-zero-knowledge) for why this is necessary)

## Commitment

The prover commit the color of every nodes.

After committing…

- The colors cannot be changed.

- The verifier cannot see any of the color just yet.

- In this project, commitments are made using SHA-256 together with a random nonce. For each node, the prover hashes the color with a random nonce, for instance:

`SHA256(color || nonce)`

When an edge is opened, the prover reveals the color and nonce for those two nodes, and the verifier hashes them again to check that they match the original commitments.

> The commitment is done via a [commitment scheme](https://en.wikipedia.org/wiki/Commitment_scheme), which guarantees the aforementioned properties without relying on any authority figures.

## Choose & Open Edge

The verifier choose an edge to be tested (which is the same as choosing two connected nodes).

- This step must be done after the commitment because otherwise the prover can change the colors to always pass the test.

- The edge should also be chosen randomly so that there are no ways that the prover can guess the chosen edge and fake a test.

## Open Edge

The chosen edge is then revealed by the prover, letting the verifier see the two colors and nonces.

## Verify Edge

The verifier check if the colors are the same.

- If the colors are the same, then the prover definitely does not have a valid coloring. The procedure can be terminated.

- If the colors are different, then the prover may have a valid coloring, or they may not have it and have just gotten lucky that the verifier did not choose the edge with the same color
  
  - If a coloring is not valid, then there must be at least one pair of connected nodes with the same color.

## Confidence

In the case that the verifier see 2 different colors (i.e. did not catch the prover lying), the verifier would be a little bit more confident in the proof, since there is a chance of failure, but it did not happen.

The verifier would not be very convinced, however, since there may only be a small chance that they have chosen the problematic edges even if they exist, especially in massive graphs with millions of edges.

The solution to this problem is to repeat the procedure. With each repeated round, the verifier gets a little bit more confident. This can be repeated however many times to get as close as 100% certain as one would want.

100% certainty is not attainable with this proof, however one can get to 90%, 99%, 99.99%, 99.9999%, 99.99999999%, … if desired.

## Why Is It Zero-Knowledge

Although the verifier now knows the colors of two nodes, they still gain no new information. This is because valid graph with its colors switched is still valid, but produces a different pair of colors. So the exact colors do not matter, only how they are connected to each other. The open edge reveals that the colors are different, but this would be true of any valid graph, so no new knowledge is obtained by the verifier.

# References

[^1]: Vipul Goyal. (2018). "Lecture 21: Zero-Knowledge Proofs III." Carnegie Mellon University School of Computer Science. [www.cs.cmu.edu/~goyal/s18/15503/scribe_notes/lecture23.pdf](https://www.cs.cmu.edu/~goyal/s18/15503/scribe_notes/lecture23.pdf)

[^2]: Numberphile, Avi Wigderson. (2021). "Zero Knowledge Proof (with Avi Wigderson) - Numberphile" video. YouTube.

[^3]: Polylog. (2025). "
I can prove I’ve solved this Sudoku without revealing it" video. YouTube.
