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

| Verdict | Meaning |
| :------ | :------ |
| `compatible` | The new revision accepts everything the old one did. |
| `forward` | Old consumers keep working; new fields are optional, types widened, constraints relaxed. |
| `breaking` | A change can reject previously valid envelopes: a required field added or removed, a type narrowed, an enum restricted, or an optional field tightened to required. |

<div align="center">
<img src="docs/assets/pipeline.svg" alt="Pipeline: parse, validate, diff, report, with a legend for the compatible, forward, and breaking verdicts" width="88%"/>
</div>

## Data model

A contract names a protocol, carries a semantic `revision`, and lists ordered `FieldSpec` entries. Each field has a dotted path (`params.name`), one or more accepted JSON types, a `required` flag, and an optional `enum`. A `strict` contract also flags top-level keys it does not declare.

```json
{
  "name": "mcp.tool_call",
  "revision": "1.0.0",
  "kind": "mcp",
  "title": "MCP Tool Call",
  "strict": false,
  "fields": [
    { "name": "jsonrpc", "type": "string", "enum": ["2.0"] },
    { "name": "id", "type": ["string", "integer"] },
    { "name": "method", "type": "string", "enum": ["tools/call"] },
    { "name": "params.name", "type": "string" },
    { "name": "params.arguments", "type": "object", "required": false }
  ]
}
```

An envelope declares the `contract` it targets, an optional `revision`, and its `data` body. The bundled fixtures cover both an MCP contract that evolves from `1.0.0` to `2.0.0` and a strict A2A `task_send` contract.

## Commands

```
python -m protocolarc <validate|diff|matrix|report|describe> ...
```

Exit codes are meaningful: `0` success, `1` validation errors present, `2` breaking compatibility detected by `diff`, `3` a usage or input error.

`validate` checks envelopes against one contract:

```bash
python -m protocolarc validate \
  examples/contracts/mcp_tool_call_1.0.0.json \
  examples/fixtures/mcp_calls.jsonl
```

```
[PASS] mcp.tool_call@1.0.0 <- mcp_calls.jsonl:1
[FAIL] mcp.tool_call@1.0.0 <- mcp_calls.jsonl:3
    ERROR   field.enum             method: value 'tools/list' not in {'tools/call'}
```

`diff` compares two revisions and classifies the change:

```bash
python -m protocolarc diff \
  examples/contracts/mcp_tool_call_1.0.0.json \
  examples/contracts/mcp_tool_call_2.0.0.json
```

```
mcp.tool_call: 1.0.0 -> 2.0.0
compatibility: BREAKING
  breaking    field.type.narrowed        id: string|integer -> string
  breaking    field.required.tightened   params.arguments: optional -> required
  forward     field.added.optional       params.timeout_ms: added integer
```

`matrix` cross-validates a set of envelopes against a set of contracts (files or directories):

```bash
python -m protocolarc matrix \
  --contracts examples/contracts \
  --envelopes examples/fixtures/mcp_calls.jsonl examples/fixtures/a2a_tasks.json
```

`report` renders the same matrix as `markdown` (default), `json`, or `text`, optionally to a file:

```bash
python -m protocolarc report \
  --contracts examples/contracts \
  --envelopes examples/fixtures/mcp_calls.jsonl \
  --format markdown --out report.md
```

`describe` prints a contract's field table:

```bash
python -m protocolarc describe examples/contracts/a2a_task_send_1.0.0.json
```

## The .NET runtime

`runtime/` holds `ProtocolArc.Runtime`, a native validator that mirrors the Python `validate` logic so a contract checked by either component yields the same findings. It is meant for hot paths where envelopes stream through a gateway.

```bash
cd runtime
dotnet run -- selfcheck
dotnet run -- validate ../examples/contracts/mcp_tool_call_1.0.0.json ../examples/fixtures/mcp_calls.jsonl --json
dotnet run -- describe ../examples/contracts/a2a_task_send_1.0.0.json
```

`selfcheck` builds a contract and two envelopes in memory and asserts the expected pass and fail split, so CI can confirm the runtime works without external fixtures.

## How validation reads an envelope

For each contract field, the validator resolves the dotted path in the envelope body and applies rules in a fixed order:

- `contract.match`: the envelope must target the contract being checked (error).
- `revision.hint`: a declared revision that differs from the contract is a warning, since it may be an older client talking to a newer contract.
- `field.required`: a missing required field is an error.
- `field.type`: a present field must match one of the accepted JSON types.
- `field.enum`: a scalar value must be within the declared enum.
- `field.unknown`: under a strict contract, an undeclared top-level key is a warning.

Findings are sorted by severity, then field, then rule, so the output is stable across runs.

## Repository layout

```
protocolarc/
├── protocolarc/            Python package (stdlib only)
│   ├── __main__.py         python -m protocolarc entry point
│   ├── cli.py              validate / diff / matrix / report / describe
│   ├── model.py            Contract, Envelope, FieldSpec
│   ├── loader.py           parse contract and envelope documents
│   ├── validate.py         envelope validation, ordered findings
│   ├── diff.py             revision comparison and compatibility classes
│   ├── matrix.py           cross-product matrix and revision chains
│   └── report.py           markdown / json / text renderers
├── runtime/                ProtocolArc.Runtime (.NET 9), mirrors the validator
├── examples/
│   ├── contracts/          mcp.tool_call 1.0.0 / 1.1.0 / 2.0.0, a2a.task_send
│   └── fixtures/           mcp_calls.jsonl, a2a_tasks.json
└── docs/assets/            banner and pipeline diagrams
```

## Determinism

Field ordering is preserved from the contract, and every derived collection is sorted before rendering, so repeated runs over the same inputs produce byte-identical output. Reports come in `json`, `markdown`, and `text`, and each is a pure function of the matrix it renders.

## Extending it

Add a validation rule by appending a `Finding` inside `validate_envelope` with a rule name, field, severity, and message; the sort key keeps output stable. Add a compatibility rule by extending the `CHANGE_IMPACT` map in `diff.py` and emitting the matching `Change`. Keep the .NET runtime in step with any validation change so both components agree.

# draft note 34
