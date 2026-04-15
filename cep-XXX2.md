# CEP XXXX - Optional dependency groups

<table>
<tr><td> Title </td><td> Optional dependency groups </td>
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

This CEP proposes the introduction of optional dependency groups in conda packaging. Optional dependency groups (or "extras") allow packagers to specify additional requirements behind a named set. This is implemented by adding a new repodata record field, `extras`, as a dictionary that maps group names to a list of dependencies. Extras can be selected via its corresponding `MatchSpec` keyword matching one or more group names.

## Motivation

Optional dependency groups are popular in Python packaging, initially introduced as part of `setuptools` via `extras_require`, and formalized years later in PEP 508.

The need in conda packaging can be also identified by analyzing certain patterns in the ecosystem:

- The `{package}-with-{group-name}` pattern can be found in projects like `ray` or `arrow`.
- The `{package}` + `{package}-base` pattern was introduced for `matplotlib`.
- Some projects choose to add all extras in the base package to avoid the complexity of having to add more outputs to their recipe.

Instead of overloading the repodata documents with more package names (which causes additional solver strain and works against optimization efforts like sharded repodata), authors propose to extend the repodata records with the additional dependency metadata, thus reducing unnecessary duplication.

## Rationale

The chosen keyword in the and `MatchSpecs` is  `extras` given its popularity in Python packaging.

## Specification

The `info/index.json` dictionary of each conda artifact MUST allow a new field, `extra-depends`, the value of which MUST be a dictionary that maps the group names (expressed as a string that MUST match the regex `[a-z0-9_.-+]{1,64}`) to a list of `MatchSpec` strings encoding the optional dependencies. Since this is backwards incompatible behavior-wise, the `schema_version` value MUST be bumped to `3`.

The `extras` field MUST also be exposed in recipe formats v1 and above, under the `requirements.extras` section (sibling to `build`, `host`, `run`, etc), that renders to the same schema (`dict[str, list[MatchSpec]]`).

This new field must be selectable by `MatchSpec` syntax using the `extras` keyword inside square brackets, the value of which must be a string or a list of string targeting group names. If an optional dependency group is matched by the `extras` field in `MatchSpec`, its list of dependencies MUST be unioned with the regular `depends` field and resolved accordingly.

## Examples

A repodata record with `extra-depends`:

```js
{
  // ...,
  "packages.conda": {
    // ...,
    "example-1.0-0.conda": {
      // ...,
      "depends": [
        "main-dependency"
      ]
      "extra-depends": {
        "group-name": [
          "extra-dependency>=2",
          "another-dependency>=1"
        ]
      }
    }
  }
}
```

A `MatchSpec` query targeting the above record:

```shell
example[extras="group-name"]
```

A recipe defining an output named `example` with a `group-name` extras:

```yaml
# ...
requirements:
  ...
  run:
    - main-dependency
  extras:
    group-name:
      - extra-dependency >=2
      - another-dependency >=1
# ...
```

## Rejected ideas

PEP 735 "optional dependency groups" are not covered in this CEP. Those are not part of the installation metadata, but this CEP proposes groups that are indeed part of it.

## References

- https://packaging.python.org/en/latest/specifications/dependency-specifiers/#extras
- [conda/conda#1696: Optional dependencies for conda packages](https://github.com/conda/conda/issues/1696), [conda/conda#7502: Optional groups of dependencies](https://github.com/conda/conda/issues/7502)

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
