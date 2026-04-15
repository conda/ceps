# CEP XXXX - Conditional dependencies

<table>
<tr><td> Title </td><td> Conditional dependencies </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td>
  Wolf Vollprecht &lt;w.vollprecht@gmail.com&gt;,
  Bas Zalmstra &lt;bas@prefix.dev&gt;,
  Jaime Rodríguez-Guerra &lt;jaime.rogue@gmail.com&gt;
</td></tr>
<tr><td> Created </td><td> Feb 5, 2025</td></tr>
<tr><td> Updated </td><td> Mar 9, 2026</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/111 </td></tr>
<tr><td> Implementation </td><td> TBD </td></tr>
<tr><td> Requires </td><td> https://github.com/conda/ceps/pull/146 </td></tr>
</table>

## Abstract

This CEP proposes the introduction of conditional dependencies in the conda ecosystem. The work comprises two changes: the addition of a new keyword argument, `when`, to the `MatchSpec` syntax, and its evaluation at solve time. The value of the `when` argument is always a logical expression of one or more MatchSpec queries targeting the solver context.

## Motivation

Conditional dependencies are often requested in the conda ecosystem. After all, an equivalent feature exist in Python packaging in the form of "environment markers" (introduced in [PEP 508](https://peps.python.org/pep-0508/)), so it's a reasonable expectation. There are even traces of planned support of it in `conda.models.match_spec` (see commit [`ab33436`](https://github.com/conda/conda/pull/7606/changes/ab33436591cd2f8ce9c792a50a412d1d02c75504)) in the context of ["pip interoperability"](https://github.com/conda/conda/issues/7053).

The feature never landed though, and its absence in the conda ecosystem has forced packagers to (inefficiently) translate this expressivity into a set of different package variants which only differ in their dependency metadata. For example, consider the following runtime requirements of a pure Python package:

```toml
# ...
requires_python = ">=3.8"
requirements = [
  "typing-extensions; python_version < '3.9'",
  "pywin32; sys_platform == 'win32'"
  "requests",
]
```

They can only be converted into conda packages by making a potentially `noarch: python` package (because it's pure Python) a non-noarch package distributed as as many as 25 platforms (five supported Python versions, times five platforms). This way, the conditional dependency is resolved (in a way) at build time by rendering the dependencies into the granular artifacts. For example, the `typing-extensions` dependency would only be present in the variants built for Python 3.8, and we would only find `pywin32` in the packages published to the `win-*` subdirs.

The adoption of conditional dependencies in conda would allow packagers to express the same complexity in a single `noarch: python` package, because these conditions would be evaluated at "solve time". Providing these capabilities requires new `MatchSpec` syntax and a bump in the repodata version to allow the new syntax in the `depends` field.

## Rationale

The syntax chosen utilizes the same key-value syntax already present in the brackets form of the `MatchSpec` language. This makes it easier to implement and less surprising to novel users. The `when` keyword is chosen to avoid confusion with the `if`/`then`/`else` syntax in [CEP 13](./cep-0013.md) `recipe.yaml` files.

Classic `MatchSpec` queries have traditionally matched fields present in candidate package records. For example, `python>=3.10` would match records with package name `python` and version greater or equal than `3.10`. The `when` field is a bit different in that sense, since it doesn't target a `when` field in the target records. Instead, its value is a condition that will match a context comprised of (potentially) other records. This is a deviation for the `MatchSpec` design but we still feel that the ergonomics offered by this syntax are worth the extra complexity.

## Specification

This CEP extends [CEP 29](./cep-0029.md) with a new keyword, `when`.

### Syntax

A conditional dependency is defined as a `MatchSpec` string that features a `when` keyword, the value of which MUST be a string that encodes a logical expression of one or more `MatchSpec` queries. The logical expression follows a Python-like syntax: `MatchSpec` strings MAY be joined with operators `and` (logical AND) and `or` (logical OR), and grouped within parentheses `()` for precedence overrides.

The inner `MatchSpec` queries inside `when` MUST be expressed in their square brackets syntax, with the exception of simple `name` and `version` queries that MAY be expressed as `{name}{operator}{version}` (no space separators). These inner `MatchSpec` queries MUST NOT feature their own `when` field.

If necessary, the `when` value MUST be quoted to avoid parsing ambiguities.

### Evaluation

A conditional dependency MUST only be taken into account when the `when` condition evaluates to true. Otherwise, it MUST be ignored by the solver.

A condition MUST evaluate to true when the logical concatenation of the `MatchSpec` queries is truthy. Each `MatchSpec` expression would evaluate to true if:

- It matches a package record potentially present in the proposed solution.
- It matches a virtual package present in the target system.
- For `run_exports` only: it matches a field injected in the evaluation context.

### Impact in `info/*.json`

This is a backwards incompatible change. To guarantee backwards compatibility, the CEP 34 `info/index.json` `schema_version` field MUST be bumped to `3`. When present in `run_exports.json`, its `schema_version` value MUST be bumped to `2`.

## Examples

Conditional dependencies can be used in the same places a regular `MatchSpec` expression is used.

As CLI input:

```shell
$ conda create -n env-with-conditions python 'numpy>=2[when="python>=3.10"]'
```

In an input file:

```yaml
name: env-with-conditions
channels: [conda-forge]
dependencies:
- python
- numpy>=2[when="python>=3.10"]
```

```toml
[dependencies]
python = "*"
numpy = { version=">=2", when="python>=3.10" }
```

In a recipe file:

```yaml:
# ...
requirements:
  run:
    - python
    - numpy>=2[when="python>=3.10"]
```

## Backwards compatibility

Adding a new field to the `MatchSpec` keywords is a backwards incompatible change. For example, in `conda`:

```shell
$ conda create -d "python[when=__unix]"
InvalidMatchSpec: Invalid spec 'python[when=python]': Invalid spec 'python[when=python]': Cannot match on field(s): {'when'}
```

When used as part of the runtime requirements of a newly built package, the conditional dependency must be included in the `depends` field of the resulting repodata record. Since this new syntax is backwards incompatible with older clients, the resulting `repodata.json` documents (or a derivative, like the sharded forms) MUST NOT include records of packages whose `info/index.json` features a value of `schema_version` equals to or greater than 3.

## Rejected ideas

- `...; if syntax` and other backwards compatible proposal that would be inadequate because then the condition would be ignored, hence creating invalid solutions.

## References

- https://github.com/conda/conda/issues/2984
- https://github.com/conda/conda/issues/7438
- https://github.com/conda/conda/issues/7439
- https://github.com/conda/conda/issues/5699

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
