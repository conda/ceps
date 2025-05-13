# CEP XXXX - Management and structure of conda environments

<table>
<tr><td> Title </td><td> Management and structure of conda environments </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Jaime Rodríguez-Guerra &lt;jaime.rogue@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> May 9, 2025</td></tr>
<tr><td> Updated </td><td> May 10, 2025</td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
</table>

## Abstract

This CEP describes the lifecycle of conda environments and their structure.

## Specification

A conda environment is defined as a directory that contains, at least, a `conda-meta/history` file.

### Internal metadata: `conda-meta/`

This directory stores metadata about the environment and installed packages. It MUST be considered protected and MUST NOT be populated directly by package contents.

This following files MUST be recognized by conda clients:

- `./history`: Plain text file. It SHOULD record the operations performed during the lifetime of the environment, but MAY be empty. Its existence marks its parent directory as a valid conda environment.

    <details>

    <summary>Structure of <code>conda</code>'s <code>history</code> file</summary>

    `conda`'s `history` file is a succession of the following blocks, with each block representing an action on the conda environment:

    ```text
    ==> YYYY-MM-DD HH:MM:SS <==
    # cmd: /path/to/conda/executable subcommand arguments ...
    # conda version: MAJOR.MINOR.PATCH
    +channel/subdir::package_being_linked-version-build_string
    +channel/subdir::package2_being_linked-version-build_string
    +channel/subdir::package3_being_linked-version-build_string
    +channel/subdir::package4_being_linked-version-build_string
    -channel/subdir::package_being_unlinked-version-build_string
    -channel/subdir::package2_being_unlinked-version-build_string
    # (update|remove) specs: ['list', 'of', 'specs']
    ```

    </details>
- `./{name}-{version}-{build-string}.json` files: Serialized [`PrefixRecord`](https://github.com/conda/conda/blob/efd8ac2a991abc5a133724a064928922cb208dbe/conda/models/records.py#L606) contents (or equivalent) for each installed conda package.

The `conda-meta/` directory MAY also present additional files that condition the behavior of the conda clients:

- `./frozen`. As described in [CEP 22](./cep-0022.md).
- `./state`. JSON document that provides a dictionary with a single key, `env_vars`, whose value is a dictionary that maps strings to strings. These are environment variable names and their values, respectively. conda clients SHOULD parse this document and export the environment variables on environment activation.

### General contents

The rest of the environment is generally populated by the contents of its installed packages, after extraction and linking. As a result, the structure is arbitrary and determined by which packages are installed. That said, there are some conventions that SHOULD be followed by package builders so the environments are populated consistently.

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

Regardless the platform, within these directories there are some special paths that conda clients SHOULD handle in a specific way:

- `./etc/conda/*.d` directories
- `./(bin|Scripts)/.{package-name}-{action}.{extension}` scripts
- `./condarc` configuration files

#### `etc/conda/*.d` directories

This special directory stores configuration files that can modify the behavior of the conda client at runtime. Packages are allowed to ship files under this directory.

The following files and directories MUST be handled by the conda client:

- `./env_vars.d/`: Directory containing JSON documents, each providing a dictionary that maps strings to strings, which are understood as environment variables. The JSON documents SHOULD be loaded alphabetically, with later documents overriding earlier ones. These environment variables SHOULD be exported on environment activation. When both `env_vars.d/` and `conda-meta/state` are present, the latter is loaded last and can override the previously defined variables.
- `./activate.d/`: Directory containing shell scripts. They SHOULD be executed on environment activation, in alphabetical order.
- `./deactivate.d/`: Directory containing shell scripts. They SHOULD be executed on environment deactivation, in reverse alphabetical order.

### Pre- and post-link/unlink scripts

The `bin/` and `Scripts/` directories usually contain executables populated by the packages themselves. There are four special paths that SHOULD be handled by conda clients. For files named like `.{package-name}-{action}.{extension}`, where `{package-name}` corresponds to the package name and `{extension}` is either `sh` (Unix) or `bat` (Windows), there are four possible `{action}` values and associated behaviors:

- `pre-link`: Executed before a package is installed / linked. Deprecated; conda clients SHOULD ignore them.
- `post-link`: Executed after a package is installed / linked.
- `pre-unlink`: Executed before a package is removed / unlinked.
- `post-unlink`: Executed after a package is removed / unlinked. Deprecated; conda clients SHOULD ignore them.

Execution is performed in topological order. The conda clients SHOULD export these environment variables for the scripts to use:

- `ROOT_PREFIX`: Path to the conda client installation root, when applicable.
- `PREFIX`: Path to the environment where the package is installed.
- `PKG_NAME`: Name of the package.
- `PKG_VERSION`: Version of the package.
- `PKG_BUILDNUM`: Build number of the package.

### Top-level `condarc` files

This can be used to configure behavior of the conda client performing operations on this environment. The following locations are recognized as valid configuration sources.

- `./.condarc`
- `./condarc`
- `./condarc.d/*.yml`
- `./condarc.d/*.yaml`

## Management of a conda environment

### Creating a conda environment

An empty directory `$CONDA_PREFIX` can be turned into a conda environment by creating an empty `conda-meta/history` file. The conda client MAY register this location into a central registry of environments, such as `~/.conda/environments.txt`.

The command used to create that environment MAY be recorded in `conda-meta/history`, along with the version, timestamp and details of the transaction.

### Installing packages

For each package to be installed, assuming it has been already downloaded and extracted:

- For regular (non-`noarch: python`) packages, place the contents of the artifact into `$CONDA_PREFIX`.
  - If the file contains a prefix placeholder, replace it with the value of `$CONDA_PREFIX` and copy the file.
  - Otherwise, place the file in `$CONDA_PREFIX`. Tools MAY offer settings to configure this operation (e.g. prefer hardlinks to copies).
- `noarch: python` packages follow some extra rules. In particular, they no longer follow a 1:1 correspondence between the path in the artifact and the linked path in `$CONDA_PREFIX`. The target path depends on variables like the Python version, OS and Python ABI modes. Details are discussed in [CEP 20](./cep-0020.md).

Once linked, the package metadata MUST be recorded at `$CONDA_PREFIX/conda-meta/{name}-{version}-{build}.json`. This document serves as a manifest of all the files that this package brought into the environment, plus some additional metadata to handle its behavior during the environment lifecycle. It MUST include this information (equivalent to a serialized `PrefixRecord` object):

```js
{
    "build": str, // build string
    "build_number": int,
    "channel": str, // URL to source channel, no subdir
    "constrains": list[str], // str must be a "conda-build form" match spec
    "depends": list[str], // str must be a "conda-build form" match spec
    "extracted_package_dir": str, // absolute path to extracted contents
    "files": list[str], // list of paths in artifact, relative to $CONDA_PREFIX, forward-slash normalized
    "fn": str, // {name}-{version}-{build}.{extension}
    "license": str, // SPDX expression preferred
    "link": { // How the package was linked into the prefix
        "source": str, // original path
        "type": (1|2|3|4), // hardlink, softlink, copy, directory
    },
    "md5": str, // 32-char hex string
    "name": str, // package name
    "noarch": "python", // optional, values: python, generic
    "package_tarball_full_path": str, // absolute path to artifact
    "package_type": "noarch_python", // optional, values: noarch_python, noarch_generic.
    "paths_data": { // Artifact contents + generated files in $CONDA_PREFIX
        "paths": [  // one dict per file:
            {
                "_path": str, // relative path of file to $CONDA_PREFIX, forward-slash normalized
                "file_mode": str, // optional; one of 'text' or 'binary'
                "no_link": bool, // optional, whether to force copy or allow link
                "path_type": str, // one of: softlink, hardlink, directory; MAY also be one of generated types: pyc_file, unix_python_entry_point, windows_python_entry_point_script, windows_python_entry_point_exe, linked_package_record
                "prefix_placeholder": str, // optional; to be replaced with $CONDA_PREFIX
                "sha256": str, // optional if generated, 64-char hex string of file in cache
                "sha256_in_prefix": str, // optional if generated, 64-char hex string of file in prefix (after placeholder has been replaced)
                "size_in_bytes": int // optional, if generated
            },
            ...
            ]
        "paths_version": 1
    },
    "requested_spec": str, // MatchSpec asked by user; use "None" if not requested (transitive)
    "sha256": str, // 64-char hex string
    "size": int, // in bytes
    "subdir": str, // one of KNOWN_SUBDIRS
    "timestamp": int, // in ms
    "url": str, // download URL of the package
    "version": str, // package version
}
```

The serialized `PrefixRecord` information SHOULD match the relevant fields in the most up-to-date repodata information available for the package (`depends` and `constrains` are of particular importance due to repodata patching). This is generally the channel's `repodata.json`, but it MAY also be an alternative source like the serialized metadata in a lockfile. The package's `info/index.json` MAY be used as a fallback if no other sources are available.

While linking paths into their targets, the conda client might run into clobbering conflicts (two or more packages wanting to write to the same path). Tools SHOULD at least warn the user about the conflicts and provide ways to handle the situation.

Once all packages have been linked, the `post-link` scripts SHOULD be executed, as described above.

### Removing a package

Removing a package from the environment SHOULD follow these instructions:

1. Execute the relevant `pre-unlink` scripts.
2. Remove all the files recorded in its `conda-meta/*.json` file (under `paths_data`).
3. Remove its `conda-meta/*.json` record.
4. If there were clobbering conflicts, restore the relevant path from the clobbered sources.

### Removing an environment

Once an environment contains no packages, the conda client MAY remove it. This process involves clearing the `conda-meta/` folder and any `condarc` files, and deregistering the environment path from the central manifest, if applicable (e.g. `~/.conda/environments.txt`). If there were any additional files in the environment directory, the conda client SHOULD report that to the user and offer to leave them in place or to proceed and clear all the contents.

## References

- [`Library/` conventions on Windows](https://github.com/ContinuumIO/anaconda-issues/issues/440)

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
