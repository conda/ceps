<table>
<tr><td> Title </td><td> Technical specification for creation, modification and deletion of conda environments </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Jaime Rodríguez-Guerra &lt;jrodriguez@quansight.com&gt;</td></tr>
<tr><td> Created </td><td> Jun 10, 2022</td></tr>
<tr><td> Updated </td><td> Jun 10, 2022</td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
</table>

## Abstract

Conda environments have existed for more than 10 years. During most of that time,
`conda` was the only tool available to create, modify and delete conda environments. As a result,
once the Python implementation was considered stable enough, its integration test suite could be
regarded as the only technical specification needed for practical purposes.

However, as other tools appeared in the ecosystem (namely `mamba` and `micromamba`, along with the
`libmamba`-based solver), some of the tests contained in the integration suite did not adjust to
the ecosystem expectations (tests too strict, too tied to `conda` implementation details,
ambiguous results, conflicting outcomes across different tests, etc).

In this CEP, we'd like to propose a minimum set of guidelines any software implementation that
operates on `conda` environments should adhere to.

## Specification

The technical specification will list a set of cases where known input conditions are given, and
list the expected outcome and its rationale. It will be detailed at the command-line interface
level following conda's 4.13 implementation. However, this CEP will not try to standardize the CLI
commands, subcommands or flags. That work can be discussed in a different CEP.

### Terminology

#### Conda environment

#### Package record

#### Match specification

#### Environment file

#### Lock file

#### History file

#### Pinning

### Creation of conda environments

### Deletion of conda environments

### Modification of conda environments


## References


## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
