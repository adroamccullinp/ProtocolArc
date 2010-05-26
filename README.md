<div align="center">

# ProtocolArc

A contract lab for agent protocol envelopes. Describe an MCP or A2A message shape as a versioned contract, validate real envelopes against it, and classify what changes between revisions as compatible, forward, or breaking.

<img src="docs/assets/banner.svg" alt="ProtocolArc over a revision track marking 1.0.0, 1.1.0, and a breaking jump to 2.0.0" width="100%"/>

`Python 3` standard library · optional `.NET 9` runtime · deterministic output

</div>

## What it is for

Agent systems pass structured envelopes between tools and peers: MCP tool calls, A2A task sends, and similar JSON-RPC shaped messages. When the shape of those messages changes, older clients can break in ways that are hard to see until traffic fails. ProtocolArc turns the envelope shape into an explicit, versioned contract so that:

- an envelope can be checked against the contract it claims to satisfy,
- two revisions of the same contract can be compared to see whether the change is safe, and
- a whole set of envelopes and contracts can be cross-checked into one matrix report.

A contract failure and a contract change are treated as different things. A malformed document raises a structural error. A document that parses but does not satisfy a contract produces ordered findings with severities, never an exception.

## The compatibility model

`diff` compares two revisions of the same contract and reports the worst outcome across all field-level changes. One breaking change makes the whole diff breaking.

