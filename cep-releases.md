<table>
<tr><td> Title </td><td> Conda Release Schedule </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Ken Odegard &lt;kodegard@anaconda.com&gt; </td></tr>
<tr><td> Created </td><td> May 20, 2022 </td></tr>
<tr><td> Updated </td><td> July 5, 2022 </td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
</table>

## Abstract

Describes a release cadence for all future `conda` versions starting with `22.9.0`.

## Specification

We propose a bimonthly (every two months) release schedule where the tagging/release occurs during the week (per ISO 8601, Monday through Sunday) of second Monday of the month.

In a nod to our many different kinds of users we will propose a deprecation policy (to be defined in a later CEP) that allows for a slower adoption rate (i.e. users could update every 3-4 months instead).

These objectives will be aided in the adoption of [CalVer](https://calver.org/):
- `YY`: the major version will be the shortened year (22+)
- `MM`: the minor version will be the shortened month (1-12)
- `MICRO`: the micro/patch version is reset to zero every month and incremented for every additional release that occurs during that month (0+)

This scheme will start with the July 2022 release of 22.7.0.

This will result in the following regular release schedule:
- 22.7.0: 2022-07-11
- 22.9.0: 2022-09-12 (9 weeks of development)
- 22.11.0: 2022-11-14 (9 weeks)
- 23.1.0: 2023-01-09 (8 weeks)
- 23.3.0: 2023-03-13 (9 weeks)
- 23.5.0: 2023-05-08 (8 weeks)
- 23.7.0: 2023-07-10 (9 weeks)
- 23.9.0: 2023-09-11 (8 weeks)
- ...

Despite following a bimonthly release schedule we will permit releases to occur at any time between the regular releases for hotfixes, security releases, or other high priority changes that require immediate release.

So it's entirely feasible to see the following releases:

- 22.7.0 (regular release)
- 22.7.1
- 22.7.2
- 22.8.0
- 22.9.0 (regular release)
- 22.9.1
- 22.10.0
- 22.10.1
- ...

## Motivation

Remove ambiguity of when and what warrants a release.

## Backwards Compatibility

Adopting this release schedule does not break any existing processes or schemes.

We will entirely sidestep and avoid any confusion regarding years of rumored changes slated to be included in a `conda` 5 release since we won't even attain a 5 release with this new scheme.

## Alternatives

1. Do nothing. Continue with ad hoc releases.
    - Rejected for being too inconsistent and difficult for planning.
2. Follow a monthly schedule.
    - Rejected for being too fast for multi-user installs.
3. Follow a quarterly schedule.
    - Rejected for being too slow for both ourselves and the average user who wants to see improvements.

## Resolution

This section contains the final decision on this issue.

## Reference

- [PEP 602 – Annual Release Cycle for Python](https://peps.python.org/pep-0602/)
- [Django's Release Cadence](https://docs.djangoproject.com/en/dev/internals/release-process/#release-cadence)

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
