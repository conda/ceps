<table>
<tr><td> Title </td><td> Environment yaml specification </td>
<tr><td> Status </td><td> Draft </td></tr>
<!-- <tr><td> Status </td><td> Draft | Proposed | Accepted | Rejected | Deferred | Implemented </td></tr> -->
<tr><td> Author(s) </td><td> Eric Dill &lt;mail@ericdill.dev&gt;</td></tr>
<tr><td> Created </td><td> March 28, 2023</td></tr>
<tr><td> Updated </td><td> NA </td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
</table>

## Abstract

This CEP aims to formalize the current state of the environment.yaml specification.
It notably does not attempt to address any proposed changes to the specification.
That is currently being discussed elsewhere.

## Motivation

There are a number of existing projects that can accept the env.yml format as input.
Each project that wants to use the env.yml spec has to implement their own parser.
This is a problem because it means that there are multiple implementations of the same specification.
This makes it difficult to evolve the specification because right now it is implicitly defined as however `conda-env` handles the env.yml file.
This CEP aims to formalize the specification so that it can be used as a reference for other projects, including `conda-env`.
There are [existing docs](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) that defines how a user should create an environment.yml file.
From what I can tell this is the only formal specification for this file.
It is the objective of this CEP to formalize the existing specification so that other projects can standardize on what they expect as input.
Evolutions to this spec are expected and welcome, but are out of the scope for the initial proposal.

Issues found in the wild that result from env.yaml not having a published spec:
- [vscode issue #280](https://github.com/microsoft/vscode-python/issues/280)

## Specification

There are four keys that the conda env spec expects:

`name`, `str`, specifying the name of the conda env that will be created.

`channels`, `list`, specifying the channels that the solver should find and pull packages from

`dependencies`, `list`, specifying the top-level dependencies that the solver should start with
- `dependencies` also has an optional dict with the `pip` key that expects a `list` as its value. This key tells the solver to also include the listed dependencies to pull from pypi

`prefix`, `str`, the full path to the environment. It's not clear to me how `name` and `prefix` interact.

`variables`, `dict`, {`str`: `str`} format of environment variables to set/unset when the environment is activated/deactivated.

jsonschema version of the current spec:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "prefix": {"type": "string"},
    "channels": {
      "type": "array",
      "items": {"type": "string"}
    },
    "dependencies": {
      "type": "array",
      "items": {
        "anyOf": [
          {"type": "string"},
          {"$ref": "#/definitions/pip"}
        ]
      }
    },
    "variables": {
      "type": "object",
      "additionalProperties": {"type": "string"}
    }
  },
  "definitions": {
    "pip": {
        "type": "object",
        "additionalProperties": {
            "type": "array",
            "required": ["pip"],
            "properties": {
                "pip": {"type": "array"}
            }
        }
    }
  }
}
```

## Other sections

Other relevant sections of the proposal.  Common sections include:

    * Specification -- The technical details of the proposed change.
    * Motivation -- Why the proposed change is needed.
    * Rationale -- Why particular decisions were made in the proposal.
    * Backwards Compatibility -- Will the proposed change break existing
      packages or workflows.
    * Alternatives -- Any alternatives considered during the design.
    * Sample Implementation -- Links to prototype or a sample implementation of
      the proposed change.
    * FAQ -- Frequently asked questions (and answers to them).
    * Resolution -- A short summary of the decision made by the community.
    * Reference -- Any references used in the design of the CEP.

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
