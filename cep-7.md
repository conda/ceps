<table>
<tr><td> Title </td><td> Conda Capitalization Standard </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Katherine Kinnaman &lt;kkinnaman@anaconda.com&gt;</td></tr>
<tr><td> Created </td><td> Jun 28, 2022</td></tr>
<tr><td> Updated </td><td> July 5, 2022</td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
</table>

## Abstract

The capitalization conventions for conda need to be decided and written down within the conda docs so that they can be enforced during PRs, for consistency within written materials about and related to conda.

## Specification

Conda should be lowercase except when used at the beginning of a sentence. When speaking about the command, code formatting should be used (i.e. `conda`)

## Motivation

The capitalization of C/conda can be inconsistent. It should be formally decided and written down so that it can be enforced for consistency in any documentation or written materials about conda.

## Alternatives

Conda should be capitalized when speaking about the organization/product and lowercase, with code formatting (i.e. `conda`), when discussing the command. This option was rejected because it is more complex and also because most references to conda in the Anaconda and conda documentation use lowercase.

## Sample Implementation

Conda is a package manager. To use the conda package manager to install a package, use `conda install package` in your command line interface.

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
