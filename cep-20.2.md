# A new recipe format – part 2 - the allowed keys & values

<table>
<tr><td> Title </td><td> A new recipe format - values </td>
<tr><td> Status </td><td> Proposed</td></tr>
<tr><td> Author(s) </td><td> Wolf Vollprecht &lt;wolf@prefix.dev&gt;</td></tr>
<tr><td> Created </td><td> May 23, 2023</td></tr>
<tr><td> Updated </td><td> May 23, 2023</td></tr>
<tr><td> Discussion </td><td>  </td></tr>
<tr><td> Implementation </td><td>https://github.com/prefix-dev/rattler-build</td></tr>
</table>

## Abstract

We propose a new recipe format that is heavily inspired by conda-build. The main
change is a pure YAML format without arbitrary Jinja or comments with semantic
meaning.

## Motivation

The conda-build format is currently under-specified. For the new format, we try to list all values
and types in a single document and document them. This is part of a larger effort (see [](/cep-20.1.md) for the new YAML syntax).

## History

A discussion was started on what a new recipe spec could or should look like.
The fragments of this discussion can be found here:
https://github.com/mamba-org/conda-specs/blob/master/proposed_specs/recipe.md
The reason for a new spec are:

- Make it easier to parse ("pure yaml"). conda-build uses a mix of comments and
  jinja to achieve a great deal of flexibility, but it's hard to parse the
  recipe with a computer
- iron out some inconsistencies around multiple outputs (build vs. build/script
  and more)
- remove any need for recursive parsing & solving
- cater to needs for automation and dependency tree analysis via a determinstic
  format

## Major differences with conda-build

Outputs and top-level package are mutually exclusive, and outputs have exactly the same structure as top-level keys.
If outputs exist, the top-level keys are 'merged' with the output keys (e.g. for the about section).

# Format

## Context section

```yaml
# The context dictionary defines arbitrary key-value pairs for Jinja interpolation
# and replaces the {% set ... %} commands commonly used in recipes
context:
  variable: test
  # note that we can reference previous values
  other_variable: test_${{ variable }}
```

## Package section

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
    number: Option<integer>, defaults to 0
    # the build string. This is usually ommited
    string: Option<string>, defaults to a build string made from "package hash & build number"

    # A list of conditions under which to skip the build of this package
    skip: [list of expressions]

    force_use_keys: [string]
    force_ignore_keys: [string]

    # wether the package is a noarch package, and if yes, wether it is "generic" or "python"
    noarch: Option<"generic" | "python">

    # Only valid if `noarch: python` - list of all entry points of the package
    # PythonEntryPoint: `bsdiff4 = bsdiff4.cli:main_bsdiff4`
    entry_points: [PythonEntryPoint]

    # ?
    osx_is_app: bool (default false)

    # used on conda-forge, still needed?
    preserve_egg_dir: bool (default false)

    # only used as a hack to down-prioritize packages
    track_features: [string]

    # skip compiling pyc for some files
    skip_compile_pyc: [glob]

    # do not
    no_link: [glob]

    # the script that is executed to build the package
    # if it is only one element and ends with `.sh` or `.bat`
    script: string | [string]

    # linux only, list of rpaths
    rpaths: [path] (defaults to ['lib/'])

    # include files even if they are already in the environment as part of some other
    # host dependency
    always_include_files: [path]

    # wether to relocate binaries or not. If this is a list of paths, then
    # only the listed paths are relocated
    binary_relocation: bool (defaults to true) | [glob]

    # force file to be detected as TEXT file (for prefix replacement)
    has_prefix_files: [path]

    # force file to be detected as BINARY file (for prefix replacement)
    binary_has_prefix_files: [path]

    # ignore all or specific files for prefix replacement
    ignore_prefix_files: bool | [path] (defaults to false)

    # wether to detect binary files with prefix or not
    detect_binary_files_with_prefix: bool (defaults to true on Unix and (always) false on Windows)

    # Wether to include the recipe or not in the final package
    include_recipe: bool (defaults to true)

    # environment variables to either pass through to the script environment or set
    script_env: [env_vars]

    run_exports: [MatchSpec] OR {strong: [MatchSpec], weak: [MatchSpec], strong_constrains: [MatchSpec], weak_constrains: [MatchSpec], noarch: [MatchSpec]}

    missing_dso_whitelist: [glob]

    runpath_whitelist: [glob]

    # This is only used in the pip feedstock.
    disable_pip: bool (defaults to false)

    # used in many r packages on Windows
    merge_build_host: bool

    # ignore run exports by name
    ignore_run_exports: list

    # ignore run exports coming from the specified packages
    ignore_run_exports_from: list

    # copies fn[.bat/.sh] to the appropriate location, adds `.bat` or `.sh` to the filename
    pre-link: string
    post-link: string
    pre-unlink: string

    # error out when overdepending
    error_overdepending: bool (defaults to ?)
    # error out when overlinking
    error_overlinking: bool (defaults to ?)

    # REMOVED:
    # noarch_python: bool
    # features: list
    # msvc_compiler: str
    # requires_features: dict
    # provides_features: dict
    # preferred_env: str
    # preferred_env_executable_paths: list

    # marked as "still experimental"
    # pin_depends: Enum<"record" | "strict">
    # overlinking_ignore_patterns: [glob]

    # defaults to patchelf (only cudatoolkit is using `lief` for some reason)
    # rpaths_patcher: None
```

## Source section

```yaml
source: [SourceElement]
```

where the different source elements are defined as follows.

### URL source

```yaml
# url pointing to the source tar.gz|zip|tar.bz2|...
url: url
# destination folder in work directory
folder: path
# hash of the file
sha256: hex string
# absolute or relative path from recipe file
patches: [path]
# removed
# fn: string
# md5: hex string
# sha1: hex string
```

### Local source

```yaml
# file, absolute or relative to recipe file
path: path
# destination folder
folder: path
# absolute or relative path from recipe file
patches: [path]
```

### Git source

```yaml
# URL to the git repository or path to local git repository
git_url: url | path
# revision to checkout to (commit or tag)
git_rev: string
git_depth: signed integer (defaults to -1 -> not shallow)
```

### Removed source definitions

SVN and HG (mercury) source definitions are removed as they are not relevant anymore.

## Requirements section

```yaml
requirements:
  # build time dependencies, in the build_platform architecture
  build: [MatchSpec]
  # dependencies to link against, in the target_platform architecture
  host: [MatchSpec]
  # the section below is copied into the index.json and required at package installation
  run: [MatchSpec]
  # constrain optional packages
  run_constrained: [MatchSpec]
```

## Test section

Note: the test section also has a weird implicit behavior with `run_test.sh`, `run_test.bat` as well as `run_test.py` and `run_test.pl` script files
that are run as part of the test.

This is the current state of the Test section.

```yaml
test:
  # files (from recipe directory) to include with the tests
  files: [glob]
  # files (from the work directory) to include with the tests
  source_files: [glob]
  # requirements at test time, in the target_platform architecture
  requires: [MatchSpec]
  # commands to execute
  commands: [string]
  # imports to execute with python (e.g. `import <string>`)
  imports: [string]
  # downstream packages that should be tested against this package
  downstreams: [MatchSpec]
```

### Proposal for new test section:

```
test: [TestElement]
```

where the different test elements are defined as follows:

#### Command test element

```yaml
# script to execute
script: string | [string]
# optional extra requirements
extra_requirements:
  # extra requirements with build_platform architecture (emulators, ...)
  build: [MatchSpec]
  # extra run dependencies
  run: [MatchSpec]
# extra files to add to the package for the test
# Alternatively, use ${{ RECIPE_DIR }} or ${{ SOURCE_DIR }} and a single list?
# or $RECIPE_DIR / $SRC_DIR ...
files:
  # files from $SRC_DIR
  source: [glob]
  # files from $RECIPE_DIR
  recipe: [glob]
```

#### Import test element

```yaml
# list of imports to try
imports: [string]
```

#### Downstream test element

```yaml
downstream: MatchSpec
```

## Outputs section

conda-build has very hard to understand behavior with multiple outputs. We propose some drastic simplifications.
Each output in the new format has the same keys as a "top-level" recipe.

Values from the top-level `build` and `about` section are merged into the outputs. The `version` from the top-level
`package` is also merged into each output. The top-level name is ignored.

```yaml
outputs:
  - package:
      name: string
      version: string (defaults to top-level version)
    build:
      # this package can only be used by other _outputs_ as build cache (for split packages)
      # in that way it replaces the top-level build
      # alternative names: package: true/false, output_package: true/false
      cache_only: bool (defaults to false)
      # cache from refers to the output from which the cache should be expanded into the WORK DIR
      cache_from: string | [string]
      # everything the same as top level
      script: ...
    requirements:
      # same definition as top level

    # as top level, by default merged from outer recipe
    about:
    source:
    test:
```

A cache only package does only package the `$WORK_DIR` (similar to how top-level packages work today) and each output that depends on a cache package via `cache_from`
will get a prepared `$WORK_DIR` with the build artifacts from the previously executed package.

> **Note**
> Should run-dependencies from the cache_only package be inherited? That would make `run_exports` work better ...

## About section

```yaml
about:
  # The license
  # We can enforce SPDX for license?
  license: string
  # license files
  license_file: path | [path] (relative paths are found in source directory _or_ recipe directory)
  # a summary of what this package does
  summary: string
  # a longer description of what this package does (should we allow referencing files here?)
  description: string
  # URL to the homepage
  home: url
  # url to the repository - rename?
  dev_url: url
  # URL to the docs
  doc_url: url
  # unsure if we should keep this one
  license_url: url

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
# a free form dictionary
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
      value: make
  host:
    - xtl >=0.7,<0.8
  run:
    - xtl >=0.7,<0.8
  run_constrained:
    - xsimd >=8.0.3,<10

test:
  - script:
      - if: unix
        value:
          - test -d ${PREFIX}/include/xtensor
          - test -f ${PREFIX}/include/xtensor/xarray.hpp
          - test -f ${PREFIX}/share/cmake/xtensor/xtensorConfig.cmake
          - test -f ${PREFIX}/share/cmake/xtensor/xtensorConfigVersion.cmake
      - if: win
        value:
          - if not exist %LIBRARY_PREFIX%\include\xtensor\xarray.hpp (exit 1)
          - if not exist %LIBRARY_PREFIX%\share\cmake\xtensor\xtensorConfig.cmake (exit 1)
          - if not exist %LIBRARY_PREFIX%\share\cmake\xtensor\xtensorConfigVersion.cmake (exit 1)
  # compile a test package
  - if: unix
    then:
      files:
        - testfiles/cmake/*
      extra_requirements:
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
  - imports:
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
      run_exports:
        - ${{ pin_subpackage('libmamba', max_pin='x.x') }}
      ignore_run_exports:
        - spdlog
        - if: win
          then: python

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

    test:
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
      run_exports:
        - ${{ pin_subpackage('libmambapy', max_pin='x.x') }}
      ignore_run_exports:
        - spdlog
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

    test:
      - imports:
          - libmambapy
          - libmambapy.bindings
      - script:
          - python -c "import libmambapy._version; assert libmambapy._version.__version__ == '${{ libmambapy_version }}'"

  - package:
      name: mamba
      version: ${{ mamba_version }}
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

    test:
      - imports: [mamba]

      - extra_requirements:
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
  home: https://github.com/mamba-org/mamba
  license: BSD-3-Clause
  license_file: LICENSE
  license_family: BSD
  summary: A fast drop-in alternative to conda, using libsolv for dependency resolution
  description: Just a package manager
  dev_url: https://github.com/mamba-org/mamba

extra:
  recipe-maintainers:
    - the_maintainer_bot
```
