# Conda Enhancement Proposals

[Conda](https://docs.conda.io/) is an Open Source project with a diverse and wide-ranging ecosystem.

To better allow community members to provide feedback and proposals
for conda's implementation, all major changes should be submitted as
**Conda Enhancement Proposals (CEP)**.

## Accepted CEPS

| CEP                 | Title                                                                       |
|---------------------|-----------------------------------------------------------------------------|
| [0000](cep-0000.md) | CEP template                                                                |
| [0001](cep-0001.md) | CEP Purpose and Guidelines                                                  |
| [0002](cep-0002.md) | Add plugin architecture to conda                                            |
| [0003](cep-0003.md) | Using the Mamba solver in conda                                             |
| [0004](cep-0004.md) | Implement initial conda plugin mechanism                                    |
| 0005                | _Does not exist_                                                            |
| [0006](cep-0006.md) | Add Channel Notices to conda                                                |
| 0007                | _Does not exist_                                                            |
| [0008](cep-0008.md) | Conda Release Schedule                                                      |
| [0009](cep-0009.md) | Conda Deprecation Schedule                                                  |
| [0010](cep-0010.md) | Conda Version Support                                                       |
| [0011](cep-0011.md) | Define the menuinst standard                                                |
| [0012](cep-0012.md) | Serving run_exports metadata in conda channels                              |
| [0013](cep-0013.md) | A new recipe format – part 1                                                |
| [0014](cep-0014.md) | A new recipe format – part 2 - the allowed keys & values                    |
| [0015](cep-0015.md) | Hosting repodata.json and packages separately by adding a base_url property |
| [0016](cep-0016.md) | Sharded Repodata                                                            |
| [0017](cep-0017.md) | Optional python site-packages path in repodata                              |
| [0018](cep-0018.md) | Migration to the Zulip chat platform                                        |
| [0019](cep-0019.md) | Computing the hash of the contents in a directory                           |
| [0020](cep-0020.md) | Support for `abi3` Python packages                                          |
| [0021](cep-0021.md) | Run-exports in sharded Repodata                                             |
| [0022](cep-0022.md) | Frozen environments                                                         |
| [0023](cep-0023.md) | Text spec input files                                                       |

## References

These proposals are similar to conda-forge's [CFEP](https://github.com/conda-forge/cfep),
[Python's PEP](https://www.python.org/dev/peps/) and [IPython's IPEP](https://github.com/ipython/ipython/wiki/IPEPs:-IPython-Enhancement-Proposals) processes etc.

## Writing a new CEP

Community members are encouraged to author a CEP to suggest changes _before_
any code is written to allow for the community to discuss the proposed changes.

The formal process by which CEPs should be authored and how they are reviewed
and resolved is specified in [CEP 1](https://github.com/conda/ceps/blob/main/cep-0001.md).

A template for new CEPs is given in [CEP 0](https://github.com/conda/ceps/blob/main/cep-0000.md).

CEPs which are in draft/proposed form should have the number `XXXX` in both their PR title, CEP title, and filename.
A number will be assigned to the CEP upon acceptance, and all references to the CEP should be updated to reflect the
CEP's number. To refer to the CEP before it has a number, use its PR number or its title.

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

Titles and headers should use the same capitalization and formatting standards as sentences.

#### In links

Links should use the same capitalization conventions as sentences. Because the conda docs currently use re-structured text (RST) as a markup language, and [RST does not support nested inline markup](https://docutils.sourceforge.io/FAQ.html#is-nested-inline-markup-possible), documentation writers should avoid using code backtick formatting inside links.
