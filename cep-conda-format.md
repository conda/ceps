<table>
<tr><td> Title </td><td> conda-build creates .conda packages </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Steve Croce &lt;scroce@anaconda.com&gt;</td></tr>
<tr><td> Created </td><td> Dec 29, 2021</td></tr>
<tr><td> Updated </td><td> Jan 12, 2022</td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> To be implemented </td></tr>
</table>

## Abstract

The `.conda` package format has been in use within the conda ecosystem for years and has a number of advantages over the `.tar.bz2` format. However, building both `.conda` and `.tar.bz2` packages still requires multiple steps and is not well documented. conda-build should fully support building and outputting `.conda` package formats in addition to the "legacy" `.tar.bz2` format either individually or at the same time.

## Specification

Today, conda-build includes functionality to create `.conda` packages if:

- in package's meta.yaml, output `type` field set to `conda_v2` *OR*
- in .condarc, `pkg_format` is set to 2

The proposal is to:

- Expand the `pkg_format` setting in the .condarc to accept a list of formats to build at once.
- Expand the conda_build_config.yaml with a setting to define package format and accept a list of formats.
- Improve conda-build's documentation for the package format and how to create it

A topic for discussion is whether default behavior should changed at some point to build both `.tar.bz2` and `.conda`, and the appropriate timeline to do so. This could help improve adoption and support of the `.conda` format.

## Reference

    * https://docs.google.com/document/d/1HGKsbg_j69rKXPihhpCb1kNQSE8Iy3yOsUU2x68x8uw/edit
    * https://github.com/conda/conda/pull/8265
    * https://github.com/conda/conda-build/pull/3334

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
