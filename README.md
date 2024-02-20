## Conda Enhancement Proposals

[Conda](https://docs.conda.io/) is an Open Source project with a diverse and wide-ranging ecosystem.

To better allow community members to provide feedback and proposals
for conda's implementation, all major changes should be submitted as
**Conda Enhancement Proposals (CEP)**.

## Accepted CEPS:

| CEP | Title |
| --- | ------- |
| [1](cep-1.md) | CEP Purpose and Guidelines  |
| [2](cep-2.md) | Add plugin architecture to conda |
| [3](cep-3.md) | Using the Mamba solver in conda |
| [4](cep-4.md) | Implement initial conda plugin mechanism |
| 5 | Does not exist |
| [6](cep-6.md) | Add Channel Notices to conda
| 7 | Does not exist |
| [8](cep-8.md) | Conda Release Schedule |
| [9](cep-9.md) | Conda Deprecation Schedule |
| [10](cep-10.md) | Conda Version Support |
| [11](cep-11.md) | Define the menuinst standard |
| [12](cep-12.md) | Serving run_exports metadata in conda channels |
| [13](cep-13.md) | A new recipe format - part 1 |
| [14](cep-14.md) | A new recipe format – part 2 - the allowed keys & values |
| [15](cep-15.md) | Hosting repodata.json and packages separately by adding a base_url property. |

## References

These proposals are similar to conda-forge's [CFEP](https://github.com/conda-forge/cfep),
[Python's PEP](https://www.python.org/dev/peps/) and [IPython's IPEP](https://github.com/ipython/ipython/wiki/IPEPs:-IPython-Enhancement-Proposals) processes etc.

## Writing a new CEP

Community members are encouraged to author a CEP to suggest changes *before*
any code is written to allow for the community to discuss the proposed changes.

The formal process by which CEPs should be authored and how they are reviewed
and resolved is specified in [CEP 1](https://github.com/conda/ceps/blob/main/cep-1.md).

A template for new CEPs is given in [CEP 0](https://github.com/conda/ceps/blob/main/cep-0.md).

## Conda capitalization standards

1. Conda should be written in lowercase, whether in reference to the tool, ecosystem, packages, or organization.
2. References to the conda command should use code formatting (i.e. `conda`).
3. If the use of conda is not a command and if conda is at the beginning of a sentence, conda should be uppercase.

### Examples

#### In sentences

Beginning a sentence:

- Conda is an open-source package and environment management system.
- `conda install` can be used to install packages.

Conda in the middle of a sentence:

- If a newer version of conda is available, you can use `conda update conda` to update to that version.
- You can find conda packages within conda channels. The `conda` command can search these channels.

#### In titles and headers

Titles and headers should use the same capitalization and formmating standards as sentences.

#### In links

Links should use the same capitalization conventions as sentences. Because the conda docs currently use re-structured text (RST) as a markup language, and [RST does not support nested inline markup](https://docutils.sourceforge.io/FAQ.html#is-nested-inline-markup-possible), documentation writers should avoid using code backtick formatting inside links.
