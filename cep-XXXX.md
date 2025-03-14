# CEP XXXX - Versioning of Existing Conda Standards

<table>
<tr><td> Title </td><td> Versioning of Existing Conda Standards and Specs
<tr><td> Status </td><td> Draft  </td></tr>
<tr><td> Author(s) </td><td> Matthew R. Becker &lt;becker.mr@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> Mar 14, 2025</td></tr>
<tr><td> Updated </td><td> Mar 14, 2025</td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
</table>

## Abstract

As the conda ecosystem is being standardized and evolving, the existing standards 
(in many cases only documented by the code that implements them) have been called 
`v1` in some cases (e.g., `.tar.bz2` versus `.conda`) and `v0` in others (e.g., `v0` versus `v1` recipe formats). 
This differing nomenclature is confusing. In this CEP, we resolve this issue by declaring all existing `conda` 
standards, documented formally in CEPs or not, the `v0` standards. Changes to these standards then are labeled `v1`, 
`v2`, etc. as appropriate.

## Specification

All existing conda standards which satisfy the following conditions

- are documented formally in CEPs or are only effectively documented through code implementations
- have not been superceeded by a newer standard labeled `v1`

MUST be versioned at `v0`. 

The number of conda package formats, `.tar.bz2` and `.conda`, is exempt from this CEP.

## Backwards Compatibility

The `v0` versioning is fully backwards compatible with all current standards, except conda package formats
which have been explicitly excluded.

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
