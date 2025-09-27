# CEP XXXX - Contents of conda packages

<table>
<tr><td> Title </td><td> CEP XXXX - Contents of conda packages </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Jaime Rodríguez-Guerra &lt;jaime.rogue@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> Sep 27, 2025</td></tr>
<tr><td> Updated </td><td> Sep 27, 2025</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/133 </td></tr>
<tr><td> Implementation </td><td> N/A </td></tr>
</table>

## Abstract

This CEP describes the contents of conda packages, regardless of how they are compressed and distributed.

## Motivation

The motivation of this CEP is mostly informative, but will also try to clarify some ambiguous details that should be homogenized across existing implementations.

## Specification

An extracted conda package is a directory that MUST at least include an `info/index.json` file. Other important metadata files SHOULD be included under `info/`.

Additionally, the package directory MAY contain any number of files in any subdirectories.
Some locations MAY receive special handling by conda clients.

### `info/` directory

This special directory contains all the metadata necessary to provide a functional conda package.

Build tools MUST NOT package arbitrary files in this directory.

#### `./info/index.json`

Required.

This file contains essential metadata about the package, such as its name, version or dependencies. The contents of this file MAY be used to populate the `repodata.json` files.

This file MUST conform to the following schema:

- `name: str`. Lowercased name of the package. It MUST comply with [CEP 26](./cep-0026.md).
- `version: str`. Normalized package version. It MUST comply with [CEP XX (Version strings)](https://github.com/conda/ceps/pull/132).
- `build: str`. A string that helps disambiguate different variant builds of the same package version. It MUST comply with [CEP 26](./cep-0026.md). It SHOULD contain the `build_number` field at the end of the string, preceded by an underscore `_`. It MAY contain the hexadecimal string of the SHA1-hash of the key-sorted dictionary provided in `./info/hash_input.json`, preceded by `h`, usually trimmed to the first seven characters.
- `build_number: int`. A non-negative integer representing the build number of the package.
- `depends: list[str]`. Dependencies the package requires at runtime. Each string MUST be a valid `MatchSpec` positional string, as defined in [CEP XX (MatchSpec)](https://github.com/conda/ceps/pull/82).
- `constrains: list[str]`. Dependencies the package is compatible with at runtime. These are not required, but if present, they must match the specifier. Each string MUST be a valid `MatchSpec` positional string, as defined in [CEP XX (MatchSpec)](https://github.com/conda/ceps/pull/82).
- `subdir: str`. The target platform for this package, or `noarch` if platform-agnostic. It MUST comply with [CEP 26](./cep-0026.md).
- `noarch: Literal['generic', 'noarch']`. Optional. When `subdir` is `noarch`, this field indicates the type of `noarch` package. It MUST be one of: `generic`, `python`.
- `timestamp: int`. Starting time of the package build. It MUST be expressed as [Unix time](https://en.wikipedia.org/wiki/Unix_time) in milliseconds.
- `track_features: str`. Space-separated string of unique identifiers.
- `python_site_packages_path: str`. Site-packages path, as introduced in [CEP 20](./cep-0020.md).

Additional keys MAY be present. The following ones are well-known but deprecated:

- `arch: str`. The architecture the package is built for, as returned by Python's `platform.machine()`, or empty in the case of `subdir == 'noarch'`.
- `platform: str`. The OS the package is built for. This is the first component of `subdir`, or empty in the case of `noarch`.
- `features: str`. Space-separated string of identifiers of properties unique to this build.
- `app: dict[str, Any]`. Metadata for Anaconda Navigator.
- `preferred_env: str`.
- `provides_features: dict[str, str]`.
- `requires_features: dict[str, str]`.

#### `./info/paths.json`

Required.

This file MUST list the contents of the package as a list of _path entries_, as described below. It MUST not list the contents of the `info/` folder.

Each _path entry_ MUST be a dictionary that complies to the following schema:

- `_path: str`. The path of the file, relative to the root of the package. It MUST use `/` as a path separator, even on Windows.
- `path_type: Literal['hardlink', 'softlink', 'directory']`. Optional, defaults to `hardlink`. Type of path entry.
- `file_mode: Literal['binary', 'text']`. Optional, defaults to `text`. How to handle the file for prefix replacement.
- `prefix_placeholder: str`. Optional, defaults to an empty string. This is the placeholder string that MAY be replaced at install time with the target location. It MUST use `/` as a path separator, even on Windows.
- `no_link: bool`. Optional, defaults to `false`. Whether to link the file from the cache or force a copy.
- `sha256: str`. The hexadecimal string of SHA256 hash of the file contents. It MUST be a 64 character string containing only characters in the `[a-z0-9]` range. If the path is a softlink, the contents of the target file are hashed.
- `size_in_bytes: int`. The size of the file, in bytes. If the path is a softlink, the size of the target file is reported.

`paths.json` supersedes `info/files`, `info/has_prefix`, and `info/no_link`. If both are present, `paths.json` takes precedence.

#### `./info/hash_input.json`

Required.

A free-form dictionary that maps `str` keys to `str` values. The dictionary MAY be empty.

Its contents MAY be used to generate a hash string that uniquely identifies the package.

#### `./info/about.json`

Optional.

A dictionary that maps `str` keys to arbitrary values.

The contents of this file usually include the `about` section of the originating recipe for the package, plus metadata about the context of the build process. The following keys SHOULD be included and, if present, they MUST conform to the proposed schema:

- `channels: list[str]`. Conda channels used to solve the build and test environments.
- `description: str`. A longer form description of the package.
- `dev_url: str`. URL pointing to the development website (often a repository) of the package.
- `doc_url: str`. URL pointing to the documentation website of the package.
- `env_vars: dict[str, str]`. Allow-listed environment variables set during the package build.
- `extra: dict[str, Any]`: A free-form dictionary of arbitrary metadata.
- `home: str`. URL pointing to the homepage of the package.
- `license: str`. SPDX license identifier for the package.
- `summary: str`: A short summary of the package (usually one sentence).

These keys are commonly found, but are now considered deprecated:

- `license_file: str | list[str]`: Paths to the license files, relative to the `recipe/` directory.
- `license_family: str`. Use `license` instead.
- `tags: list[str]`.
- `identifiers: list[str]`.
- `keywords: list[str]`.

Additional keys MAY be allowed. Some examples include vendor information such as the conda-build and conda versions used at build time, along with the packages present in the conda `base` environment (`conda_build_version`, `conda_version`, `root_pkgs`, respectively).

#### `./info/link.json`

Optional.

A dictionary containing important metadata for installation (linking) operations. Its contents MUST conform to the following schema:

- `package_metadata_version: int`. Version of this file. The only known value is `1`.
- `noarch: dict[str, Any]`. A dictionary describing the `noarch` configuration of the package. Its keys MUST conform to:
  - `type: Literal["generic", "python"]`. Type of `noarch` package.
  - `entry_points: list[str]`. If `type == "python"`, this key MUST list the console entry points of the Python package, as a list of strings with syntax `{executable-name}={dotted-import-path}:{function-name}` (for example `bsdiff4 = bsdiff4.cli:main_bsdiff4`).
- `preferred_env: dict[str, str]`. Deprecated, optional. It MUST have two keys: `name: str` (name of the preferred environment) and `executable_paths: list[str]` (list of preferred executable paths in that environment).

#### `./info/licenses/`

Optional.

Directory containing all the license files that apply to the distributed code and resources.

It MAY be empty or absent if the recipe doesn't ship any installable files.

#### `./info/recipe/`

Optional.

Directory containing the recipe used to build the package. It SHOULD contain the original and rendered versions of the recipe file, along with the files necessary to run the build again.

It SHOULD contain a file specifying the licensing details of the recipe itself.

#### `./info/test/`

Optional.

Directory containing the scripts and files needed to test the package.

#### `./info/git`

Optional.

If the package sources come from a `git` repository and the `git` executable is available, this file will include information about the status of the cloned repository. Namely, the output of:

- `git log -n1`
- `git describe --tags`
- `git status`

#### `./info/files`

Deprecated.

Lists all files that are part of the package itself, 1 per line. All of these files need to get linked into the environment. Any files in the package that are not listed in this file are not linked when the package is installed. The directory delimiter for the files in info/files should always be "/", even on Windows. This matches the directory delimiter used in the tarball.

#### `./info/has_prefix`

Deprecated. Optional.

Lists all files that contain a hard-coded build prefix or placeholder prefix, which needs to be replaced by the install prefix at installation time.

Each line of this file should be either a path, in which case it is considered a text file with the default placeholder `/opt/anaconda1anaconda2anaconda3`, or a space-separated list of `placeholder`, `mode`, and `path`, where:

- Placeholder is the path of the build prefix which needs to be replaced at install time.
- Mode is either `text` or `binary`.
- Path is the relative path of the file to be updated.

#### `./info/no_link`

Deprecated. Optional.

Lists all files that cannot be linked into environments and are copied instead.

### Recommendations for installed files

On Unix filesystems, packages generally follow a subset of the [Filesystem Hierarchy Standard](https://en.wikipedia.org/wiki/Filesystem_Hierarchy_Standard):

- `./bin/`: executables and scripts.
- `./etc/`: configuration files.
- `./include/`: header files.
- `./lib/`: dynamic and static libraries.
- `./share/`: miscellaneous data contents.

On Windows, the expected directory structure is a bit different due to how Python (and other interpreted languages) are organized in this operating system:

- `./Library/`, uses the same directories as the Unix structure listed above. Most packages will populate this directory.
- Python interpreters and Python-related packages stay in the root-level:
  - `./DLLs/`: Compiled Python extensions (`.pyd`)
  - `./include/`: Python development headers (`.h`).
  - `./Lib/`: Equivalent to `./lib/pythonX.Y/site-packages` on Unix.
  - `./libs/`: Python `.lib` files.
  - `./Scripts/`: Python entry points (`.exe` trampolines and the corresponding `-script.py` files).
  - `./Tools/`: Miscellaneous Python scripts.
  - `./python*.(exe|dll|pdb)`: The Python interpreter executables and libraries.
- Other interpreted languages might also populate the root-level directly, specially if they rely on `noarch: generic` packages. Some examples:
  - Node.js places its executables in the root level, and leaves everything else under `./node_modules/`.
  - R installs to `./lib/R/` using a Unix-style directory structure, but also places some executables in `./Scripts/`.
  - Ruby installs directly to the root level, using a Unix-style directory structure.

### `etc/conda/*.d` directories

This special directory stores configuration files that can modify the behavior of the conda client at runtime. Packages are allowed to ship files under this directory.

The following files and directories MUST be handled by the conda client:

- `./etc/conda/env_vars.d/`: Directory containing JSON documents, each providing a dictionary that maps strings to strings, meant to be exported as environment variables on environment activation, and unset on deactivation.
- `./etc/conda/activate.d/`: Directory containing shell scripts, meant to be executed on environment activation.
- `./etc/conda/deactivate.d/`: Directory containing shell scripts, meant to be executed on environment deactivation.

### Pre- and post-link/unlink scripts

The `bin/` and `Scripts/` directories usually contain executables populated by the packages themselves. There are four special paths that MAY be handled by conda clients. For files named like `.{package-name}-{action}.{extension}`, where `{package-name}` corresponds to the package name and `{extension}` is either `sh` (Unix) or `bat` (Windows), there are four possible `{action}` values and associated behaviors:

- `pre-link`: Executed before a package is installed / linked.
- `post-link`: Executed after a package is installed / linked.
- `pre-unlink`: Executed before a package is removed / unlinked.
- `post-unlink`: Executed after a package is removed / unlinked. Deprecated; MAY be ignored.

These scripts should be avoided whenever possible. If they are indeed necessary, these rules apply:

- They MUST NOT write to stdout, but they MAY write to `$CONDA_PREFIX/.messages.txt`, whose contents SHOULD be reported after the conda client completes all actions.
- They MUST NOT touch anything other than the files being installed.
- They MUST NOT depend on any installed or to-be-installed conda packages.
- They SHOULD depend only on standard system tools such as `rm`, `cp`, `mv`, and `ln`.

### `Menu/*.json` files

These are defined by the `menuinst` standards, introduced in [CEP 11](./cep-0011.md).

### Additional restrictions

The `conda-meta/` directory is reserved for conda environments and MUST NOT be populated by conda packages directly.

`./info/repodata_record.json` MAY be written at extraction time by conda client tools. It MUST NOT be present in the distributed artifacts.

## Rationale

Some keys or files have been proposed for formal deprecation because they are not used widely, and as a result were not adapted from `conda-build` to `rattler-build`.

## References

- <https://docs.conda.io/projects/conda-build/en/latest/resources/package-spec.html#package-metadata>
- <https://rattler.build/latest/package_spec/>
- <https://github.com/conda/ceps/pull/124#discussion_r2083137907>
- [`Library/` conventions on Windows](https://github.com/ContinuumIO/anaconda-issues/issues/440)

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
