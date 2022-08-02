<table>
<tr><td> Title </td><td> Conda Release Schedule </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td>
<td> Ken Odegard &lt;kodegard@anaconda.com&gt;, Jannis Leidel &lt;jleidel@anaconda.com&gt; </td></tr>
<tr><td> Created </td><td> May 20, 2022 </td></tr>
<tr><td> Updated </td><td> August 1, 2022 </td></tr>
<tr><td> Discussion </td><td> https://github.com/conda-incubator/ceps/pull/26 </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
</table>

## Abstract

This CEP describes a release cadence for all future `conda` versions starting with `22.9.0`.

## Specification

We propose regularly scheduled bi-monthly (every two months) releases where the tagging/release occurs during the week (per ISO 8601, Monday through Thursday) of the second Monday of the month.

In a nod to our many different kinds of users, we will also propose a deprecation policy (to be defined in a later CEP) that allows for a slower adoption rate (i.e., users could update every 3-4 months instead).

To accomplish better, more predictable versioning, we will adopt [CalVer](https://calver.org/):
- `YY`: the major version will be the shortened year (22+)
- `MM`: the minor version will be the shortened month (1-12)
- `MICRO`: the micro/patch version is reset to zero every month and incremented for every additional release that occurs during that month (0+)

This scheme will start with the September 2022 release of 22.9.0, resulting in the following regular release schedule:

| Version | Release Week |
|---|---|
| 22.9.0 | 2022-09-12 |
| 22.11.0 | 2022-11-14 |
| 23.1.0 | 2023-01-09 |
| 23.3.0 | 2023-03-13 |
| 23.5.0 | 2023-05-08 |
| 23.7.0 | 2023-07-10 |
| 23.9.0 | 2023-09-11 |
| ... | ... |

> **Note**
> Despite following a bimonthly release schedule, we will permit releases to occur at any time between regular releases for hotfixes, security releases, or other high-priority changes that require immediate release.

To distinguish between the bi-monthly release schedule and other optional releases, we define the following release types:

- **Regular release**: the regularly scheduled bi-monthly release
- **Optional release**: releases that may occur on alternating months from regular releases
- **Hotfix release**: extra releases that may occur during any month to patch an earlier release of the same month (whether a regular or optional release)

So, it's entirely feasible to see the following releases:

| Version | Release Type |
|---|---|
| 22.9.0 | regular |
| 22.9.1 | hotfix |
| 22.9.2 | hotfix |
| 22.10.0 | optional |
| 22.10.1 | hotfix |
| 22.11.0 | regular |
| 22.12.0 | optional |
| 22.12.1 | hotfix |
| ... | ... |

## Motivation

Our goal with this CEP is to remove ambiguity/maintainer guesswork of when and what warrants a release.

## Backwards Compatibility

Adopting this release schedule does not break any existing processes or schemes.

We will eliminate confusion regarding years of rumored changes slated for a `conda 5.0` release since we will skip from `conda 4.14.0` to `conda 22.9.0`. Avoiding `conda 5.0` is not to say that these changes won't occur, but instead that it's unrealistic for these changes to be successfully (and safely) rolled out in a single release.

Finally, since `SemVer` is semantically interchangeable with `CalVer` and we propose switching from `conda 4.14.0` to `conda 22.9.0`, both version parsing and version ordering will be unaffected.

## Alternatives

1. Do nothing. Continue with ad hoc releases.
    - Rejected for being too inconsistent and challenging for roadmap/planning purposes.
2. Follow a monthly schedule.
    - Rejected for being too fast for maintainers and multi-user installs.
3. Follow a quarterly schedule.
    - Rejected for being too slow for maintainers and the average user who wants to see improvements.

## Resolution

This section contains the final decision on this issue.

## Reference

- [PEP 602 – Annual Release Cycle for Python](https://peps.python.org/pep-0602/)
- [Django's Release Cadence](https://docs.djangoproject.com/en/dev/internals/release-process/#release-cadence)

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
