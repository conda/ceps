<table>
<tr><td> Title </td><td> Conda Deprecation Schedule </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Ken Odegard &lt;kodegard@anaconda.com&gt; </td></tr>
<tr><td> Created </td><td> May 20, 2022 </td></tr>
<tr><td> Updated </td><td> July 6, 2022 </td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
</table>

## Abstract

Describes a deprecation schedule to properly warn about upcoming removals from the codebase. This will be applicable to the following:

- `conda/conda`
- `conda/conda-build`

Other [conda](https://github.com/conda) or [conda-incubator](https://github.com/conda-incubator) projects may choose to adopt this policy in the future but if they do this CEP should be updated to reflect that adaptation.

## Specification

We propose a deprecation schedule that is slower than the Conda Release Schedule (see CEP-?). This is in acknowledgement of our diverse user groups (e.g. everything from per user per machine installs to multi-user installs on shared clusters).

All deprecations are to be:

1. initially marked as **pending deprecation** and remain in a pending state for at least three (3+) `MINOR` releases
2. January (`YY.1.0`), May (`YY.5.0`), and September (`YY.9.0`) are deprecation releases where:
    - all **pending deprecations** that have been pending for at least three (3+) `MINOR` releases are marked as **deprecations** and remain in a deprecated state for four (4) `MINOR` releases
    - all **deprecations** that have been deprecated for four (4) `MINOR` releases are removed

To summarize, features may be marked as **pending deprecation** in any release however **deprecations** and **removals** only occur in the first release of a quarter.

Occasionally there may be code changes that we feel warrant a longer deprecation schedule. If that occurs the deprecation warning will clearly specify that a deviation is occurring and what the expected schedule will be instead.

## Motivation

Help prevent unexpected breakage of downstream tooling as the codebase evolves.

## Backwards Compatibility

This is backwards compatible and will also encourage better backwards compatibility.

## Alternatives

1. Mark as **pending deprecation** in one release, mark as a **deprecation** the next release, and **remove** in third release.
   - Rejected for being too rapid given the sprawling ecosystem and unknown number of downstream applications.

## Resolution

This section contains the final decision on this issue.

## Reference

- [Django's Deprecation Policy](https://docs.djangoproject.com/en/dev/internals/release-process/#deprecation-policy)

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
