# CEP XXXX - Channel-wide metadata files served by conda channels

<table>
<tr><td> Title </td><td> CEP XXXX - Channel-wide metadata files served by conda channels </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Jaime Rodríguez-Guerra &lt;jaime.rogue@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> Nov 5, 2025 </td></tr>
<tr><td> Updated </td><td> Jan 29, 2026 </td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/140 </td></tr>
<tr><td> Implementation </td><td> https://github.com/conda/conda-index/blob/0.7.0/conda_index/index/__init__.py#L818 </td></tr>
<tr><td> Requires </td><td> https://github.com/conda/ceps/pull/133 </td></tr>
</table>

## Abstract

This CEP describes the channel-wide metadata files served in conda channels. Namely, `channeldata.json`.

## Motivation

The motivation of this CEP is merely informative. It describes the schema of an existing metadata file.

## Specification

> The terms conda channel, channel subdirectory, package name, and version are to be understood as specified by [CEP 26](./cep-0026.md). Package scripts like activation, deactivation, post-link, pre-link and pre-unlink are defined in [CEP PR#133](https://github.com/conda/ceps/pull/133). Other package metadata fields are also defined there.

A conda channel MAY serve a `channeldata.json` path.

If present, this JSON document MUST be served at the root of the conda channel. It aggregates some packaging metadata across all the channel subdirectories. It MUST follow this schema:

- `channeldata_version: int`. Version of the `channeldata` schema. Currently `1`.
- `subdirs: list[str]`: List of channel subdirectories available in the channel.
- `packages: dict[str, dict]`. Mapping of package names to a dictionary with the following metadata:
  - `activate.d: bool`. Whether the packages feature activation scripts.
  - `binary_prefix: bool`. Whether the package files contain a prefix placeholder that must be replaced in binary mode.
  - `deactivate.d: bool`. Whether the packages feature deactivation scripts.
  - `dev_url: str`. URL to the main website of the project.
  - `doc_url: str`. URL to the documentation website of the project.
  - `home: str`. URL to the main website of the project.
  - `license: str`. License of the project, preferably a SPDX expression.
  - `post_link: bool`. Whether the packages feature post-link scripts.
  - `pre_link: bool`. Whether the packages feature pre-link scripts.
  - `pre_unlink: bool`. Whether the packages feature pre-unlink scripts.
  - `run_exports: dict[str, dict]`. Mapping of versions to their `run_exports` metadata. See [CEP 12](./cep-0012.md) for the valid keys.
  - `source_url: str | list[str]`. URL (or URLs) of the sources that were fetched to build the package.
  - `subdirs: list[str]`. Channel subdirectories under which this package is available.
  - `summary: str`. Short description of the project.
  - `text_prefix: bool`. Whether the package files contain a prefix placeholder that must be replaced in text mode.
  - `timestamp: int`. Upload date of the most recently published artifact, as a POSIX timestamp in milliseconds.
  - `version: str`. Most recent version published in the channel.

## Rationale

The `channeldata.json` file is considered optional because the listed metadata may be unreliable. It assumes that all the artifacts for a given package name will always have a homogeneous composition, but this is not necessarily true. Some examples:

- Some artifacts may contain activation scripts on some platforms, but not on others.
- Prefix replacement may only be needed from a certain point in the lifetime of the project (e.g. the maintainers add a compiled extension for performance).
- The website or license may change during the project lifetime.

## References

- <https://docs.conda.io/projects/conda-build/en/stable/concepts/generating-index.html>

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
