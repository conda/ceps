# A new recipe format – part 2 - the allowed keys & values

<table>
<tr><td> Title </td><td> A new recipe format – part 2 - the allowed keys & values </td>
<tr><td> Status </td><td> Accepted</td></tr>
<tr><td> Author(s) </td><td> Wolf Vollprecht &lt;wolf@prefix.dev&gt;</td></tr>
<tr><td> Created </td><td> May 23, 2023</td></tr>
<tr><td> Updated </td><td> Jan 22, 2024</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda-incubator/ceps/pull/56 </td></tr>
<tr><td> Implementation </td><td>https://github.com/prefix-dev/rattler-build</td></tr>
</table>

## Abstract

We propose a new recipe format that is heavily inspired by conda-build. The main
change is a pure YAML format without arbitrary Jinja or comments with semantic
meaning.

This document builds upon CEP 13, which defines the YAML syntax for the recipe.
In this CEP, we define the allowed keys and values for the recipe.

## Motivation

The conda-build format is currently under-specified. For the new format, we try to list all values
and types in a single document and document them. This is part of a larger effort (see [CEP-13](/cep-13.md) for the new YAML syntax).

## History

A discussion was started on what a new recipe spec could or should look like.
The fragments of this discussion can be found here:
https://github.com/mamba-org/conda-specs/blob/7b53425caa11357487cba3fa9c7397744edb41f8/proposed_specs/recipe.md
The reasons for a new spec are:

- Make it easier to parse ("pure yaml"). conda-build uses a mix of comments and
  jinja to achieve a great deal of flexibility, but it's hard to parse the
  recipe with a computer
- Iron out some inconsistencies around multiple outputs (`build` vs. `build/script`
  and more)
- Remove any need for recursive parsing & solving
- Cater to needs for automation and dependency tree analysis via a deterministic
  format

## Major differences with conda-build

Outputs and top-level package are mutually exclusive, and outputs have exactly the same structure as top-level keys.
If outputs exist, the top-level keys are 'merged' with the output keys (e.g. for the about section).

# Format

## Schema version

The implicit version of the YAML schema for a recipe is an integer 1.
To discern between the "old" format and the new format, we utilize the file name.
The old format is `meta.yaml` and the new format is `recipe.yaml`.
The version can be explicitly set by adding a `schema_version` key to the recipe.

```yaml
# optional, since implicitly defaults to 1
schema_version: 1 # integer
```

To benefit from autocompletion, and other LSP features in editors, we can add a schema URL to the recipe.

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/prefix-dev/recipe-format/73cd2eed94c576213c5f25ab57adf6d8c83e792a/schema.json
```

## Context section

The context section is a dictionary with key-value pairs that can be used for string interpolation.
The right-hand side of the key-value pair is a scalar (bool, number or string).

The variables can reference other variables from the context section.

> [!NOTE]
> The order of the keys is not enforced by the YAML standard. We expect parsers to parse maps (especially the context section)
> in the order they are defined in the file. However, we do not require this behavior for the recipe to be valid to conform to the YAML standard.
> Given this, implementations need to ensure topological sorting is done before string interpolation.

```yaml
# The context dictionary defines arbitrary key-value pairs for Jinja interpolation
# and replaces the {% set ... %} commands commonly used in recipes
context:
  variable: test
  # note that we can reference previous values, that means that they are rendered in order
  other_variable: test_${{ variable }}
```



## Package section

Required for recipes without outputs section. This is the only required section (for single-output recipes).

```yaml
package:
  # The name of the package
  name: string
  # The version of the package, following the conda version spec
  # Note that versions are always strings (1.23 is _not_ a valid version since it is a `float`. Needs to be quoted.)
  version: string
```

## Build section

```yaml
build:
  # the build number
  number: integer  # defaults to 0

  # the build string. This is usually omitted (can use `${{ hash }}` variable here)
  string: string  # defaults to a build string made from "package hash & build number"

  # A list of Jinja conditions under which to skip the build of this package (they are joined by `or`)
  # What is valid in an `if:` condition is valid
  skip: [list of expressions]

  # whether the package is a noarch package, and if yes, whether it is "generic" or "python"
  # defaults to null ("arch" package)
  noarch: Option<OneOf<"generic" | "python">>

  # script can be a single string or a list of strings
  # if script is a single string and ends with `.sh` or `.bat`, then we interpret it as a file
  script: string | [string] | Script

  # merge the build and host environments (used in many R packages on Windows)
  # was `merge_build_host`
  merge_build_and_host_envs: bool (defaults to false)

  # include files even if they are already in the environment
  # as part of some other host dependency
  always_include_files: [path]

  # do not soft- or hard-link these files, but always copy them was `no_link`
  always_copy_files: [glob]

  variant:
    # Keys to forcibly use for the variant computation (even if they are not in the dependencies)
    use_keys: [string]

    # Keys to forcibly ignore for the variant computation (even if they are in the dependencies)
    ignore_keys: [string]

    # used to prefer this variant less
    # note: was `track_features`
    down_prioritize_variant: integer (negative, defaults to 0)

  # settings concerning only Python
  python:
    # List of strings, where each string follows this format:
    # PythonEntryPoint: `bsdiff4 = bsdiff4.cli:main_bsdiff4`
    entry_points: [PythonEntryPoint]

    # Specifies if python.app should be used as the entrypoint on macOS
    # was `osx_is_app`
    use_python_app_entrypoint: bool (defaults to false)  # macOS only!

    # used on conda-forge, still needed?
    preserve_egg_dir: bool (default false)

    # skip compiling pyc for some files (was `skip_compile_pyc`)
    skip_pyc_compilation: [glob]

  # settings concerning the prefix detection in files
  prefix_detection:
    # force the file type of the given files to be TEXT or BINARY
    # for prefix replacement
    force_file_type:
      # force TEXT file type
      # was `???`
      text: [glob]
      # force binary file type
      # was `???`
      binary: [glob]

    # ignore all or specific files for prefix replacement
    # was `ignore_prefix_files`
    ignore: bool | [path] (defaults to false)

    # whether to detect binary files with prefix or not
    # was `detect_binary_files_with_prefix`
    ignore_binary_files: bool (defaults to true on Unix and (always) false on Windows)

  # settings for shared libraries and executables
  dynamic_linking:
    # linux only, list of rpaths (was rpath)
    rpaths: [path] (defaults to ['lib/'])

    # whether to relocate binaries or not. If this is a list of paths, then
    # only the listed paths are relocated
    binary_relocation: bool (defaults to true) | [glob]

    # Allow linking against libraries that are not in the run requirements
    # (was `missing_dso_whitelist`)
    missing_dso_allowlist: [glob]

    # Allow runpath / rpath to point to these locations outside of the environment
    # (was `runpath_whitelist`)
    rpath_allowlist: [glob]

    # what to do when detecting overdepending
    overdepending_behavior: OneOf<"ignore" | "error"> # (defaults to "error")

    # what to do when detecting overlinking
    overlinking_behavior: OneOf<"ignore" | "error"> # (defaults to "error")

  # REMOVED:
  # pre-link: string (was deprecated for a long time)
  # Whether to include the recipe or not in the final package - should be specified on command line or other config file?
  # noarch_python: bool
  # features: list
  # msvc_compiler: str
  # requires_features: dict
  # provides_features: dict
  # preferred_env: str
  # preferred_env_executable_paths: list
  # disable_pip: bool
  # marked as "still experimental"
  # pin_depends: Enum<"record" | "strict">
  # overlinking_ignore_patterns: [glob]
  # defaults to patchelf (only cudatoolkit is using `lief` for some reason)
  # rpaths_patcher: None
  # post-link: path
  # pre-unlink: path
  # pre-link: path
```

### Script section

```yaml
script:
  # the interpreter to use for the script
  interpreter: string  # defaults to bash on UNIX and cmd.exe on Windows
  # the script environment. You can use Jinja to pass through environment variables
  # with the `env` key (`${{ env.get("MYVAR") }}`).
  env: {string: string}
  # secrets that are set as env variables but never shown in the logs or the environment
  # The variables are taken from the parent environment by name (e.g. `MY_SECRET`)
  secrets: [string]
  # The file to use as the script. Automatically adds `bat` or `sh` to the filename
  # on Windows or UNIX respectively (if no file extension is given).
  file: string  # build.sh or build.bat
  # A string or list of strings that is the script contents (mutually exclusive with `file`)
  content: string | [string]
```

## Source section

```yaml
source: [SourceElement]
```

where the different source elements are defined as follows.

### URL source

```yaml
# url pointing to the source tar.gz|zip|tar.bz2|... (this can be a list of mirrors that point to the same file)
url: url | [url]
# destination folder in work directory
target_directory: path
# rename the downloaded file to this name
file_name: string
# hash of the file
sha256: hex string
# legacy md5 sum of the file (test both, prefer sha256)
md5: hex string
# relative path from recipe file
patches: [path]
```

### Local source

A path can be either:

- directory ("../bla")
- a path to an archive ("../bla.tar.gz")
- a path to a file ("../bla.txt")

```yaml
# file, absolute or relative to recipe file
path: path
# if there is a gitignore, adhere to it and ignore files that are matched by the ignore rules
# i.e. only copy the subset of files that are not ignored by the rules
use_gitignore: bool (defaults to true)
# destination folder
target_directory: path
# rename the downloaded file to this name
file_name: string
# absolute or relative path from recipe file
patches: [path]
```

### Git source

```yaml
# URL to the git repository or path to local git repository
git: url | path
# the following 3 keys are mutually exclusive (branch, tag, and rev)
# branch to checkout to
branch: string
# tag to checkout to
tag: string
# revision to checkout to (hash or ref)
rev: string
# depth of the git clone (mutually exclusive with rev)
depth: signed integer (defaults to -1 -> not shallow)
# should this use git-lfs?
lfs: bool (defaults to false)
# destination folder in work directory
target_directory: path
# absolute or relative path from recipe file
patches: [path]
```

### Removed source definitions

SVN and HG (mercury) source definitions are removed as they are not relevant anymore.

## Requirements section

```yaml
requirements:
  # build time dependencies, in the build_platform architecture
  build: [PackageSelector]
  # dependencies to link against, in the target_platform architecture
  host: [PackageSelector]
  # the section below is copied into the index.json and required at package installation
  run: [PackageSelector]
  # constrain optional packages (was `run_constrained`)
  run_constraints: [PackageSelector]
  # the run exports of this package
  run_exports: [PackageSelector] OR RunExports

  # the run exports to ignore when calculating the requirements
  ignore_run_exports:
    # ignore run exports by name (e.g. `libgcc-ng`)
    by_name: [string]
    # ignore run exports that come from the specified packages
    from_package: [string]

```

#### PackageSelector

A `PackageSelector` in the recipe is currently defined as a string with up to two whitespaces, looking like this:

```
<name> <version> <build_string>

# examples:
python
python 3.8
python 3.8 h1234567_0
python >=3.8,<3.9
python >=3.8,<3.9 h1234567_0
python 3.9.*
```

> [!NOTE]
> `MatchSpec` are defined with many more options in conda. We are sticking to conda-build's definition for the time being.
> For example, `conda` MatchSpecs allow specifying a channel, a build number (in square brackets) and many additional things.
> We might homogenize these things later on.


#### `RunExports` section

The different kind of run exports that can be specified are:

```yaml
# strong run exports go from build -> host & -> run
strong: [PackageSelector]
# weak run exports go from host -> run
weak: [PackageSelector]
# strong constraints adds a run constraint from build -> run_constraints (was `strong_constrains`)
strong_constraints: [PackageSelector]
# weak constraints adds a run constraint from host -> run_constraints (was `weak_constrains`)
weak_constraints: [PackageSelector]
# noarch run exports go from host -> run for `noarch` builds
noarch: [PackageSelector]
```

### Test section

<details>
<summary>
The current state of the Test section which is being removed with this spec.

Note: the test section also has a weird implicit behavior with `run_test.sh`, `run_test.bat` as well as `run_test.py` and `run_test.pl` script files
that are run as part of the test.

</summary>
The current YAML format for the test section is:

```yaml
test:
  # files (from recipe directory) to include with the tests
  files: [glob]
  # files (from the work directory) to include with the tests
  source_files: [glob]
  # requirements at test time, in the target_platform architecture
  requires: [PackageSelector]
  # commands to execute
  commands: [string]
  # imports to execute with python (e.g. `import <string>`)
  imports: [string]
  # downstream packages that should be tested against this package
  downstreams: [PackageSelector]
```

</details>

The new test section consists of a list of test elements. Each element is executed independently and can have different requirements.
There are multiple types of test elements defined, such as the `command` test element, the `python` test element and the `downstream` test element.

Before, the test section was written to a single folder (`info/test`). In the new format, we propose to write each test element to a separate folder
(`info/tests/<index>`). This allows us to run each test element independently.

```yaml
tests: [TestElement]
```

#### Command test element

The command test element renders to a single folder with a `test_time_dependencies.json` with two keys (`build` and `run`) that contain the raw "PackageSelector" strings.
The `script` is rendered to a `script.json` that contains the `interpreter`, `env` and other keys (as defined in the `Script` section).
Files are copied into the `info/tests/<index>` folder.

```yaml
# script to execute
# reuse script definition from above
script: string | [string] | Script
# optional extra requirements
requirements:
  # extra requirements with build_platform architecture (emulators, ...)
  build: [PackageSelector]
  # extra run dependencies
  run: [PackageSelector]

# extra files to add to the package for the test
files:
  # files from $SRC_DIR
  source: [glob]
  # files from $RECIPE_DIR
  recipe: [glob]
```

#### Python test element

The python test element renders a `test_import.py` file that contains the imports to test.
It also automatically runs the `pip check` command to check for missing dependencies.

```yaml
python:
  # list of imports to try
  imports: [string]
  pip_check: bool  # defaults to true
```

#### Downstream test element

The downstream test element renders to a `test_downstream.json` file that contains the `downstream` key with the raw "PackageSelector" string.

```yaml
downstream: PackageSelector
```

## Outputs section

conda-build has very hard to understand behavior with multiple outputs. We propose some drastic simplifications.
Each output in the new format has the same keys as a "top-level" recipe.

Values from the top-level `build`, `source` and `about` sections are (deeply) merged into each of the outputs.

The top-level package field is replaced by a top-level `recipe` field. The `version` from the top-level
`recipe` is also merged into each output. The top-level name is ignored (but could be used, e.g. for
the feedstock-name in the conda-forge case).

```yaml
# note: instead of `package`, it says `recipe` here
recipe:
  name: string # mostly ignored, could be used for feedstock name
  version: string # merged into each output if not overwritten by output

outputs:
  - package:
      name: string
      version: string (defaults to top-level version)
    build:
      script: ...
    requirements:
      # same definition as top level

    # same definitions as on top level, by default merged from outer recipe
    about:
    source:
    tests:
```

Before the build, the outputs are topologically sorted by their dependencies. Each output acts as an independent recipe.

> [!NOTE]
> A previous version contained a idea for a "cache-only" output. We've moved that to a future CEP.

### Aside: variant computation for multiple outputs

Multiple outputs are treated like individual recipes after the merging of the nodes is completed.
Therefore, each variant is computed for each output individually.

Another tricky bit is that packages can be "strongly" connected with a `pin_subpackage(name, exact=True)` constraint.
In this case, the pinned package should also be part of the "variant configuration" for the output and appropriately zipped.

For example, we can have three outputs: `libmamba`, `libmambapy`, and `mamba`.

- `libmamba` -> creates a single variant as it is a low-level C++ library
- `libmambapy` -> creates multiple packages, one per python version
- `mamba` -> creates multiple packages (one per python + libmambapy version)

<img width="1527" alt="img-1" src="https://github.com/conda-incubator/ceps/assets/885054/b8292fd0-bd8d-4a55-831b-d32b7db2d61f">

This has historically been an issue in conda-build, as it didn't take into account `pin_subpackage` edges as "variants" and
sometimes created the same hashes for two different outputs. E.g. in the following situation, conda-build would only create a single
`foofoo` package (instead of two variants that exactly pin two different libfoo packages):

<img width="2065" alt="img-2" src="https://github.com/conda-incubator/ceps/assets/885054/b5e80f64-28ef-45fd-afbb-91e94dda5eeb">

## About section

```yaml
about:
  # a summary of what this package does
  summary: string
  # a longer description of what this package does (should we allow referencing files here?)
  description: string

  # the license of the package in SPDX format
  license: string (SPDX enforced)
  # the license files
  license_file: path | [path] (relative paths are found in source directory _or_ recipe directory)
  # URL that points to the license – just stored as metadata
  license_url: url

  # URL to the homepage (used to be `home`)
  homepage: url
  # URL to the repository (used to be `dev_url`)
  repository: url
  # URL to the documentation (used to be `doc_url`)
  documentation: url

  # REMOVED:
  # prelink_message:
  # license_family: string (deprecated due to SPDX)
  # identifiers: [string]
  # tags: [string]
  # keywords: [string]
  # doc_source_url: url
```

## Extra section

```yaml
# a free form YAML dictionary
extra:
  <key>: <value>
```

## Example recipe

What follows is an example recipe, using the YAML syntax discussed in https://github.com/conda-incubator/ceps/pull/54

```yaml
context:
  name: xtensor
  version: 0.24.6

package:
  name: ${{ name|lower }}
  version: ${{ version }}

source:
  url: https://github.com/xtensor-stack/xtensor/archive/${{ version }}.tar.gz
  sha256: f87259b51aabafdd1183947747edfff4cff75d55375334f2e81cee6dc68ef655

build:
  number: 0
  skip:
    # note that the value is a minijinja expression
    - osx or win

requirements:
  build:
    - ${{ compiler('cxx') }}
    - cmake
    - if: unix
      then: make
  host:
    - xtl >=0.7,<0.8
  run:
    - xtl >=0.7,<0.8
  run_constraints:
    - xsimd >=8.0.3,<10

tests:
  - script:
      - if: unix
        then:
          - test -d ${PREFIX}/include/xtensor
          - test -f ${PREFIX}/include/xtensor/xarray.hpp
          - test -f ${PREFIX}/share/cmake/xtensor/xtensorConfig.cmake
          - test -f ${PREFIX}/share/cmake/xtensor/xtensorConfigVersion.cmake
      - if: win
        then:
          - if not exist %LIBRARY_PREFIX%\include\xtensor\xarray.hpp (exit 1)
          - if not exist %LIBRARY_PREFIX%\share\cmake\xtensor\xtensorConfig.cmake (exit 1)
          - if not exist %LIBRARY_PREFIX%\share\cmake\xtensor\xtensorConfigVersion.cmake (exit 1)
  # compile a test package
  - if: unix
    then:
      files:
        - testfiles/cmake/*
      requirements:
        build:
          - ${{ compiler('cxx') }}
          - cmake
          - ninja
      script: |
        cd testiles/cmake/
        mkdir build; cd build
        cmake -GNinja ..
        cmake --build .
        ./target/hello_world

  - downstream: xtensor-python
  - downstream: xtensor-blas
  - python:
      imports:
        - xtensor_python
        - xtensor_python.numpy_adapter
```

Or a multi-output package

```yaml
context:
  name: mamba
  libmamba_version: "1.4.2"
  libmambapy_version: "1.4.2"
  # can also reference previous variables here
  mamba_version: ${{ libmamba_version }}
  release: "2023.04.06"
  libmamba_version_split: ${{ libmamba_version.split('.') }}

# we can leave this out
# package:
#   name: mamba-split

# this is inherited by every output
source:
  url: https://github.com/mamba-org/mamba/archive/refs/tags/${{ release }}.tar.gz
  sha256: bc1ec3de0dd8398fcc6f524e6607d9d8f6dfeeedb2208ebe0f2070c8fd8fdd83

build:
  number: 0

outputs:
  - package:
      name: libmamba
      version: ${{ libmamba_version }}

    build:
      script: ${{ "build_mamba.sh" if unix else "build_mamba.bat" }}

    requirements:
      build:
        - ${{ compiler('cxx') }}
        - cmake
        - ninja
        - ${{ "python" if win }}
      host:
        - libsolv >=0.7.19
        - libcurl
        - openssl
        - libarchive
        - nlohmann_json
        - cpp-expected
        - reproc-cpp >=14.2.1
        - spdlog
        - yaml-cpp
        - cli11
        - fmt
        - if: win
          then: winreg
      run_exports:
        - ${{ pin_subpackage('libmamba', max_pin='x.x') }}
      ignore_run_exports:
        from_package:
          - spdlog
          - if: win
            then: python

    tests:
      - script:
          - if: unix
            then:
              - test -d ${PREFIX}/include/mamba
              - test -f ${PREFIX}/include/mamba/version.hpp
              - test -f ${PREFIX}/lib/cmake/libmamba/libmambaConfig.cmake
              - test -f ${PREFIX}/lib/cmake/libmamba/libmambaConfigVersion.cmake
              - test -e ${PREFIX}/lib/libmamba${SHLIB_EXT}
            else:
              - if not exist %LIBRARY_PREFIX%\include\mamba\version.hpp (exit 1)
              - if not exist %LIBRARY_PREFIX%\lib\cmake\libmamba\libmambaConfig.cmake (exit 1)
              - if not exist %LIBRARY_PREFIX%\lib\cmake\libmamba\libmambaConfigVersion.cmake (exit 1)
              - if not exist %LIBRARY_PREFIX%\bin\libmamba.dll (exit 1)
              - if not exist %LIBRARY_PREFIX%\lib\libmamba.lib (exit 1)
          - if: unix
            then:
              - cat $PREFIX/include/mamba/version.hpp | grep "LIBMAMBA_VERSION_MAJOR ${{ libmamba_version_split[0] }}"
              - cat $PREFIX/include/mamba/version.hpp | grep "LIBMAMBA_VERSION_MINOR ${{ libmamba_version_split[1] }}"
              - cat $PREFIX/include/mamba/version.hpp | grep "LIBMAMBA_VERSION_PATCH ${{ libmamba_version_split[2] }}"

  - package:
      name: libmambapy
      version: ${{ libmambapy_version }}

    build:
      script: ${{ "build_mamba.sh" if unix else "build_mamba.bat" }}
      string: py${{ CONDA_PY }}h${{ PKG_HASH }}_${{ PKG_BUILDNUM }}

    requirements:
      build:
        - ${{ compiler('cxx') }}
        - cmake
        - ninja
        - if: build_platform != target_platform
          then:
            - python
            - cross-python_${{ target_platform }}
            - pybind11
            - pybind11-abi
      host:
        - python
        - pip
        - pybind11
        - pybind11-abi
        - openssl
        - yaml-cpp
        - cpp-expected
        - spdlog
        - fmt
        - termcolor-cpp
        - nlohmann_json
        - ${{ pin_subpackage('libmamba', exact=True) }}
      run:
        - python
        - ${{ pin_subpackage('libmamba', exact=True) }}

      run_exports:
        - ${{ pin_subpackage('libmambapy', max_pin='x.x') }}

      ignore_run_exports:
        from_package:
          - spdlog

    tests:
      - python:
          imports:
            - libmambapy
            - libmambapy.bindings
      - script:
          - python -c "import libmambapy._version; assert libmambapy._version.__version__ == '${{ libmambapy_version }}'"

  - name: mamba
    # version: always the same as top-level
    build:
      script: ${{ "build_mamba.sh" if unix else "build_mamba.bat" }}
      string: py${{ CONDA_PY }}h${{ PKG_HASH }}_${{ PKG_BUILDNUM }}
      entry_points:
        - mamba = mamba.mamba:main

    requirements:
      build:
        - if: build_platform != target_platform
          then:
            - python
            - cross-python_${{ target_platform }}
      host:
        - python
        - pip
        - openssl
        - ${{ pin_subpackage('libmambapy', exact=True) }}
      run:
        - python
        - conda >=4.14,<23.4
        - ${{ pin_subpackage('libmambapy', exact=True) }}

    tests:
      - python:
          imports: [mamba]

      - requirements:
          run:
            - pip
        script:
          - mamba --help
          # check dependencies with pip
          - pip check
          - if: win
            then:
              - if exist %PREFIX%\condabin\mamba.bat (exit 0) else (exit 1)
          - if: linux
            then:
              - test -f ${PREFIX}/etc/profile.d/mamba.sh
              # these tests work when run on win, but for some reason not during conda build
              - mamba create -n test_py2 python=2.7 --dry-run
              - mamba install xtensor xsimd -c conda-forge --dry-run

          - if: unix
            then:
              - test -f ${PREFIX}/condabin/mamba

          # for some reason tqdm doesn't have a proper colorama dependency so pip check fails
          # but that's completely unrelated to mamba
          - python -c "import mamba._version; assert mamba._version.__version__ == '${{ mamba_version }}'"

about:
  homepage: https://github.com/mamba-org/mamba
  license: BSD-3-Clause
  license_file: LICENSE
  summary: A fast drop-in alternative to conda, using libsolv for dependency resolution
  description: Just a package manager
  repository: https://github.com/mamba-org/mamba

extra:
  recipe-maintainers:
    - the_maintainer_bot
```
