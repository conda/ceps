# CEP XXXX - Structure of installed conda environments

<table>
<tr><td> Title </td><td> Structure of installed conda environments </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Jaime Rodríguez-Guerra &lt;jaime.rogue@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> May 9, 2025</td></tr>
<tr><td> Updated </td><td> May 10, 2025</td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
</table>

## Abstract

This CEP describes the structure of conda environments on disk.

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
- `./{name}-{version}-{build-string}.json` files: Serialized [`PrefixRecord`](https://github.com/conda/conda/blob/efd8ac2a991abc5a133724a064928922cb208dbe/conda/models/records.py#L606) contents (or equivalent) for each installed conda package. The following rules apply:
  - It MUST be named as a CEP 26 "distribution string" (sans subdir), with the three fields matching the corresponding keys in the JSON file. 
  - The serialized `PrefixRecord` information SHOULD match the relevant fields in the most up-to-date repodata information available for the package (`depends` and `constrains` are of particular importance due to repodata patching). This is generally the channel's `repodata.json`, but it MAY also be an alternative source like the serialized metadata in a lockfile. The package's `info/index.json` MAY be used as a fallback if no other sources are available.

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

On Windows, the expected directory structure is:

- `./Lib/`: `.lib` files.
- `./Library/`: Unix-style contents, as above.
- `./Scripts/`: Executables (`.exe`, `.bat`) and DLLs.
- Some binaries might be present in the root level, like `python.exe`.

Within these directories, there are some special paths that conda clients SHOULD handle in a specific way:

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

- `pre-link`: Executed before a package is installed/ linked. Deprecated; conda clients MAY ignore them.
- `post-link`: Executed after a package is installed/ linked.
- `pre-unlink`: Executed before a package is removed / unlinked.
- `post-unlink`: Executed before a package is removed / unlinked.

Execution is performed in topological order. The conda clients SHOULD export these environment variables for the scripts to use:

- `ROOT_PREFIX`: Path to the conda client installation root, when applicable.
- `PREFIX`: Path to the environment where the package is installed.
- `PKG_NAME`: Name of the package.
- `PKG_VERSION`: Version of the package.
- `PKG_BUILDNUM`: Build number of the package.

### Top-level `condarc` file

This can be used to configure behavior of the conda client performing operations on this environment. The following locations are recognized as valid configuration sources.

- `./.condarc`
- `./condarc`
- `./condarc.d/*.yml`
- `./condarc.d/*.yaml`

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
