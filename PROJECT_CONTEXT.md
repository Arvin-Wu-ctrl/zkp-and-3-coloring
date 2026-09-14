# ZKP 3-Coloring Project Context

## Goal
Build an educational implementation of the zero-knowledge
proof protocol for graph 3-coloring.

The project should be understandable to undergraduate students
and useful as a GitHub/transfer application project.

## Current protocol

1. Prover has a valid 3-coloring.
2. Prover randomly permutes the color labels.
3. For every vertex, Prover creates a commitment using:
   SHA-256(color || nonce)
4. Verifier randomly selects an edge.
5. Prover opens the commitments for the two endpoints.
6. Verifier checks:
   - commitments match
   - endpoint colors are different
7. Repeat for multiple rounds.

## Current implementation

Graphs:
- Stored as JSON
- Loaded into NetworkX graphs
- triangle.json
- k4.json

Current tasks:
- load_graph(filepath) in src/graphs.py
- validate a supplied coloring

## Experimental goal

Compare empirical cheating-detection probability with the
theoretical probability.

Stop an experiment as soon as an invalid same-color edge
is discovered.

## Design decisions

- Python
- NetworkX
- SHA-256 commitments
- Random nonce for each commitment
- The underlying valid coloring does not need to change.
- Color labels can be randomly permuted eacpip install openaih round.

## Coding philosophy

Keep implementation simple and readable.
Do not overengineer.
Explain cryptographic and graph-theoretic reasoning when
suggesting code.