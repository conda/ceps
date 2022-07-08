<table>
<tr><td> Title </td><td> Conda Capitalization Standard </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Katherine Kinnaman &lt;kkinnaman@anaconda.com&gt;</td></tr>
<tr><td> Created </td><td> Jun 28, 2022</td></tr>
<tr><td> Updated </td><td> July 5, 2022</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda-incubator/ceps/pull/31 </td></tr>
<tr><td> Implementation </td><td> https://github.com/conda/conda-docs/issues/803 </td></tr>
</table>

## Abstract

The capitalization conventions for conda need to be decided and written down within the conda docs so that they can be enforced during PRs, for consistency within written materials about and related to conda. This capitalization consistency is also important as the conda organization begins to formalize governance and NumFOCUS funding documents as we strive to become more organized in the open source community.

## Motivation

The capitalization of C/conda can be inconsistent. It should be formally decided and written down so that it can be enforced for consistency in any documentation or written materials about conda.

## Specification

Conda should be written in lowercase, whether in reference to the tool, ecosystem, packages, or organization. References to the conda command should use code formatting (i.e. `conda`). If the use of conda is not a command and if conda is at the beginning of a sentence, conda should be uppercase.

The standard will be written down in the conda README, as well as in the (Ways to contribute)[https://docs.conda.io/projects/conda/en/latest/dev-guide/contributing.html#ways-to-contribute] section of the conda Developer Guide. These will serve as easy places for PR editors to point, if necessary, but as most people use these conventions already, this standard should not need to be announced heavily.

## Examples

### In sentences

Beginning a sentence: 

- Conda is an open-source package and environment management system. 
- `conda install` can be used to install packages.

Conda in the middle of a sentence: 

- If a newer version of conda is available, you can use `conda update conda` to update to that version.
- You can find conda packages within conda channels. The `conda` command can search these channels.

### In titles and headers

Titles and headers should use the same capitalization and formmating standards as sentences.

### In links

Links should use the same capitalization conventions as sentences. Because the conda docs currently used re-structured text (RST) as a markup language, and (RST does not support nexted inline markup)[https://docutils.sourceforge.io/FAQ.html#is-nested-inline-markup-possible], documentation writers should avoid using code backtick formatting inside links.

## Alternatives

Conda should be capitalized when speaking about the organization/product and lowercase, with code formatting (i.e. `conda`), when discussing the command. This option was rejected because it is more complex and also because most references to conda in the Anaconda and conda documentation use lowercase already.

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
