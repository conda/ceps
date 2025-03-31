# CEP XXXX - Versioning of Existing conda Standards

<table>
<tr><td> Title </td><td> CEP XXXX - Versioning of Existing conda Standards and Specs </td></tr>
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
This differing nomenclature is confusing. In this CEP, we resolve this issue by establishing conventions on how to number existing and future `conda` standards.

## Specification

All existing conda standards which satisfy the following conditions

- are documented formally in CEPs or are only effectively documented through code implementations
- have not been superseded by a newer standard labeled `v1`

MUST be versioned at `v1`.

The numbering of build recipe formats is exempt from this CEP due to the fact
that the new recipe format in [CEP 14](https://github.com/conda/ceps/blob/main/cep-0014.md) specified `schema_version: 1`.

Standards MUST use a version specifier that consists only of numbers and a single period `.`, has a major version,
and has at most a minor version (i.e. matches the regex `^[0-9]+($|\.[0-9]+$)`). A `v` MAY be prepended
for clarity, but MUST be removed before comparing versions. Version comparisons and ordering MUST follow
`conda`'s version comparison and ordering conventions.

## Backwards Compatibility

The `v1` versioning is fully backwards compatible with all current standards, except recipe formats
which have been explicitly excluded.

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
