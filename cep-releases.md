<table>
<tr><td> Title </td><td> Conda Release Schedule </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Ken Odegard &lt;kodegard@anaconda.com&gt; </td></tr>
<tr><td> Created </td><td> May 20, 2022 </td></tr>
<tr><td> Updated </td><td> May 20, 2022 </td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
</table>

## Abstract

Describes a release cadence for all future `conda` versions starting with 5.0.0.

## Specification

We propose a monthly release schedule where the tagging/release occurs during the week (per ISO 8601, Monday through Sunday) of the 15th.

In a nod to our many different kinds of users we propose a deprecation policy (to be defined in a later CEP) that allows for a slower adoption rate. Users on a slower schedule would be encouraged to update once a quarter.

Both of these policies will be encapsulated in the version scheme:
- the major version will be an annual counter,
- the minor version will correlate with the quarter,
- the micro/patch version will generally correlate with the month within the quarter but will also be incremented if a bug fix/security patch needs an early release, and
- this scheme will start with the July 2022 release of 5.0.0.

This will result in the following release schedule:
- 5.0.0: 2022-07-14
- 5.0.1: 2022-08-18 (5 weeks of development)
- 5.0.2: 2022-09-15 (4 weeks)
- 5.1.0: 2022-10-13 (4 weeks)
- 5.1.1: 2022-11-17 (5 weeks)
- 5.1.2: 2022-12-15 (4 weeks)
- 5.2.0: 2023-01-12 (4 weeks)
- 5.2.1: 2023-02-16 (5 weeks)
- 5.2.2: 2023-03-16 (4 weeks)
- 5.3.0: 2023-04-13 (4 weeks)
- 5.3.1: 2023-05-18 (5 weeks)
- 5.3.2: 2023-06-15 (4 weeks)
- 6.0.0: 2023-07-13 (4 weeks)

## Motivation

Remove ambiguity of when and what warrants a release.

## Backwards Compatibility

Adopting this release schedule does not break any existing processes or schemes.

The only potential "confusion" is the years of rumored changes slated to be included in a `conda` 5 release, may of which may not occur in any `conda` 5 if we adopt the proposed schedule.

## Alternatives

1. Do nothing. Continue with ad hoc releases.
    - Rejected for being too inconsistent and difficult for planning.
2. Follow a monthly schedule.
    - Rejected for being too fast for multi-user installs.
3. Follow a quarterly schedule.
    - Rejected for being too slow for the average user who wants to see improvements.

## Resolution

This section contains the final decision on this issue.

## Reference

- [PEP 602 – Annual Release Cycle for Python](https://peps.python.org/pep-0602/)
- [Django's Release Cadence](https://docs.djangoproject.com/en/dev/internals/release-process/#release-cadence)

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
