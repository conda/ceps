# CEP ?? - Frozen environments

<table>
<tr><td> Title </td><td> Frozen environments </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Jaime Rodríguez-Guerra &lt;jaime.rogue@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> Nov 19, 2024</td></tr>
<tr><td> Updated </td><td> Nov 19, 2024</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/99 </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
</table>

## Abstract

Given a `$CONDA_PREFIX/conda-meta/frozen` marker file, tools will prevent modifications in `$CONDA_PREFIX` unless a special override flag is passed.

> The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT",
  "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as
  described in [RFC2119][RFC2119] when, and only when, they appear in all capitals, as shown here.

## Motivation

This CEP is inspired by [PEP 668][PEP-668], which defines the `EXTERNALLY-MANAGED` marker file for Python virtual environments. The conda ecosystem could benefit from a similar file for conda environments. Some examples include:

- Protecting modifications of the `base` environment in `conda` installations.
- Protecting external management of `.pixi/envs/*` environments by other tools.
- Reproducibility of the build and host environments in conda package building tools.

## Specification

- The marker file path MUST be `$CONDA_PREFIX/conda-meta/frozen`. This is case-sensitive.
- The marker file can be empty. It can optionally contain a JSON document with the schema described with a single key `message`. The value MUST be a non-empty string.
- Tools MUST respect the presence of `frozen` in the environment and error out with:
    - A message chosen by the tool, if `frozen` is empty.
    - The message included in the `message` key, if `frozen` is not empty.
    - A help message explaining how to override the check, if available.
- Tools SHOULD offer a way to override the presence of `frozen` (e.g. `--override-frozen-env`). However, tools MUST NOT enable the overrides by default.

## Example

An example `frozen` file can be:

```json
{
    "message": "This environment is running a production service.\nIt is marked as read-only and MUST not be modified."
}
```

A hypothetical tool finding this file in the environment to be modified would output something like:

```
Could not modify environment. The environment has been marked as frozen. Reason:

    This environment is running a production service.
    It is marked as read-only and MUST not be modified.

You can bypass this check by using the `--override-frozen-env-checks` flag, at your own risk.
```

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

<!-- links -->

[PEP-668]: https://peps.python.org/pep-0668/
