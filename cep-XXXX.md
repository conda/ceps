# CEP XXXX - The `MatchSpec` query language

<table>
<tr><td> Title </td><td> The <code>MatchSpec</code> query language </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td>
  Jaime Rodríguez-Guerra &lt;jaime.rogue@gmail.com&gt;,
  Cheng H. Lee &lt;clee@anaconda.com&gt;,
  Bas Zalmstra &lt;bas@prefix.dev&gt;
</td></tr>
<tr><td> Created </td><td> June 4, 2024 </td></tr>
<tr><td> Updated </td><td> January 29, 2026 </td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/82 </td></tr>
<tr><td> Implementation </td><td> https://github.com/conda/conda/blob/4.3.34/conda/resolve.py#L33, https://github.com/conda/conda/blob/25.7.0/conda/models/match_spec.py#L85, https://docs.rs/rattler_conda_types/latest/rattler_conda_types/struct.MatchSpec.html, https://github.com/mamba-org/mamba/blob/2.3.2/libmamba/src/specs/match_spec.cpp, https://github.com/openSUSE/libsolv/blob/0.7.35/src/conda.c#L567 </td></tr>
<tr><td> Requires </td><td> https://github.com/conda/ceps/pull/132, https://github.com/conda/ceps/pull/133, https://github.com/conda/ceps/pull/135 </td></tr>
</table>

## Abstract

This CEP standardizes the syntax for the `MatchSpec` query language.

## Motivation

The motivation of this CEP is merely informative. It describes the details of an existing DSL.

## Nomenclature

The `MatchSpec` query syntax is a mini-language designed to query package records from one or more conda channels. It is sometimes referred to as simply _spec_ or _conda spec_.

## Specification

`MatchSpec` strings provide a compact method to query collections of conda artifacts (e.g. in a conda channel, or in an installed environment) by matching `str` and `int` fields on package records (see [CEP PR #133's `./info/index.json`](https://github.com/conda/ceps/pull/133) and [CEP PR#135's "Package Record Metadata"](https://github.com/conda/ceps/pull/135)). Note that fields using other types, like `list[str]` (`depends`, `constrains`, etc.) cannot be matched by this syntax.

### Search vs solver `MatchSpec`

`MatchSpec` strings can be used under two different contexts:

- Search queries: To obtain all the artifacts matching the query against a collection of packages. Results MAY include more than one entry per package name.
- Solver requests: To obtain the subset of packages in an index that satisfy the request and their dependency metadata. Results MUST only include one entry per package name.

In contrast with search queries, only some `MatchSpec` fields make sense for solver requests. Most common include: `name`, `version`, `build`, `channel`.

### Syntax

The `MatchSpec` syntax can be thought of as a structured collection of _matching expressions_, each targeting a package record field. A matching expression is defined as a string that MUST follow these rules:

- For expressions targeting the `version` field, [version specifier rules](#version-matching) MUST be applied.
- For expressions targeting any other `str` field, [string matching conventions](#string-matching) MUST be used.
- For expressions targeting `int` fields, the target value MUST be converted to `str` and handled as such.

The full `MatchSpec` syntax takes this approximate form, with parentheses denoting optional fields:

```text
(channel(/subdir):(namespace):)name(version(build))([key1='value 1',key2=value2])
```

More precisely, the following rules apply:

- A `MatchSpec` string MAY exhibit two forms of expressions: positional and keyword based.
- Six positional expressions are recognized. From left to right, they can be are arranged in two groups: (`channel`, `subdir` and `namespace`) and (`name`, `version`, `build`).
  - The first group is optional. If present, it MUST be separated from the second one by a single colon character `:`. Within this group, there are four items:
    - `channel: str`. Optional
    - `subdir: str`. Optional. It requires `channel` to be defined. Must be separated from `channel` by a single forward slash, `/`.
    - A colon `:` separator, required if `channel` or `namespace` are defined.
    - `namespace: str`. Optional. This expression field MUST be parsed and ignored.
  - The second group contains three expressions. They MUST be separated by either spaces or a single `=` character. Separator types MUST NOT be mixed. See the [version expression parsing notes](#version-expression-parsing) for additional details on the interaction between the `=` symbol as a separator and as an operator. Leading and trailing spaces MUST be ignored.
    - `name: str`. Required. Empty names MUST be represented as `*`.
    - `version: str | VersionSpec`. Optional.
    - `build: str`. Optional. It requires `version` to be present.
- All keyword expressions are optional. If present, they MUST be enclosed in a single set of square brackets, after the positional expressions. The following rules apply:
  - Keyword expressions are written as key-value pairs. They MUST be built by joining the name of the target field (key) and the expression string (value) with a single `=` character.
  - The value MUST be quoted with single `'` or double `"` quotes if it contains spaces, commas, equal signs, or square brackets. Quoting rules follow [Python's string literals](https://docs.python.org/3/reference/lexical_analysis.html#strings).
  - Keyword expression pairs MUST be separated by a single comma character `,`.
  - Spaces between separators MAY be allowed and MUST be ignored.
- When both positional and keyword expressions are used, the keyword expressions override the positional values, except for `name` (its positional value MUST always win).

### Canonical representation

The canonical string representation of a `MatchSpec` expression follows these rules:

1. `name` is required and MUST be written as a positional expression. An empty name MUST be written as `*` if necessary.
2. If `version` describes an exact equality expression, it MUST be written as a positional expression, prepended by `==`. If `version` denotes fuzzy equality (e.g. `1.11.*`), it MUST be written as a positional expression with the `.*` suffix left off and prepended by `=`. Otherwise `version` MUST be included inside the key-value brackets.
3. If `version` is an exact equality expression, and `build` does not contain asterisks, `build` MUST be written as a positional expression, prepended by `=`. Otherwise, `build` MUST go inside the key-value brackets.
4. If `channel` is defined and does not contain asterisks, a `::` separator is used between `channel`
   and `name`. `channel` MAY be represented by its name or full, subdir-less URL.
5. If both `channel` and `subdir` do not contain asterisks, `subdir` is appended to
   `channel` with a `/` separator. Otherwise, `subdir` is included in the key-value brackets.
6. Key-value pairs MUST NOT use spaces between separators. Values MUST be quoted with single quotes.
7. The `namespace` MUST NOT be written.
8. Case-insensitive string fields MUST be lowercased.

### Matching conventions

#### String matching

Matching expressions that target string fields MUST be interpreted using these rules:

- If the expression begins with `^` and ends with `$`, it MUST be interpreted as a regular expression (regex). The expression matches if the regex search returns a hit; e.g. with Python: `re.search(expression, field) is not None`.
- If the expression contains an asterisk (`*`), it is considered a glob expression and MUST be interpreted as if it was a regular expression. To convert a glob expression into a regex string:
   1. Escape characters considered special in regex expressions adequately (e.g. using Python's `re.escape`).
   2. Replace escaped asterisks (`\*`) by `.*`.
   3. Wrap the resulting string with `^` and `$`.
- Otherwise, matches MUST be tested with exact, case-insensitive string equality.

For the `name` field, regex and globs SHOULD NOT be allowed for solver requests.

#### Version matching

Expressions targeting the `version` field MUST be handled with additional rules. These expressions are referred to as _version specifiers_.

A version specifier MUST consist of one or more _version clauses_, separated by logical operators that MUST follow these rules:

- `|` denotes the logical OR.
- `,` denotes the logical AND.
- `,` (AND) has higher precedence than `|` (OR).

A _version clause_ consists of a single version literal (as defined in [CEP PR #132](https://github.com/conda/ceps/pull/132)) and optionally an operator.

> For example, given a string `python>=3,<4`, the version specifier is the full expression `>=3,<4`, which consists of two clauses (`>=3`, `<4`) separated by `,` (AND). Each clause contain a version literal (`3` and `4`, respectively.)

Each version clause MUST be described by one of these types:

- [String matching](#string-matching) rules, as defined in the section above. This applies to clauses expressed as exact version literals or version literals augmented with asterisks (`*`); e.g. `1.2.3`, `1.2.3.*`, and `1.*.3`.
- Exact equality, expressed as a version literal prefixed by the double-equals string `==`, MUST be interpreted as a strict string equality test after removing the `==` prefix.
- Fuzzy equality, expressed as a version literal prefixed by one `=` symbol. After removing the leading `=` character and appending a `.*` suffix, the string MUST be interpreted with [string matching](#string-matching) rules.
- Exclusion, expressed as a version literal, or a version literal augmented with asterisks, prefixed by the string `!=`, MUST be interpreted as a negated [string matching](#string-matching) test.
- Ordered comparison, with the implied ordering described in [CEP PR #132](https://github.com/conda/ceps/pull/132):
  - Exclusive ordered comparison, expressed as a version literal prefixed by `<` or `>`, MUST be interpreted as "smaller than" and "greater than", respectively, as per their position in the version ordering scheme.
  - Inclusive ordered comparison, expressed as a version literal prefixed by one of these strings: `<=`, `>=`, MUST be interpreted as in "exclusive ordered comparison", respectively, but they will also match if their position is equivalent in the version ordering scheme.
- Semver-like comparisons, expressed as a version literal prefixed by the `~=` string, MUST be interpreted as greater or equals than the version literal while also matching a fuzzy equality test for the version literal sans its last segment (e.g. `~=0.5.3` expands to `>=0.5.3,0.5.*`). This operator is considered deprecated, and its expanded alternative SHOULD be used instead.

Version expressions SHOULD NOT contain spaces between operators, and MUST be removed and ignored if present.

### Version expression parsing

In the name of backwards compatibility, the (`name`, `version`, `build`) group in the `MatchSpec` syntax allows two types of separators: spaces and a single `=` character. This conditions how certain `version` expressions are parsed. Given a _version literal_ denoted as `version-literal` (i.e. no operators or asterisks), the following rules MUST apply:

- If the string only contains two fields, which MUST be `name` and `version`:
  - `{name}={version-literal}` and `{name} ={version-literal}` (note the space) both denote fuzzy equality. They are equivalent to `{name}[version={version-literal}.*]` and `{name} {version-literal}.*`
  - `{name} {version-literal}` denotes exact equality. It is equivalent to `{name}[version={version-literal}]` and `{name}=={version-literal}`.
- If the string contains three fields, `name`, `version` and `build`:
  - `{name} {version-literal} {build}`, `{name} =={version-literal} {build}`, `{name}={version-literal}={build}` and `{name}=={version-literal}={build}` all denote exact equality. They are equivalent to `{name}[version={version-literal},build={build}]`.
  - `{name} ={version-literal} {build}` denotes fuzzy equality.

Some examples for `name=pkg` and `version-literal=1.8`, with equivalent version specifiers in the same paragraph:

```text
pkg=1.8
pkg =1.8
pkg 1.8.*
pkg 1.8.* *
pkg=1.8.*
pkg=1.8.*=*
pkg =1.8.* *
pkg[version=1.8.*]
pkg[version="1.8.*"]

pkg 1.8
pkg 1.8 *
pkg==1.8
pkg=1.8=*
pkg==1.8=*
pkg ==1.8 *
pkg[version=1.8]
pkg[version="1.8"]
```

### Fully specified expressions

To uniquely identify a single package record, a `MatchSpec` expression can be constructed in two ways:

- By passing exact values to the fields `channel` (preferably by URL), `subdir`, `name`, `version`, `build`.
- By matching its checksum directly: `*[md5=12345678901234567890123456789012]` or `*[sha256=f453db4ffe2271ec492a2913af4e61d4a6c118201f07de757df0eff769b65d2e]`.

## Examples

```python
>>> str(MatchSpec('foo 1.0 py27_0'))
'foo==1.0=py27_0'
>>> str(MatchSpec('foo=1.0=py27_0'))
'foo==1.0=py27_0'
>>> str(MatchSpec('conda-forge::foo[version=1.0.*]'))
'conda-forge::foo=1.0'
>>> str(MatchSpec('conda-forge/linux-64::foo>=1.0'))
"conda-forge/linux-64::foo[version='>=1.0']"
>>> str(MatchSpec('*/linux-64::foo>=1.0'))
"foo[subdir=linux-64,version='>=1.0']"
```

## Rationale

The initial `MatchSpec` form was a simpler `name [version [build]]` syntax (still in use in build recipes), with two optional keyword arguments (`optional`, `target`) between parentheses. The CLI also had its own string specification, which only supported name and version separated by `=` symbols (see [`conda 4.3.x`'s `spec_from_line()`](https://github.com/conda/conda/blob/b65743878d9d368dc45dc0089a651e72adb10274/conda/cli/common.py#L517-L540)). `conda search` allowed queries based on regexes only.

With `conda 4.4.0`, a new syntax was introduced to unify and consolidate all these different variations (see [release notes for 4.4.0](https://github.com/conda/conda/blob/main/CHANGELOG.md#new-feature-highlights-2), [`conda/conda#4158`](https://github.com/conda/conda/pull/4158), and [`conda/conda#5517`](https://github.com/conda/conda/pull/5517)), and also brought channel and subdir matching (fields before `::`) and arbitrary record field matching in between square brackets.

The new syntax had to maintain backwards compatibility with the space- and `=`-separated forms too. This is the reason behind some surprising behaviors discussed in the specification above.

Mixing `*` with other version-specific operators is disallowed as per the recommendations discussed in <https://github.com/conda/ceps/pull/60>.

## References

- [`conda.models.match_spec.MatchSpec`](https://github.com/conda/conda/blob/24.5.0/conda/models/match_spec.py)
- [`rattler_conda_types::match_spec`](https://github.com/conda/rattler/blob/rattler-v0.37.4/crates/rattler_conda_types/src/match_spec/mod.rs)
- [Package match specifications at conda-build docs](https://docs.conda.io/projects/conda-build/en/latest/resources/package-spec.html#package-match-specifications)
- [Comparison of `MatchSpec` implementation in `conda` vs a LARK grammar](https://github.com/chenghlee/conda-matchspec-grammar)
- [Comparison of `MatchSpec` implementations in `conda`, `rattler` and `mamba`](https://github.com/baszalmstra/cep-matchspec-tests)

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
