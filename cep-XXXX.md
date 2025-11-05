# CEP XXXX - Package metadata files served by conda channels

<table>
<tr><td> Title </td><td> CEP XXXX - Metadata files served by conda channels </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Jaime Rodríguez-Guerra &lt;jaime.rogue@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> Sep 30, 2025 </td></tr>
<tr><td> Updated </td><td> Sep 30, 2025 </td></tr>
<tr><td> Discussion </td><td> N/A </td></tr>
<tr><td> Implementation </td><td> N/A </td></tr>
<tr><td> Requires </td><td> https://github.com/conda/ceps/pull/133 </td></tr>
</table>

## Abstract

This CEP standardizes the schema for the package metadata (repodata) files served in conda channels. Namely, `repodata.json` and its variants.

## Motivation

The motivation of this CEP is merely informative. It describes the schema of existing metadata files already in wide use.

## Specification

As per [CEP 26](./cep-0026.md), a conda channel is defined as a location that MUST serve a `noarch/repodata.json` path. It MAY also serve additional, platform-specific `repodata.json` paths under other subdirectories of the same depth, which MUST follow the `subdir` naming conventions described in [CEP 26](./cep-0026.md).

> Note that there are no requirements for these paths to be backed by a proper filesystem; the contents of these locations can also be provided by API endpoints.

`repodata.json` documents are subdir-specific JSON dictionaries that aggregate the `index.json` metadata of the included conda artifacts (see [CEP PR#133](https://github.com/conda/ceps/pull/133)), and extend them with details only known when the compressed artifact has been generated (such as size, timestamp, or checksums).

### Schema

Each `repodata.json` MUST represent a dictionary with the keys listed below. All of them are optional. Additional top-level keys MUST be allowed but they MUST be ignored if not recognized.

- `info: dict[str, dict]`. Metadata about the `repodata.json` itself. See [info metadata](#info-metadata).
- `packages: dict[str, dict]`. This entry maps `*.tar.bz2` filenames to their [package record metadata](#package-record-metadata).
- `packages.conda: dict[str, dict]`. This entry maps `*.conda` filenames to [package record metadata](#package-record-metadata).
- `removed: list[str]`. List of filenames that were once included in either `packages` or `packages.conda`, but are now removed. The corresponding artifacts SHOULD still be accessible via their direct URL.

Additional keys SHOULD NOT be present and SHOULD be ignored.

#### `info` metadata

This dictionary stores information about the repodata file. It MUST follow this schema:

- `arch: str`. Deprecated. Same meaning as in [CEP PR#133](https://github.com/conda/ceps/pull/133)'s `index.json` key.
- `base_url: str`. Optional. See [CEP 15](./cep-0015.md).
- `platform: str`. Deprecated. Same meaning as in [CEP PR#133](https://github.com/conda/ceps/pull/133)'s `index.json` key.
- `repodata_version: int`. Optional. Version of the `repodata.json` schema. In its absence, tools MUST assume its value is `1`. See [CEP 15](./cep-0015.md) for `repodata_version = 2`.
- `subdir: str`. Recommended. The channel subdirectory this `repodata.json` belongs to. If its absence, its value MAY be inferred from the parent component of the `repodata.json` path.

Additional keys SHOULD NOT be present and SHOULD be ignored.

#### Package record metadata

Each entry in `packages` and `packages.conda`:

- MUST follow the `index.json` schema (see [CEP PR#133](https://github.com/conda/ceps/pull/133)).
- SHOULD report the same values as the artifact's `info/index.json` metadata. Small modifications MAY be introduced to apply metadata fixes (e.g. correct the constraints of a requirement in the `depends` field) without needing to rebuild the artifact.
- MUST additionally include the following keys:
  - `md5: str | None`. Hexadecimal string of the MD5 checksum of the compressed artifact.
  - `sha256: str | None`. Hexadecimal string of the SHA256 checksum of the compressed artifact.
  - `size: int`. Size, in bytes, of the compressed artifact.
- If the entry corresponds to a `.tar.bz2` package that was transmuted to `.conda`, it SHOULD include these keys:
  - `legacy_bz2_md5: str`: Hexadecimal string of the SHA256 checksum of the original `.tar.bz2` artifact.
  - `legacy_bz2_size: int`: Size, in bytes, of the original `.tar.bz2` artifact.

Additional keys SHOULD NOT be present and SHOULD be ignored.

### Repodata variants

A conda channel MAY serve additional `repodata.json` documents in each subdir. Their name SHOULD match the glob `*repodata*.json`, and their contents MUST follow the `repodata.json` schema.
Common variants include `current_repodata.json`, which aggregates a subset of the full repodata document, focusing on the latest versions of each package plus their necessary dependencies.

Channels SHOULD serve compressed versions of every repodata file. The following compression schemes are recognized:

- BZ2: MUST append the `.bz2` extension; e.g. `repodata.json.bz2`.
- ZSTD: MUST append the `.zst` extension; e.g. `repodata.json.zst`. Recommended.

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

## References

- <https://docs.conda.io/projects/conda-build/en/stable/concepts/generating-index.html>

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
