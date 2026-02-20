# CEP XXXX - Version literals and their ordering

<table>
<tr><td> Title </td><td> Version literals and their ordering </td></tr>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td>
  Jaime Rodríguez-Guerra &lt;jaime.rogue@gmail.com&gt;,
  Bas Zalmstra &lt;bas@prefix.dev&gt;
</td></tr>
<tr><td> Created </td><td> Sep 26, 2025 </td></tr>
<tr><td> Updated </td><td> Feb 13, 2026 </td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/132 </td></tr>
<tr><td> Implementation </td><td> https://github.com/conda/conda/blob/6614653b1d9bdbffcef55e338d3220daed70c7f8/conda/models/version.py#L52, https://github.com/conda/rattler/blob/rattler-v0.37.4/crates/rattler_conda_types/src/version/mod.rs#L141 </td></tr>
</table>

> The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC2119][RFC2119] when, and only when, they appear in all capitals, as shown here.

## Abstract

This CEP describes version literals as used in the conda ecosystem, and their ordering.

## Motivation

The motivation of this CEP is mostly informative, but will also try to clarify some ambiguous details that should be homogenized across existing implementations.

## Specification

### Version literals

[CEP 26](./cep-0026.md) only discussed the type of characters that can be part of a version string (or literal), and its maximum length:

> [...] version strings MUST only consist of digits, periods, lowercase ASCII letters, underscores, plus symbols, and exclamation marks. The maximum length of a version string MUST NOT exceed 64 characters.

The present CEP _extends_ these rules with additional constraints:

- Version literals MUST be composed of alphanumeric characters `[A-Za-z0-9]`, separated into segments by periods `.` and underscores `_`. Dashes `-` are historically allowed and interpreted as underscores, but SHOULD NOT be used because they break filename conventions.
- Consecutive runs of digits MUST NOT exceed a value of `2^31-1`.
- Empty segments (i.e. two consecutive periods, or a period plus an underscore) SHOULD NOT be allowed.
- A single trailing underscore MAY be used exceptionally for comparisons against `openssl 1.x`-like version schemes (e.g. `1.0.1_ < 1.0.1a`).
- A single epoch number (a positive integer followed by `!`) MAY prefix the rest of the string.
- A single local version string MAY be added at the end, separated by a plus symbol `+`.

### Ordering

Before being compared, version literals MUST be parsed into a list of segments (with each segment being a list of components) as follows:

- They are first split into _epoch_, _main version_, and _local version_ at `!` and `+` respectively.
  - If there is no `!`, the epoch is set to `0`.
  - If there is no `+`, the local version is empty.
- The main version part is then split into components at `.`, `_`, and `-`.
  - Each component is split again into consecutive runs of numerals and non-numerals.
  - Subcomponents containing only numerals are converted to integers.
  - Strings are converted to lowercase, with special treatment for `dev` and `post`.
  - Trailing underscores are considered part of the preceding string, if any.
  - When a component starts with a letter, the fill value `0` is inserted before the letter.
  - Leading zeros in a component are removed.
- The epoch and main version segments are concatenated.
- The same is repeated for the local version part, and stored as a separate list of segments.

For example:

```python
>>> parse("1.2g.beta15.rc")
[[0], [1], [2, 'g'], [0, 'beta', 15], [0, 'rc']], []
>>> parse("1!2.15.1_ALPHA")
[[1], [2], [15], [1], [0, 'alpha']], []
>>> parse("1!2.15.1alpha_")
[[1], [2], [15], [1, 'alpha_']], []
>>> parse("1!2.15.1_alpha+1.2.3h123")
[[1], [2], [15], [1], [0, 'alpha']], [[1], [2], [3, 'h', 123]]
```

The resulting list of components MUST be compared as follows:

- Integers are compared numerically.
- Strings are compared lexicographically, case-insensitive. The substring `dev` is always smaller.
- Strings are considered smaller than integers, except for `post`, which is always greater.
- When a component has no correspondent, the missing component is assumed to be `0`.
- Local versions are only compared when the main versions are identical. A version without a local part is treated as having an implicit local version of 0.

> Warning:
> Pre-releases markers are sensitive to leading zeros and periods. While `"1.1.0" == "1.1.0.0" ==
> "1.1"`, the rule "When a component starts with a letter, the fill value `0` is inserted" results
> in `"1.1.0rc" == "1.1.rc" > "1.1rc"`. See [conda#12568](https://github.com/conda/conda/issues/12568).

## Rationale

- The `dev` substring is handled differently to allow `dev` pre-releases to sort before alphas, betas, and release candidates.
- The `post` substring is handled differently to allow `post` releases to sort after any equivalent final release.
- Missing components are treated like `0` to allow equivalences like `'1.1' == '1.1.0'`.
- The `0` fill value is used in components starting with letters to keep numbers and strings in phase, resulting in `'1.1.a1' == '1.1.0a1'`.
- Consecutive runs of digits are limited to prevent integer overflow issues upon parsing. The upper bound is the maximum value for 32-bit unsigned integers because [MSVC still defaults to that for `int`](https://learn.microsoft.com/en-us/cpp/cpp/fundamental-types-cpp?view=msvc-180#sizes-of-built-in-types).

## Rejected ideas

conda's version ordering is often compared to Python's PEP 440 and following adjustments, but they are not the same specification. We chose not to incorporate many good ideas in that specification so this CEP represents the current state of the ecosystem. In the future, we may revisit some of these rules to accommodate for special cases in prerelease ordering and their synonyms.

## Backwards compatibility

This CEP _extends_ [CEP 26](./cep-0026.md) with more details about version literals.

It respects existing implementations and does not break backwards compatibility.

## Further work

This CEP only standardizes the current behavior exhibited across most implementations. There are many edge cases that the authors would like to improve in future efforts. Examples include:

- `alpha` == `a` (and similar) suffix normalizations.
- Require version literals to start with a digit to avoid situations like `v0.1 != 0.1`.
- Revise PEP440 normalization rules and study which ones we should adopt.
- Propose a stricter subset of these rules to reduce ambiguity.

## Examples

The ordering specification results in the following versions sorted in this way:

```sh
  0.4
  == 0.4.0
< 0.4.1.rc
  == 0.4.1.RC    # case-insensitive comparison
< 0.4.1+local    # 'local' < 0
< 0.4.1+0.local  # '0.local' < 0
< 0.4.1
  == 0.4.1+0     # no local is the same as '+0'
< 0.4.1+1.local  # '1.local' > 0
< 0.5a1
< 0.5b3
< 0.5C1
< 0.5
< 0.9.6
< 0.960923
< 1.0
< 1.1dev1  # special case 'dev'
< 1.1a1
< 1.1.0dev1
  == 1.1.dev1  # 0 is inserted before string
< 1.1.a1
< 1.1.0rc1
< 1.1.0.0
  == 1.1.0
  == 1.1
< 1.1.post1  # special case 'post'
  == 1.1.0post1
< 1.1post1
< 1996.07.12
< 1!0.4.1  # epoch increased from implicit 0
< 1!3.1.1.6
< 2!0.4.1
```

Local versions are not very common but there are some examples:

```text
$ conda search "*[version='*+*']"
Loading channels: done
# Name                       Version           Build  Channel
py-sirius-ms         2.1+sirius6.0.3    pyhd8ed1ab_0  conda-forge
py-sirius-ms         2.1+sirius6.0.4    pyhd8ed1ab_0  conda-forge
py-sirius-ms         2.1+sirius6.0.5    pyhd8ed1ab_0  conda-forge
py-sirius-ms         2.1+sirius6.0.6    pyhd8ed1ab_0  conda-forge
py-sirius-ms         2.1+sirius6.0.7    pyhd8ed1ab_0  conda-forge
py-sirius-ms         2.1+sirius6.0.7    pyhd8ed1ab_1  conda-forge
py-sirius-ms         3.0+sirius6.1.0    pyhd8ed1ab_0  conda-forge
py-sirius-ms         3.0.1+sirius6.1.0    pyhd8ed1ab_0  conda-forge
py-sirius-ms         3.1+sirius6.1.1    pyhd8ed1ab_0  conda-forge
r-sirius-ms          2.1+sirius6.0.4   r44h57928b3_1  conda-forge
r-sirius-ms          2.1+sirius6.0.4   r44h694c41f_1  conda-forge
r-sirius-ms          2.1+sirius6.0.4   r44ha770c72_1  conda-forge
r-sirius-ms          2.1+sirius6.0.5   r44h57928b3_1  conda-forge
r-sirius-ms          2.1+sirius6.0.5   r44h694c41f_1  conda-forge
r-sirius-ms          2.1+sirius6.0.5   r44ha770c72_1  conda-forge
r-sirius-ms          2.1+sirius6.0.6   r44h57928b3_1  conda-forge
r-sirius-ms          2.1+sirius6.0.6   r44h694c41f_1  conda-forge
r-sirius-ms          2.1+sirius6.0.6   r44ha770c72_1  conda-forge
r-sirius-ms          2.1+sirius6.0.7   r44h57928b3_0  conda-forge
r-sirius-ms          2.1+sirius6.0.7   r44h57928b3_1  conda-forge
r-sirius-ms          2.1+sirius6.0.7   r44h694c41f_0  conda-forge
r-sirius-ms          2.1+sirius6.0.7   r44h694c41f_1  conda-forge
r-sirius-ms          2.1+sirius6.0.7   r44ha770c72_0  conda-forge
r-sirius-ms          2.1+sirius6.0.7   r44ha770c72_1  conda-forge
r-sirius-ms          3.0.1+sirius6.1.0   r44h57928b3_0  conda-forge
r-sirius-ms          3.0.1+sirius6.1.0   r44h694c41f_0  conda-forge
r-sirius-ms          3.0.1+sirius6.1.0   r44ha770c72_0  conda-forge
r-sirius-ms          3.1+sirius6.1.1   r44h57928b3_0  conda-forge
r-sirius-ms          3.1+sirius6.1.1   r44h694c41f_0  conda-forge
r-sirius-ms          3.1+sirius6.1.1   r44ha770c72_0  conda-forge
r-sirius-ms          3.1+sirius6.1.1   r45h57928b3_1  conda-forge
r-sirius-ms          3.1+sirius6.1.1   r45h694c41f_1  conda-forge
r-sirius-ms          3.1+sirius6.1.1   r45ha770c72_1  conda-forge
typst-test           0.0.0.post105+699b871      h6e96688_0  conda-forge
typst-test           0.0.0.post105+699b871      h6e96688_1  conda-forge
typst-test           0.0.0.post106+2b4e689      h6e96688_0  conda-forge
```

## References

- [`conda 25.7.x` docs on Version Ordering](https://docs.conda.io/projects/conda/en/25.7.x/user-guide/concepts/pkg-specs.html#version-ordering).
- [Comparison between `conda`, `rattler` and `mamba` parsers](https://github.com/baszalmstra/cep-version-tests).
- [Draft CEP about disallowing `*` in version literals](https://github.com/conda/ceps/pull/60).

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

<!-- links -->

[RFC2119]: https://www.ietf.org/rfc/rfc2119.txt
