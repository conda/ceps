# CEP XXXX - Management and structure of conda environments

<table>
<tr><td> Title </td><td> Management and structure of conda environments </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Jaime Rodríguez-Guerra &lt;jaime.rogue@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> May 9, 2025</td></tr>
<tr><td> Updated </td><td> Sep 27, 2025</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/124 </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
</table>

## Abstract

This CEP describes the lifecycle of conda environments and their structure.

## Specification

A conda environment is defined as a directory that contains, at least, a `conda-meta/history` file.

### Internal metadata: `conda-meta/`

This directory stores metadata about the environment and installed packages. It MUST be considered protected and MUST NOT be populated directly by package contents.

This following files MUST be recognized by conda clients:

#### `./conda-meta/history`

Required.

Plain text file. Its existence MUST mark its parent directory as a valid conda environment.

It SHOULD record the operations performed during the lifetime of the environment, but MAY be empty. If populated, a `history` file MUST be composed of one or more _action blocks_. Each action block MUST follow this syntax:

```text
==> YYYY-MM-DD HH:MM:SS <==
# cmd: /path/to/conda/executable subcommand arguments ...
# name-of-tool version: MAJOR.MINOR.PATCH
+channel/subdir::name_of_linked_package1-version-build_string
+channel/subdir::name_of_linked_package2-version-build_string
+channel/subdir::name_of_linked_package3-version-build_string
+channel/subdir::name_of_linked_package4-version-build_string
-channel/subdir::name_of_unlinked_package1-version-build_string
-channel/subdir::name_of_unlinked_package2-version-build_string
# (update|remove) specs: ['spec1', 'spec2', 'spec3', 'spec4']
```

#### `./conda-meta/{name}-{version}-{build-string}.json`

Required.

This document serves as a manifest of all the files that each installed package brought into the environment, plus some additional metadata to handle its behavior during the environment lifecycle.

It MUST be a JSON document that ships a dictionary conforming to this schema:

- `arch: str | None`. Deprecated, as defined in [CEP PR#133](https://github.com/conda/ceps/pull/133).
- `build: str`. Build string, as defined in [CEP PR#133](https://github.com/conda/ceps/pull/133).
- `build_number: int`. Build number, as defined in [CEP PR#133](https://github.com/conda/ceps/pull/133).
- `channel: str`: URL to source channel, without subdir, as defined in [CEP 26](./cep-0026.md).
- `constrains: list[str]`. Runtime constraints, as defined in [CEP PR#133](https://github.com/conda/ceps/pull/133).
- `depends: list[str]`. Runtime requirements, as defined in [CEP PR#133](https://github.com/conda/ceps/pull/133).
- `extracted_package_dir: str`: Absolute path to extracted contents of the artifact.
- `files: list[str]`: list of installed paths that are owned by this artifact, relative to `$CONDA_PREFIX`, forward-slash normalized. It MUST include generated files (e.g. `*.pyc` bytecode files).
- `fn: str`. Filename of compressed artifact, as defined in [CEP 26](./cep-0026.md).
- `license: str`. SPDX license expression, as defined in [CEP PR#133](https://github.com/conda/ceps/pull/133).
- `link: dict[str, Any]`: How the package was linked into the prefix. It MUST only allow two keys:
  - `source: str`: The path of the extracted package directory.
  - `type: Literal[1, 2, 3, 4]`: Type of linkage (1 = hardlink, 2 = softlink, 3 = copy, 4 = directory).
- `md5: str`: Hexadecimal string of MD5 hash, as defined in [CEP PR#133](https://github.com/conda/ceps/pull/133).
- `name: str`: Lowercase name of the package, as defined in [CEP 26](./cep-0026.md).
- `noarch: Literal['generic', 'python']`: Optional. Noarch type, as defined in [CEP PR#133](https://github.com/conda/ceps/pull/133).
- `package_tarball_full_path: str`: Absolute path to downloaded artifact (compressed).
- `paths_data: dict[str, Any]`: Metadata about the artifact installed contents, which includes the artifact distributed files, and the generated files at install time. It MUST be a mapping with two keys:
  - `paths: list[dict[str, Any]`: Information about installed files. Extends [CEP PR#133](https://github.com/conda/ceps/pull/133)'s `paths.json` with some extra details:
    - `_path": str`: Relative path of file within `$CONDA_PREFIX`, forward-slash normalized.
    - `file_mode": Literal['text', 'binary']`: Optional, defaults to `text`. How to perform prefix replacement.
    - `no_link": bool`: Optional, defaults to `false`. Whether to force copy or allow link.
    - `path_type": Literal['softlink', 'hardlink', 'directory', 'pyc_file', 'unix_python_entry_point', 'windows_python_entry_point_script', 'windows_python_entry_point_exe', 'linked_package_record']`: Optional, defaults to `hardlink`. How the file was written to `$CONDA_PREFIX`, which includes what type of generated file it is, if applicable.
    - `prefix_placeholder": str`: Optional. String that MUST be replaced with the target location at `$CONDA_PREFIX`.
    - `sha256": str`: Optional if the file is generated. 64-char hex string corresponding to the SHA256 checksum of the original file in cache.
    - `sha256_in_prefix": str`: Optional if generated, 64-char hex string corresponding to the SHA256 checksum of the file as installed in the target prefix. This MAY be different than `sha256` due to prefix replacement.
    - `size_in_bytes": int`: optional, if generated. Size of file, in bytes.
  - `paths_version: int`: Version of this schema. Currently, `1`.
- `platform: str | None`. Deprecated, as defined in [CEP PR#133](https://github.com/conda/ceps/pull/133).
- `requested_spec: str`: Deprecated, use `requested_specs` instead. `MatchSpec` string (as defined in [CEP PR#82](https://github.com/conda/ceps/pull/82)) that led to choosing this package.
- `requested_specs: list[str]`: List of `MatchSpec` strings (as defined in [CEP PR#82](https://github.com/conda/ceps/pull/82)) that led to choosing this package.
- `sha256: str`: Hexadecimal string of SHA256 hash, as defined in [CEP PR#133](https://github.com/conda/ceps/pull/133).
- `size: int`: Size, in bytes, of compressed artifact, as defined in [CEP PR#133](https://github.com/conda/ceps/pull/133).
- `subdir: str`: Subdir string, as defined in [CEP PR#133](https://github.com/conda/ceps/pull/133).
- `timestamp: int`: Moment the package build started, as defined in [CEP PR#133](https://github.com/conda/ceps/pull/133).
- `url: str`: Direct URL to download the artifact. It SHOULD be the result of joining the `channel` URL plus `subdir` (or its `base_url` field as defined in [CEP 15](./cep-0015.md)) plus the `fn` field.
- `version: str`: Package version, as defined in [CEP PR#132](https://github.com/conda/ceps/pull/132).

The fields above that also appear in [CEP PR#133](https://github.com/conda/ceps/pull/133)'s `info/index.json` MUST match the relevant fields in the most up-to-date repodata information available for the package at install time (`depends` and `constrains` are of particular importance due to repodata patching).
This is generally the channel's `repodata.json`, but it MAY also be an alternative source like the serialized metadata in a lockfile. The package's `info/index.json` SHOULD be used as a fallback if no other sources are available.

Additional keys MAY be present in the file and MUST be ignored if not recognized.

#### `./conda-meta/frozen`

Optional.

Empty file or JSON document that MUST follow [CEP 22](./cep-0022.md).

#### `./conda-meta/state`

Optional.

JSON document that MUST provide a dictionary with a single key, `env_vars`, whose value is a dictionary that maps strings to strings. These are environment variable names and their values, respectively.

conda clients SHOULD parse this document and export the environment variables on environment activation, and unset them on deactivate.

### General contents

The rest of the environment is generally populated by the contents of its installed packages, after extraction and linking. As a result, the structure is arbitrary and determined by which packages are installed. Refer to [CEP XX (Contents of conda packages)](https://github.com/conda/ceps/pull/133) for more details on which conventions to follow.

Packages MAY include files in some special paths that conda clients SHOULD handle in a specific way:

- `./etc/conda/*.d` directories
- `./(bin|Scripts)/.{package-name}-{action}.{extension}` scripts
- `./condarc` configuration files

#### `etc/conda/*.d` directories

The following files and directories MUST be handled by the conda client:

- `./etc/conda/env_vars.d/`: Directory containing JSON documents, each providing a dictionary that maps strings to strings, which are understood as environment variables. The JSON documents SHOULD be loaded alphabetically, with later documents overriding earlier ones. These environment variables SHOULD be exported on environment activation, and unset on deactivation. When both `env_vars.d/` and `conda-meta/state` are present, the latter is loaded last and can override the previously defined variables.
- `./etc/conda/activate.d/`: Directory containing shell scripts. They SHOULD be executed on environment activation, in alphabetical order.
- `./etc/conda/deactivate.d/`: Directory containing shell scripts. They SHOULD be executed on environment deactivation, in reverse alphabetical order.

### Pre- and post-link/unlink scripts

conda clients SHOULD execute scripts located under `./bin/` (Unix) or `./Scripts/` (Windows) with the syntax `.{package-name}-{action}.{extension}`, where `{package-name}` corresponds to the package name, `{extension}` is either `sh` (Unix) or `bat` (Windows), and `{action}` being one of:

- `pre-link`: Executed before the corresponding package is installed / linked.
- `post-link`: Executed after the corresponding package is installed / linked.
- `pre-unlink`: Executed before the corresponding package is removed / unlinked.
- `post-unlink`: Executed after the corresponding package is removed / unlinked. Deprecated; conda clients SHOULD ignore them.

These scripts should be avoided whenever possible. If they are indeed necessary, these rules apply:

- They MUST NOT write to stdout, but they MAY write to `$CONDA_PREFIX/.messages.txt`, whose contents SHOULD be reported after the conda client completes all actions.
- They MUST NOT touch anything other than the files being installed.
- They MUST NOT depend on any installed or to-be-installed conda packages.
- They SHOULD depend only on standard system tools such as `rm`, `cp`, `mv`, and `ln`.

Execution SHOULD be performed in topological order. The conda client SHOULD export these environment variables for the scripts to use:

- `ROOT_PREFIX`: Path to the conda client installation root, when applicable.
- `PREFIX`: Path to the environment where the package is installed.
- `PKG_NAME`: Name of the package.
- `PKG_VERSION`: Version of the package.
- `PKG_BUILDNUM`: Build number of the package.

### Top-level `condarc` files

Environments MAY includes files in these locations which affect the behavior of the conda client performing operations on this environment. The following locations are recognized as valid configuration sources.

- `./.condarc`
- `./condarc`
- `./condarc.d/*.yml`
- `./condarc.d/*.yaml`

## Management of a conda environment

### Creating a conda environment

An empty directory `$CONDA_PREFIX` can be turned into a conda environment by creating an empty `conda-meta/history` file. The conda client MAY register this location into a central registry of environments, such as `~/.conda/environments.txt`.

The command used to create that environment MAY be recorded in `conda-meta/history`, along with the version, timestamp and details of the transaction.

### Installing packages

For each package to be installed, conda clients:

1. SHOULD download or copy the artifact to the cache location using the "filenames" syntax described in [CEP 26](./cep-0026.md).
2. SHOULD, if available, verify the integrity of the artifact with its checksum (`sha256` is preferred over `md5`).
3. MUST extract and aggregate the artifact to a central location. The extracted directory SHOULD be named as a distribution string (without subdir), as described in [CEP 26](./cep-0026.md).
4. SHOULD write an `./info/repodata_record.json` file in the extracted directory, whose contents MUST be populated with one of:
   - The `RepodataRecord` information available in the lockfile, if relevant.
   - The `RepodataRecord` information available in the repodata source, if relevant.
   - The contents of `./info/index.json`, as a fallback.

Once extracted, the packages MUST be installed in the target prefix `$CONDA_PREFIX` by following these steps:

1. Execute the relevant `pre-link` scripts.
2. Place the contents in the `$CONDA_PREFIX`:
   - For regular (non-`noarch: python`) packages, place the contents of the artifact into `$CONDA_PREFIX`.
     - If the file contains a prefix placeholder, replace it with the value of `$CONDA_PREFIX` and copy the file.
     - Otherwise, place the file in `$CONDA_PREFIX`. Tools MAY offer settings to configure this operation (e.g. prefer hardlinks to copies).
   - `noarch: python` packages follow some extra rules. In particular, they no longer follow a 1:1 correspondence between the path in the artifact and the linked path in `$CONDA_PREFIX`. The target path depends on variables like the Python version, OS and Python ABI modes. Details are discussed in [CEP 17](./cep-0017.md) and [CEP 20](./cep-0020.md)
3. Execute the relevant `post-link` scripts.
4. Record the package metadata at `$CONDA_PREFIX/conda-meta/{name}-{version}-{build}.json`, as instructed above.

While linking paths into their targets, the conda client MAY run into clobbering conflicts (two or more packages wanting to write to the same path). Tools SHOULD at least warn the user about the conflicts and provide ways to handle the situation.

### Removing a package

Removing a package from the environment SHOULD follow these instructions:

1. Execute the relevant `pre-unlink` scripts.
2. Remove all the files recorded in its `conda-meta/*.json` file (under `paths_data`).
3. Legacy only. Execute the relevant `post-unlink` scripts.
4. Remove its `conda-meta/*.json` record.
5. If there were clobbering conflicts, restore the relevant path from the clobbered sources.

### Removing an environment

Once an environment contains no packages, the conda client MAY remove it. This process involves clearing the `conda-meta/` folder and any `condarc` files, and deregistering the environment path from the central manifest, if applicable (e.g. `~/.conda/environments.txt`). If there were any additional files in the environment directory, the conda client SHOULD report that to the user and offer to leave them in place or to proceed and clear all the contents.

## References

- [Adding pre-link, post-link, and pre-unlink scripts](https://docs.conda.io/projects/conda-build/en/stable/resources/link-scripts.html)

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
