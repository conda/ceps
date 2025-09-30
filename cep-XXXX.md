# CEP XXXX - Metadata files served by conda channels

<table>
<tr><td> Title </td><td> CEP XXXX - Metadata files served by conda channels </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Jaime Rodríguez-Guerra &lt;jaime.rogue@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> Sep 30, 2025 </td></tr>
<tr><td> Updated </td><td> Sep 30, 2025 </td></tr>
<tr><td> Discussion </td><td> N/A </td></tr>
<tr><td> Implementation </td><td> N/A </td></tr>
</table>

## Abstract

This CEP standardizes the schema for the metadata files served in conda channels. Namely, `repodata.json` (and its variants) and `channeldata.json`.

> Channels may also serve `run_exports.json`, which is described in [CEP 12](./cep-0012.md).

## Motivation

The motivation of this CEP is merely informative. It describes the schema of existing metadata files already in wide use.

## Specification

As per [CEP 26](./cep-0026.md), a conda channel is defined as a location that MUST serve a `noarch/repodata.json` path. It MAY also serve additional, platform-specific `repodata.json` paths under other subdirectories of the same depth, which MUST follow the `subdir` naming conventions described in [CEP 26](./cep-0026.md).

A conda channel MAY also serve a `channeldata.json` path in its root level.

Note that there are no requirements for these paths to be backed by a proper filesystem; the contents of these locations can also be provided by API endpoints.

The contents of the `repodata.json` and `channeldata.json` documents MUST follow the schemas described below.

### `repodata.json`

`repodata.json` documents are subdir-specific JSON dictionaries that aggregate the `index.json` metadata of the included conda artifacts (see [CEP PR#133](https://github.com/conda/ceps/pull/133)), and extend them with details only known when the compressed artifact has been generated (such as size, timestamp, or checksums).

Each `repodata.json` MUST represent a dictionary with the keys listed below. All of them are optional. Additional top-level keys MUST be allowed but they MUST be ignored if not recognized.

- `info: dict[str, dict]`. Metadata about the `repodata.json` itself. See [info metadata](#info-metadata).
- `packages: dict[str, dict]`. This entry maps `*.tar.bz2` filenames to their [package record metadata](#package-record-metadata).
- `packages.conda: dict[str, dict]`. This entry maps `*.conda` filenames to [package record metadata](#package-record-metadata).
- `removed: list[str]`. List of filenames that were once included in either `packages` or `packages.conda`, but they were removed. See [repodata patching](#repodata-patching) for more information.

#### `info` metadata

This dictionary stores information about the repodata file. It MUST follow this schema:

- `subdir: str`. Recommended. The channel subdirectory this `repodata.json` belongs to.
- "... TODO"

#### Package record metadata

Each entry in `packages` and `packages.conda` MUST follow the `index.json` schema (see [CEP PR#133](https://github.com/conda/ceps/pull/133)), augmented with these keys:

- `md5: str | None`. Hexadecimal string of the MD5 checksum of the compressed artifact.
- `sha256: str | None`. Hexadecimal string of the SHA256 checksum of the compressed artifact.
- `size: int`. Size, in bytes, of the compressed artifact.

#### Repodata variants

... TODO. `current_repodata.json` and timebased snapshots.

#### Repodata patching

... TODO.

### `channeldata.json`

Deprecated.

This JSON document MAY be served at the root of the conda channel. It aggregates some packaging metadata across all the channel subdirectories. It MUST follow this schema:

- `channeldata_version: int`. Version of the `channeldata` schema. Currently `1`.
- `subdirs: list[str]`: List of subdirectories supported by the channel.
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

## Examples

A minimal conda channel only needs a single, empty file:

```text
./noarch/repodata.json
```

A conda channel with a Linux x64 specific subdirectory:

```text
./noarch/repodata.json
./linux-64/repodata.json
```

Optionally serving `channeldata.json`:

```text
./noarch/repodata.json
./linux-64/repodata.json
./channeldata.json
```

## Rationale

The `channeldata.json` file is considered deprecated because the listed metadata may be unreliable. It assumes that all the artifacts for a given package name will always have a homogeneous composition, but this is not necessarily true. Some examples:

- Some artifacts may contain activation scripts on some platforms, but not on others.
- Prefix replacement may only be needed from a certain point in the lifetime of the project (e.g. the maintainers add a compiled extension for performance).
- The website or license may change during the project lifetime.

## References

- <https://docs.conda.io/projects/conda-build/en/stable/concepts/generating-index.html>

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
