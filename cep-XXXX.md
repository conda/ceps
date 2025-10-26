# CEP XXXX - `conda-lock.yml` lockfiles

<table>
<tr><td> Title </td><td> <code>conda-lock.yml</code> lockfiles </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Jaime Rodríguez-Guerra &lt;jaime.rogue@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> Oct 26, 2025 </td></tr>
<tr><td> Updated </td><td> Oct 26, 2025 </td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/138 </td></tr>
<tr><td> Implementation </td><td> https://github.com/conda/conda-lock/blob/v3.0.4/conda_lock/lockfile/v1/models.py </td></tr>
<tr><td> Requires </td><td> https://github.com/conda/ceps/pull/82 </td></tr>
</table>

## Abstract

This CEP standardizes the existing `conda-lock.yml` lockfile format, introduced by [`conda-lock`](https://github.com/conda/conda-lock).

## Motivation

The motivation of this CEP is merely informative. It describes the details of an existing file
format.

## Rationale

The `conda-lock.yml` file format describes a lockfile. As such, its main purpose is to provide the instructions to create environments in a reproducible way. Unlike [explicit lockfiles](./cep-0023.md), `conda-lock.yml` files can encode more than one environment for several platforms. It is also capable of handling PyPI dependencies.

## Specification

`conda-lock.yml` files are YAML documents with three top-level fields: `version`, `metadata` and `package`. The `metadata`  section contains provenance information, while `package` enumerates the lockfile information as a list of packages and their details.

A `conda-lock.yml` file name SHOULD contain the term `conda-lock` and MUST end in `.yml` or `.yaml`.

The `package` list enumerates two types of packages via the `manager` field: `conda` and `pip`. Packages labeled with `manager == "conda"` SHOULD be installed first. For a lockfile to contain packages labeled with `manager == "pip"`, a Python interpreter SHOULD be provided by the conda packages.

### Schema

#### Top-level `version`

Optional, defaults to `1`.

A positive integer that describes the version of the schema. The only currently admitted value is `1`.

#### `metadata`

Required.

A dictionary that describes provenance and reproducibility metadata for the lockfile. It MUST only include the following keys, mapping to the values specified below. Additional keys MUST NOT be present.

##### `content_hash`

`dict[str, str]`, required.

This dictionary MUST map each key present in `platforms` to a SHA256 hash, as a lowercased hexadecimal string. The hash MUST be computed from the packages present in that target platform.

##### `channels`

`list[Channel]`, required.

This list collects all the conda channels used to generate the lockfile.

Each `Channel` item MUST be a dictionary with the following keys:

- `url` MUST map to a non-empty `str` that describes the source URL of the given channel.
- `used_env_vars` MUST map to a `list[str]` that described which environment variables are necessary to access the channel URL, if any.

##### `platforms`

`list[str]`, required.

This list collects all the target platforms supported by the lockfile. Each target platform MUST conform to a [CEP 26](./cep-0026.md) `subdir` string, excluding `noarch`.

##### `sources`

`list[str]`, required.

A list of paths to source files used to generate the lockfile. These paths MUST be relative to the location of the lockfile.

##### `time_metadata`

`dict[str, str]`, optional.

A dictionary with a single key, `created_at`, that MUST map to string encoding the ISO 8601 timestamp as `%Y-%m-%dT%H:%M:%SZ`.

##### `git_metadata`

`dict[str, str]`, optional.

A dictionary that includes provenance information about the git repository and the user that created it.

It MUST accept the following optional keys. Any other keys MUST NOT be accepted.

- `git_user_name`: `str`, optional. User name, as obtained from the `user.name` field in the global configuration.
- `git_user_email`: `str`, optional. User email, as obtained from the `user.email` field in the global configuration.
- `git_sha`: `str`, optional. Hash of the most recent git commit that modified one of the `sources` for this lockfile.

##### `inputs_metadata`

`dict[str, dict[str, str]]`, optional.

A dictionary that maps each of the paths in `sources` to their corresponding content hashes. Each value MUST be a dictionary with only two keys, `md5` and `sha256`, which MUST map to the hexadecimal digest strings of the MD5 and SHA256 hashes of the input file contents, respectively.

##### `custom_metadata`

`dict[str, str]`, optional.

Free form metadata, as key-value string pairs.

#### `package`

`list[LockedDependency]`, required.

This list enumerates the lockfile contents. Each item MUST be a dictionary, termed `LockedDependency` with the following keys:

##### `name`

`str`, required.

Package name, as described in [CEP 26](./cep-0026.md).

##### `version`

`str`, required.

Version string, as described in [CEP 26](./cep-0026.md).

##### `manager`

`Literal["conda", "pip"]`, required.

The ecosystem this package belongs to. `pip` is to be understood as PyPI.

##### `platform`

`str`, required.

The platform this package targets. It MUST be one of the items in `metadata.platforms`.

##### `dependencies`

`dict[str, str]`, optional.

A dictionary that MUST map a package name string (as in [CEP 26](./cep-0026.md)) to a constraint string.

When these two strings are concatenated, it MUST result in a:

- For `manager == "conda"` entries, a `MatchSpec` string, as described in [CEP PR#82](https://github.com/conda/ceps/pull/82).
- For `manager == "pip"` entries, a [PEP 440](https://peps.python.org/pep-0440/) dependency specifier.

##### `url`

`str`, required.

Direct download URL for this package.

##### `hash`

`dict[str, str]`, required.

A dictionary which MUST only contain at most two keys, `md5` and `sha256`, which MUST map to the hexadecimal digest strings of the MD5 and SHA256 hashes of the downloaded artifact, respectively.

##### `source`

`dict[str, str]` optional.

Provenance details of the package. It MUST only contain two keys, `type` (whose only valid value is the string `url`) and `url` (which maps to a URL string).

##### `build`

`str`, optional.

It MUST be the build string of the package, as expressed in [CEP 26](./cep-0026.md), when the `manager` field is set to `conda`. It SHOULD be `None` otherwise.

##### `category`

`str`, optional, defaults to `main`.

A non-empty string that reports which install group this package belongs to. If not provided, `main` MUST be assumed.

##### `optional`

`bool`, required.

A boolean specifying whether this package is required in the created environment or not.

## Examples

A minimal example to install `ca-certificates` in Linux, macOS (Intel and Apple Silicon), and Windows would look like this:

```yaml
version: 1
metadata:
  content_hash:
    linux-64: af8caa5bbfb00f2641c82d05c7258a316df062d8fadc022a7f47dfd3a25ab331
    osx-arm64: c42e37e577b97bb1e4aafd415a42d1f7cf3e2e579df9250afcf87f8816c32393
    osx-64: a2df6aa6d2047b27fae27db33b1a91895832d43ff9f36c6975d416fe8ca75ac3
    win-64: 0330a1a7629629d74acdf2d60b6a18e7691b47b25e14fa6b1f65fc31cc302951
  channels:
  - url: conda-forge
    used_env_vars: []
  platforms:
  - linux-64
  - osx-arm64
  - osx-64
  - win-64
  sources:
  - environment.yml
package:
- name: ca-certificates
  version: 2025.10.5
  manager: conda
  platform: linux-64
  dependencies:
    __unix: ''
  url: https://conda.anaconda.org/conda-forge/noarch/ca-certificates-2025.10.5-hbd8a1cb_0.conda
  hash:
    md5: f9e5fbc24009179e8b0409624691758a
    sha256: 3b5ad78b8bb61b6cdc0978a6a99f8dfb2cc789a451378d054698441005ecbdb6
  category: main
  optional: false
- name: ca-certificates
  version: 2025.10.5
  manager: conda
  platform: osx-64
  dependencies:
    __unix: ''
  url: https://conda.anaconda.org/conda-forge/noarch/ca-certificates-2025.10.5-hbd8a1cb_0.conda
  hash:
    md5: f9e5fbc24009179e8b0409624691758a
    sha256: 3b5ad78b8bb61b6cdc0978a6a99f8dfb2cc789a451378d054698441005ecbdb6
  category: main
  optional: false
- name: ca-certificates
  version: 2025.10.5
  manager: conda
  platform: osx-arm64
  dependencies:
    __unix: ''
  url: https://conda.anaconda.org/conda-forge/noarch/ca-certificates-2025.10.5-hbd8a1cb_0.conda
  hash:
    md5: f9e5fbc24009179e8b0409624691758a
    sha256: 3b5ad78b8bb61b6cdc0978a6a99f8dfb2cc789a451378d054698441005ecbdb6
  category: main
  optional: false
- name: ca-certificates
  version: 2025.10.5
  manager: conda
  platform: win-64
  dependencies:
    __win: ''
  url: https://conda.anaconda.org/conda-forge/noarch/ca-certificates-2025.10.5-h4c7d964_0.conda
  hash:
    md5: e54200a1cd1fe33d61c9df8d3b00b743
    sha256: bfb7f9f242f441fdcd80f1199edd2ecf09acea0f2bcef6f07d7cbb1a8131a345
  category: main
  optional: false
```

## References

- <https://github.com/conda/conda-lock/blob/v3.0.4/conda_lock/lockfile/v1/models.py>

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

<!-- links -->
