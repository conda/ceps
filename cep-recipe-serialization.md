# Recipe format: Rendered recipe YAML and serialization

## Motivation

As part of the metadata, a package might include the "raw" and "rendered" recipe.
A rendered recipe is a recipe.yaml file that has all Jinja and if/else logic resolved to the final values.

This CEP defines the structure and contents of the `rendered_recipe.yaml` file
which captures the complete recipe, build configuration, dependencies and
sources used to create a conda package.

The goal is to have a single file that contains all the information needed to
reproduce the exact build of a package. This will enable better reproducibility,
provenance tracking, and debugging of conda packages.

## Storage

The rendered recipe YAML file is stored in the `info/recipe` folder of the final
package. Alongside the rendered recipe, we copy the entire "recipe folder".
If the original recipe was not named `recipe.yaml`, then we rename it inside the package.

For example:

```txt
├── recipe
    ├── patches
    │   └── patch1.diff
    ├── build.sh
    ├── build.bat
    └── my_recipe.yaml
```

Will be copied into the following folder structure in the final package:

```txt
├── ...
├── index.json
└── recipe
    ├── build.bat
    ├── build.sh
    ├── recipe.yaml
    ├── patches
    │   └── patch1.diff
    ├── rendered_recipe.yaml
    └── variant_config.yaml
```

## Specification

The rendered recipe YAML file contains the following top-level sections:

1. `recipe`: The fully rendered recipe with all Jinja2 expressions evaluated and
   if/else logic resolved to the final used values.
2. `build_configuration`: Captures all the build-time configuration such as the
   target platform, build/host prefixes, variant used, package version and build
   string, channels, etc.
3. `finalized_dependencies`: Records the exact versions and builds of all
   dependencies (build, host and run) that were used at build time, like a
   "lockfile".
4. `finalized_sources`: Contains the final references to the sources used, e.g.
   git commit hashes, tarball URLs + sha256, etc.
5. `system_tools`: Records the tools that were used from the host system in
   order to warn if reproducing the build on a different host system might lead
   to different results (patchelf, git, etc).

### Recipe section

This section is the fully rendered recipe in valid YAML format, with all Jinja2
expressions evaluated and if/else logic resolved to the final values used during
the build.

Some key things to note:

- Compiler expressions like ${{ compiler('c') }} are rendered to their final
  YAML dictionary form:

  ```yaml
  - ${{ compiler('c') }}
  # becomes
  - compiler: c
  ```

- Pin expressions like ${{ pin_subpackage('libtool', max_pin='x.x') }} are
  rendered to:

  ```yaml
  - ${{ pin_subpackage('libtool', exact=true) }}
  # becomes
  - pin_subpackage:
      name: libtool
      max_pin: null
      min_pin: null
      exact: true
  ```

- For the following:

  ```yaml
  - ${{ pin_subpackage('some-pkg-a', min_pin="x.x.x") }}
  - ${{ pin_compatible('python', min_pin="x.x.x") }}
  ```

  the rendered result is as follows:

  ```yaml
  - pin_subpackage:
      name: some-pkg-a
      max_pin: null
      min_pin: x.x.x
      exact: false
  - pin_compatible:
      name: python
      max_pin: null
      min_pin: x.x.x
      exact: false
  ```

### Build configuration section

This records all information that was used at build time, incl. variables given
on the CLI or by environment yaml. Everything necessary to reproduce the build
should be recorded here.

Here's the documentation for the fields in the provided YAML:

#### `build_configuration`

The `build_configuration` section contains information related to the build
process.

##### `target_platform`

- Type: string
- Description: The target platform for which the package is being built (e.g.,
  `osx-arm64`).

##### `host_platform` (remove?)

- Type: string
- Description: The host platform used for building the package. Usually
  equivalent to `target_platform`, except when the `target_platform` is
  `noarch`. If the `target_platform` is `noarch`, the `host_platform` is the
  platform where the build is being executed.

> [!NOTE] 
> Actually we might remove this field as we can reconstruct it from the `build_platform` and `target_platform` fields.

##### `build_platform`

- Type: string
- Description: The platform used for building the package (e.g., `osx-arm64`).

##### `variant`

- Type: object
- Description: Dictionary with the variant configuration used for the build.

##### `hash`

- Type: object
- Description: Contains information related to hashing.
  - `hash`: The hash value (e.g., `60d57d3`).
  - `prefix`: Prefix for the hash, which can include values like `py311`
    based on the variant configuration.

##### `directories`

- Type: object
- Description: Contains directory paths used during the build process.
  - `host_prefix`: The host prefix directory with placeholders for the host
    environment.
  - `build_prefix`: The build prefix directory for the build environment.
  - `work_dir`: The working directory with extracted sources.
  - `build_dir`: The build directory that contains `host_prefix`,
    `build_prefix`, and `work_dir` as subdirectories.

##### `channels`

- Type: array of URLs
- Description: The URLs to the conda channels that were used to resolve dependencies (e.g., `conda-forge`).
               Also in the correct order.

##### `timestamp`

- Type: string / timestamp in ISO 8601 format
- Description: The timestamp of the build configuration (e.g.,
  `2024-04-13T14:35:30.774863Z`).

##### `subpackages`

- Type: list of objects
- Description: Contains information about subpackages that are used in
  `pin_subpackage` expressions.
  - `curl`: An example subpackage.
    - `name`: The name of the subpackage (e.g., `curl`).
    - `version`: The version of the subpackage (e.g., `8.0.1`).
    - `build_string`: The build string for the subpackage (e.g., `h60d57d3_0`).

##### `packaging_settings`

- Type: object
- Description: Contains settings related to the final package output.
  - `archive_type`: The type of archive used for packaging (either `tar_bz2` or
    `conda`).
  - `compression_level`: The numerical compression level used for packaging
    (e.g., `15`).
  - `compression_threads`: The number of threads used for compression (e.g.,
    `1`).

#### Example

```yaml
build_configuration:
  target_platform: osx-arm64
  host_platform: osx-arm64
  build_platform: osx-arm64
  variant:
    target_platform: osx-arm64
  hash:
    hash: 60d57d3
    hash_input: '{"target_platform": "osx-arm64"}' # input values for the hash
    hash_prefix: "" # would contain `py311` and similar prefixes based on variant config
  directories:
    host_prefix: # host prefix with placeholders for the host environment
    build_prefix: # build prefix for the build environment
    work_dir: # work dir with extracted sources
    build_dir: # build dir that contains host_prefix, build_prefix and work_dir as subdirectories
  channels:
    - conda-forge
  timestamp: 2024-04-13T14:35:30.774863Z
  subpackages:
    curl:
      name: curl
      version: 8.0.1
      build_string: h60d57d3_0
  packaging_settings:
    archive_type: conda
    compression_level: 15
    compression_threads: 1
```

### Finalized dependencies

The finalized dependencies section contains a "lockfile" of all the dependencies
exactly as they were used at build-time, for the two environments `build` and
`host`. It also includes the final `run` and `constrains` specs that are
computed based on the `build` and `host` dependencies (resolved all
`run_exports`).

The `finalized_dependencies` section contains the following keys:

```yaml
finalized_dependencies:
  build:
    specs: [list of spec objects]
    resolved: [list of resolved dependency objects]
    run_exports: { package_name: run_export } # all run_exports.json that were found among the packages in this environment
  host:
    specs: [list of spec objects]
    resolved: [list of resolved dependency objects]
    run_exports: { package_name: run_export } # all run_exports.json that were found among the packages in this environment
  run:
    depends: [list of dependencies with dependency source information]
    constrains: [list of constrains with dependency source information]
    run_exports: optional run_export dictionary
```

#### Spec objects

A dependency spec contains the `MatchSpec` and additional information about the
source of the dependency. There are 6 possible `DependencyInfo` versions:

- `compiler`: The dependency comes from a `compiler` expression.
- `pin_subpackage`: The dependency comes from a `pin_subpackage` expression.
- `pin_compatible`: The dependency comes from a `pin_compatible` expression.
- `source`: The dependency comes from te recipe.
- `run_export`: The dependency comes from a run export.
- `variant`: The dependency comes from a variant.

Example:

```yaml
- compile: c              # language specified in ${{ compiler(`c`) }}
  spec: clang_osx-arm64   
- source: make >=1.3      
- pin_compatible: quarto
  min_pin: x.x    # not present if not specified
  max_pin: x.x.x  # not present if not specified
  exact: true     # not present if false or not specified
  spec: quarto >=1.4.550,<1.5
- pin_subpackage: some-pkg-a
  min_pin: x.x    # not present if not specified
  max_pin: x.x.x  # not present if not specified
  exact: true     # not present if false or not specified
  spec: some-pkg-a >=1.0.0,<2
- run_export: zlib
  spec: libzlib >=1.3.1,<1.4.0a0
  from: host              # environment that exported this dependency
- variant: setuptools     # key from variant coming configuration
  spec: setuptools 69.*
```

The list of `resolved` dependencies contains a dictionary with the following
fields (equivalent to `RepoDataRecord`):

```yaml
build: hb7217d7_0
build_number: 0
depends: []
license: GPL-2.0-or-later
license_family: GPL
md5: fe8efc3385f58f0055e8100b07225055
name: libtool
sha256: efe50471d2baea151f2a93f1f99c05553f8c88e3f0065cdc267e1aa2e8c42449
size: 408403
subdir: osx-arm64
timestamp: 1672362003513 # when available
version: 2.4.7
fn: libtool-2.4.7-hb7217d7_0.conda
url: https://conda.anaconda.org/conda-forge/osx-arm64/libtool-2.4.7-hb7217d7_0.conda
channel: https://conda.anaconda.org/conda-forge/
```

#### Run exports

The `build` and `host` section contain a `run_exports` dictionary that contains
collected run_exports from all direct dependencies. The dictionary contains
`name: run_export` pairs. A `run_export` entry contains the keys:

```yaml
weak: [list of weak run exports]
strong: [list of strong run exports]
weak_constrains: [list of weak constrains]
strong_constrains: [list of strong constrains]
noarch: [list of noarch run exports]
```

The `run` section also contains a single `run_exports` entry that is used to
generate the `run_exports` metadata for the package that we are currently
building. Different from the other `run_exports`, these are "outgoing"
run_exports.

### Finalized sources

This section contains the finalized sources that were used at build-time. For
`git` sources, this contains a reference to the commit hash that was used. For
`url` and `path` sources, this contains the URL and the SHA256 hash of the
downloaded file.

```yaml
finalized_sources:
  - path: ../
  - git: https://github.com/ros2-gbp/rosidl_typesupport_fastrtps-release.git
    rev: 7af149d83d7e4a2d4c9ce4ae9682bff4a8ebc28e # here we are storing the commit hash
    target_directory: ros-humble-fastrtps-cmake-module/src/work
  - url: https://github.com/watchexec/watchexec/archive/refs/tags/v1.25.1.tar.gz
    sha256: 9609163c14cd49ec651562838f38b88ed2d370e354af312ddc78c2be76c08d37
```

The following fields are available for each source:

#### Path source

> [!NOTE] The `sha256` field is added if it is not already present in the source
> description. (TODO in rattler-build) We should compute the SHA hashes of the
> patches as well and store it in the source description.

```yaml
path: # path to the source
sha256: # computed sha256 hash of the source (this is only added if not in the source entry in the original recipe)
patches: # list of patches that should be applied to the source
target_directory: # optional target directory where the source should be extracted
file_name: # optional file name
use_gitignore: # optional bool wether to use the .gitignore file when copying a directory
```

#### Git source

```yaml
git: # git URL
rev: # resolved commit hash at build time
depth: # optional depth to clone the repository
patches: # list of patches that should be applied to the source
target_directory: # optional target directory where the source should be extracted
lfs: # optional bool to request the lfs pull in git source
```

#### URL source

```yaml
url: # URL to the source code
sha256: # sha256 hash of the downloaded file
md5: # md5 hash of the downloaded file
file_name: # optional file name to rename the downloaded file
patches: # list of patches that should be applied to the source
target_directory: # optional target directory where the source should be extracted
```

### System tools

This section records all system tools that were used during build execution and
their versions (if available). This is useful for tracking the tools that were
used from the host system in order to warn if reproducing the build on a
different host system might lead to different results. It also records the
version of `rattler_build` itself, so a future build could be reproduced with
the same version of `rattler_build`.

```yaml
system_tools:
  rattler_build: 0.14.0
  patchelf: 0.12
  git: 2.33.0
```

## Full Example

```yaml
recipe:
  schema_version: 1
  package:
    name: curl
    version: 8.0.1
  source:
    - url: http://curl.haxx.se/download/curl-8.0.1.tar.bz2
      sha256: 9b6b1e96b748d04b968786b6bdf407aa5c75ab53a3d37c1c8c81cdb736555ccf
  build:
    number: 0
    string: h60d57d3_0
  requirements:
    build:
      - compiler: c
      - make
      - perl
      - pkg-config
      - libtool
    host:
      - zlib
  tests:
    - test_type: command
      script:
        - curl --version
  about:
    homepage: http://curl.haxx.se/
    repository: https://github.com/curl/curl
    documentation: https://curl.haxx.se/docs/
    license: curl
    license_file:
      - COPYING
    summary: tool and library for transferring data with URL syntax
    description: |-
      Curl is an open source command line tool and library for transferring data
      with URL syntax. It is used in command lines or scripts to transfer data.
build_configuration:
  target_platform: osx-arm64
  host_platform: osx-arm64
  build_platform: osx-arm64
  variant:
    target_platform: osx-arm64
  hash:
    hash: 60d57d3
    hash_input: '{"target_platform": "osx-arm64"}'
    hash_prefix: ""
  directories:
    host_prefix: /Users/wolfv/Programs/rattler-build/output/bld/rattler-build_curl_1713018930/host_env_placehold_placehold_placehold_placehold_placehold_placehold_placehold_placehold_placehold_placehold_placehold_placehold_placehold_placehold_placehold_placehold_placehold
    build_prefix: /Users/wolfv/Programs/rattler-build/output/bld/rattler-build_curl_1713018930/build_env
    work_dir: /Users/wolfv/Programs/rattler-build/output/bld/rattler-build_curl_1713018930/work
    build_dir: /Users/wolfv/Programs/rattler-build/output/bld/rattler-build_curl_1713018930
  channels:
    - conda-forge
  timestamp: 2024-04-13T14:35:30.774863Z
  subpackages:
    curl:
      name: curl
      version: 8.0.1
      build_string: h60d57d3_0
  packaging_settings:
    archive_type: conda
    compression_level: 15
    compression_threads: 1
finalized_dependencies:
  build:
    specs:
      # specs record the source, can be one of `raw`, `compiler`, `pin_subpackage`, `pin_compatible`, `variant`, `run_export`
      - source: compiler
        spec: clang_osx-arm64
      - source: raw
        spec: make
      - source: raw
        spec: perl
      - source: raw
        spec: pkg-config
      - source: raw
        spec: libtool
    resolved:
      - build: he57ea6c_1
        build_number: 1
        depends: []
        license: GPL-3.0-or-later
        license_family: GPL
        md5: 1939d04ef89e38fde652ee8c669e092f
        name: make
        sha256: a011e3e1c4caec821eb4213d0a0154d39e5f81a44d2e8bafe6f84e7840c3909e
        size: 253227
        subdir: osx-arm64
        timestamp: 1602706492919
        version: "4.3"
        fn: make-4.3-he57ea6c_1.tar.bz2
        url: https://conda.anaconda.org/conda-forge/osx-arm64/make-4.3-he57ea6c_1.tar.bz2
        channel: https://conda.anaconda.org/conda-forge/
      - build: hab62308_1008
        build_number: 1008
        depends:
          - libglib >=2.70.2,<3.0a0
          - libiconv >=1.16,<2.0.0a0
        license: GPL-2.0-or-later
        license_family: GPL
        md5: 8d173d52214679033079d1b0582075aa
        name: pkg-config
        sha256: e59e69111709d097f9938e72ba19811ec1ef36aababdbed77bd7c767f15639e0
        size: 46049
        subdir: osx-arm64
        timestamp: 1650239029040
        version: 0.29.2
        fn: pkg-config-0.29.2-hab62308_1008.tar.bz2
        url: https://conda.anaconda.org/conda-forge/osx-arm64/pkg-config-0.29.2-hab62308_1008.tar.bz2
        channel: https://conda.anaconda.org/conda-forge/
      - build: h0d3ecfb_2
        build_number: 2
        depends: []
        license: LGPL-2.1-only
        md5: 69bda57310071cf6d2b86caf11573d2d
        name: libiconv
        sha256: bc7de5097b97bcafcf7deaaed505f7ce02f648aac8eccc0d5a47cc599a1d0304
        size: 676469
        subdir: osx-arm64
        timestamp: 1702682458114
        version: "1.17"
        fn: libiconv-1.17-h0d3ecfb_2.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/libiconv-1.17-h0d3ecfb_2.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: hb7217d7_0
        build_number: 0
        depends: []
        license: GPL-2.0-or-later
        license_family: GPL
        md5: fe8efc3385f58f0055e8100b07225055
        name: libtool
        sha256: efe50471d2baea151f2a93f1f99c05553f8c88e3f0065cdc267e1aa2e8c42449
        size: 408403
        subdir: osx-arm64
        timestamp: 1672362003513
        version: 2.4.7
        fn: libtool-2.4.7-hb7217d7_0.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/libtool-2.4.7-hb7217d7_0.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: 7_h4614cfb_perl5
        build_number: 7
        depends: []
        license: GPL-1.0-or-later OR Artistic-1.0-Perl
        md5: ba3cbe93f99e896765422cc5f7c3a79e
        name: perl
        sha256: b0c55040d2994fd6bf2f83786561d92f72306d982d6ea12889acad24a9bf43b8
        size: 14439531
        subdir: osx-arm64
        timestamp: 1703311335652
        version: 5.32.1
        fn: perl-5.32.1-7_h4614cfb_perl5.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/perl-5.32.1-7_h4614cfb_perl5.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: hfc324ee_4
        build_number: 4
        constrains:
          - glib 2.80.0 *_4
        depends:
          - libffi >=3.4,<4.0a0
          - libiconv >=1.17,<2.0a0
          - libintl >=0.22.5,<1.0a0
          - libzlib >=1.2.13,<1.3.0a0
          - pcre2 >=10.43,<10.44.0a0
        license: LGPL-2.1-or-later
        md5: c0de76b2c1f1bee86ca8660684ab6ec4
        name: libglib
        sha256: 48f371fcb374020c140b26dbfc9a6ef3fbc834334e8cca984120be7bffa6d1bf
        size: 2638588
        subdir: osx-arm64
        timestamp: 1712590361453
        version: 2.80.0
        fn: libglib-2.80.0-hfc324ee_4.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/libglib-2.80.0-hfc324ee_4.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: h26f9a81_0
        build_number: 0
        depends:
          - bzip2 >=1.0.8,<2.0a0
          - libzlib >=1.2.13,<1.3.0a0
        license: BSD-3-Clause
        license_family: BSD
        md5: 1ddc87f00014612830f3235b5ad6d821
        name: pcre2
        sha256: 4bf7b5fa091f5e7ab0b78778458be1e81c1ffa182b63795734861934945a63a7
        size: 615219
        subdir: osx-arm64
        timestamp: 1708118184900
        version: "10.43"
        fn: pcre2-10.43-h26f9a81_0.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/pcre2-10.43-h26f9a81_0.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: h8fbad5d_2
        build_number: 2
        depends:
          - libiconv >=1.17,<2.0a0
        license: LGPL-2.1-or-later
        md5: 3d216d0add050129007de3342be7b8c5
        name: libintl
        sha256: 21bc79bdf34ffd20cb84d2a8bd82d7d0e2a1b94b9e72773f0fb207e5b4f1ff63
        size: 81206
        subdir: osx-arm64
        timestamp: 1712512755390
        version: 0.22.5
        fn: libintl-0.22.5-h8fbad5d_2.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/libintl-0.22.5-h8fbad5d_2.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: h53f4e23_5
        build_number: 5
        constrains:
          - zlib 1.2.13 *_5
        depends: []
        license: Zlib
        license_family: Other
        md5: 1a47f5236db2e06a320ffa0392f81bd8
        name: libzlib
        sha256: ab1c8aefa2d54322a63aaeeefe9cf877411851738616c4068e0dccc66b9c758a
        size: 48102
        subdir: osx-arm64
        timestamp: 1686575426584
        version: 1.2.13
        fn: libzlib-1.2.13-h53f4e23_5.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/libzlib-1.2.13-h53f4e23_5.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: h93a5062_5
        build_number: 5
        depends: []
        license: bzip2-1.0.6
        license_family: BSD
        md5: 1bbc659ca658bfd49a481b5ef7a0f40f
        name: bzip2
        sha256: bfa84296a638bea78a8bb29abc493ee95f2a0218775642474a840411b950fe5f
        size: 122325
        subdir: osx-arm64
        timestamp: 1699280294368
        version: 1.0.8
        fn: bzip2-1.0.8-h93a5062_5.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/bzip2-1.0.8-h93a5062_5.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: h3422bc3_5
        build_number: 5
        depends: []
        license: MIT
        license_family: MIT
        md5: 086914b672be056eb70fd4285b6783b6
        name: libffi
        sha256: 41b3d13efb775e340e4dba549ab5c029611ea6918703096b2eaa9c015c0750ca
        size: 39020
        subdir: osx-arm64
        timestamp: 1636488587153
        version: 3.4.2
        fn: libffi-3.4.2-h3422bc3_5.tar.bz2
        url: https://conda.anaconda.org/conda-forge/osx-arm64/libffi-3.4.2-h3422bc3_5.tar.bz2
        channel: https://conda.anaconda.org/conda-forge/
      - build: h54d7cd3_11
        build_number: 11
        depends:
          - clang_impl_osx-arm64 18.1.3 hda94301_11
        license: BSD-3-Clause
        license_family: BSD
        md5: 7bdafeb8d61d59551df2417995bc3d46
        name: clang_osx-arm64
        sha256: 595cbec0f835ba16ad551315079193d16fc7f3a4e136aa1045ab9104cac79bf7
        size: 20490
        subdir: osx-arm64
        timestamp: 1712621394350
        version: 18.1.3
        fn: clang_osx-arm64-18.1.3-h54d7cd3_11.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/clang_osx-arm64-18.1.3-h54d7cd3_11.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: hda94301_11
        build_number: 11
        depends:
          - cctools_osx-arm64
          - clang 18.1.3.*
          - compiler-rt 18.1.3.*
          - ld64_osx-arm64
          - llvm-tools 18.1.3.*
        license: BSD-3-Clause
        license_family: BSD
        md5: 90e54a957e833f7cd2412b6d2e1d84fa
        name: clang_impl_osx-arm64
        sha256: f00e3930fa341ad5fa87a90f297b385a949bf2ee100a3a2cc2a135629fde6d7e
        size: 17571
        subdir: osx-arm64
        timestamp: 1712621386541
        version: 18.1.3
        fn: clang_impl_osx-arm64-18.1.3-hda94301_11.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/clang_impl_osx-arm64-18.1.3-hda94301_11.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: h30cc82d_0
        build_number: 0
        constrains:
          - llvm        18.1.3
          - clang-tools 18.1.3
          - clang       18.1.3
          - llvmdev     18.1.3
        depends:
          - libllvm18 18.1.3 h30cc82d_0
          - libxml2 >=2.12.6,<3.0a0
          - libzlib >=1.2.13,<1.3.0a0
          - zstd >=1.5.5,<1.6.0a0
        license: Apache-2.0 WITH LLVM-exception
        license_family: Apache
        md5: 505aef673d805f9efe0c61954a6a99d0
        name: llvm-tools
        sha256: 48eb7b17ca6de1b43dfddc3b4a629a8a9764c9da3f3012980e1b917c71f06a4f
        size: 23023681
        subdir: osx-arm64
        timestamp: 1712517958538
        version: 18.1.3
        fn: llvm-tools-18.1.3-h30cc82d_0.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/llvm-tools-18.1.3-h30cc82d_0.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: h3808999_0
        build_number: 0
        depends:
          - clang 18.1.3.*
          - clangxx 18.1.3.*
          - compiler-rt_osx-arm64 18.1.3.*
        license: Apache-2.0 WITH LLVM-exception
        license_family: APACHE
        md5: 09f614cf0dc4ea2b249c2e522b337730
        name: compiler-rt
        sha256: dfada604649fb2cfa6fb3dbd657fccf81cd01e00a7f6f29da24fc40e36cd51fa
        size: 96152
        subdir: osx-arm64
        timestamp: 1712580507858
        version: 18.1.3
        fn: compiler-rt-18.1.3-h3808999_0.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/compiler-rt-18.1.3-h3808999_0.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: default_h4cf2255_0
        build_number: 0
        constrains:
          - clang-tools 18.1.3.*
          - llvm 18.1.3.*
          - llvm-tools 18.1.3.*
          - llvmdev 18.1.3.*
        depends:
          - clang-18 18.1.3 default_he012953_0
        license: Apache-2.0 WITH LLVM-exception
        license_family: Apache
        md5: efbaa3d968b1dcacba9eb980d1ab66f4
        name: clang
        sha256: 613f4c4773f1dd274d2682a9170d52cb466f437a47ebcad2c2634c3b37aeb73f
        size: 22913
        subdir: osx-arm64
        timestamp: 1712569692457
        version: 18.1.3
        fn: clang-18.1.3-default_h4cf2255_0.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/clang-18.1.3-default_h4cf2255_0.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: h4f39d0f_0
        build_number: 0
        depends:
          - libzlib >=1.2.13,<1.3.0a0
        license: BSD-3-Clause
        license_family: BSD
        md5: 5b212cfb7f9d71d603ad891879dc7933
        name: zstd
        sha256: 7e1fe6057628bbb56849a6741455bbb88705bae6d6646257e57904ac5ee5a481
        size: 400508
        subdir: osx-arm64
        timestamp: 1693151393180
        version: 1.5.5
        fn: zstd-1.5.5-h4f39d0f_0.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/zstd-1.5.5-h4f39d0f_0.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: h30cc82d_0
        build_number: 0
        depends:
          - libcxx >=16
          - libxml2 >=2.12.6,<3.0a0
          - libzlib >=1.2.13,<1.3.0a0
          - zstd >=1.5.5,<1.6.0a0
        license: Apache-2.0 WITH LLVM-exception
        license_family: Apache
        md5: fad73e8421bcd0de381d172c2224d3a5
        name: libllvm18
        sha256: 5a8781ab13b163fd028916d050bb209718b14de85493bb7a4b93ea798998b9fe
        size: 25782519
        subdir: osx-arm64
        timestamp: 1712517407600
        version: 18.1.3
        fn: libllvm18-18.1.3-h30cc82d_0.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/libllvm18-18.1.3-h30cc82d_0.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: h3808999_0
        build_number: 0
        constrains:
          - compiler-rt 18.1.3
        depends:
          - clang 18.1.3.*
          - clangxx 18.1.3.*
        license: Apache-2.0 WITH LLVM-exception
        license_family: APACHE
        md5: 78c11131b59e53aedcf7854956a9347c
        name: compiler-rt_osx-arm64
        noarch: generic
        sha256: 4bbe97d77ae12edd5c0206d014e0473ae8c4fcacbc1e1b21e8e92fd694608301
        size: 10165573
        subdir: noarch
        timestamp: 1712580450851
        version: 18.1.3
        fn: compiler-rt_osx-arm64-18.1.3-h3808999_0.conda
        url: https://conda.anaconda.org/conda-forge/noarch/compiler-rt_osx-arm64-18.1.3-h3808999_0.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: default_h4cf2255_0
        build_number: 0
        depends:
          - clang 18.1.3 default_h4cf2255_0
        license: Apache-2.0 WITH LLVM-exception
        license_family: Apache
        md5: fd98656c5b62774633c84c41f42bdd6d
        name: clangxx
        sha256: 1f9c1605d4f74b1d5df7d44676a5a6c53d542fc8c44d94fcc1d4d1977cede661
        size: 22939
        subdir: osx-arm64
        timestamp: 1712569715149
        version: 18.1.3
        fn: clangxx-18.1.3-default_h4cf2255_0.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/clangxx-18.1.3-default_h4cf2255_0.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: default_he012953_0
        build_number: 0
        constrains:
          - clang-tools 18.1.3
          - clangxx 18.1.3
          - llvm-tools 18.1.3
          - clangdev 18.1.3
        depends:
          - libclang-cpp18.1 18.1.3 default_he012953_0
          - libcxx >=16.0.6
          - libllvm18 >=18.1.3,<18.2.0a0
        license: Apache-2.0 WITH LLVM-exception
        license_family: Apache
        md5: 931dd6124b399ae12172f235f5ace407
        name: clang-18
        sha256: edb5c1e2ffc7704b0e0bce0f5315eb1aba8fd9710e61bcbdeb40e340720123c6
        size: 754206
        subdir: osx-arm64
        timestamp: 1712569562918
        version: 18.1.3
        fn: clang-18-18.1.3-default_he012953_0.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/clang-18-18.1.3-default_he012953_0.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: h4653b0c_0
        build_number: 0
        depends: []
        license: Apache-2.0 WITH LLVM-exception
        license_family: Apache
        md5: 9d7d724faf0413bf1dbc5a85935700c8
        name: libcxx
        sha256: 11d3fb51c14832d9e4f6d84080a375dec21ea8a3a381a1910e67ff9cedc20355
        size: 1160232
        subdir: osx-arm64
        timestamp: 1686896993785
        version: 16.0.6
        fn: libcxx-16.0.6-h4653b0c_0.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/libcxx-16.0.6-h4653b0c_0.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: default_he012953_0
        build_number: 0
        depends:
          - libcxx >=16.0.6
          - libllvm18 >=18.1.3,<18.2.0a0
        license: Apache-2.0 WITH LLVM-exception
        license_family: Apache
        md5: d8e0decc03dadc234e0885bb2a857c68
        name: libclang-cpp18.1
        sha256: a528f933aa430c86591ed94e7eb5e4c16947232f149920250ba78e104d91e0b3
        size: 12809223
        subdir: osx-arm64
        timestamp: 1712569190982
        version: 18.1.3
        fn: libclang-cpp18.1-18.1.3-default_he012953_0.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/libclang-cpp18.1-18.1.3-default_he012953_0.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: h5e7191b_0
        build_number: 0
        constrains:
          - ld 711.*
          - cctools 986.*
          - cctools_osx-arm64 986.*
          - clang >=18.1.1,<19.0a0
        depends:
          - libcxx
          - libllvm18 >=18.1.1,<18.2.0a0
          - sigtool
          - tapi >=1100.0.11,<1101.0a0
        license: APSL-2.0
        license_family: Other
        md5: c751b76ae8112e3d516831063da179cc
        name: ld64_osx-arm64
        sha256: 82f964dcff2052b327762ca44651407451ad396a1540c664928841c72b7cf3c0
        size: 1064448
        subdir: osx-arm64
        timestamp: 1710484550965
        version: "711"
        fn: ld64_osx-arm64-711-h5e7191b_0.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/ld64_osx-arm64-711-h5e7191b_0.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: hd11630f_0
        build_number: 0
        constrains:
          - cctools 986.*
          - clang 18.1.*
          - ld64 711.*
        depends:
          - ld64_osx-arm64 >=711,<712.0a0
          - libcxx
          - libllvm18 >=18.1.1,<18.2.0a0
          - libzlib >=1.2.13,<1.3.0a0
          - sigtool
        license: APSL-2.0
        license_family: Other
        md5: cce200c91b2d291c85e66098fe0d31c2
        name: cctools_osx-arm64
        sha256: 4152323bbb78e2730fea9004333c9c51fb82a9ddd935f005280bf621849ec53d
        size: 1123368
        subdir: osx-arm64
        timestamp: 1710484635601
        version: "986"
        fn: cctools_osx-arm64-986-hd11630f_0.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/cctools_osx-arm64-986-hd11630f_0.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: he4954df_0
        build_number: 0
        depends:
          - libcxx >=11.0.0.a0
        license: NCSA
        license_family: MIT
        md5: d83362e7d0513f35f454bc50b0ca591d
        name: tapi
        sha256: 1709265fbee693a9e8b4126b0a3e68a6c4718b05821c659279c1af051f2d40f3
        size: 191416
        subdir: osx-arm64
        timestamp: 1602687595316
        version: 1100.0.11
        fn: tapi-1100.0.11-he4954df_0.tar.bz2
        url: https://conda.anaconda.org/conda-forge/osx-arm64/tapi-1100.0.11-he4954df_0.tar.bz2
        channel: https://conda.anaconda.org/conda-forge/
      - build: h0d0cfa8_1
        build_number: 1
        depends:
          - icu >=73.2,<74.0a0
          - libiconv >=1.17,<2.0a0
          - libzlib >=1.2.13,<1.3.0a0
          - xz >=5.2.6,<6.0a0
        license: MIT
        license_family: MIT
        md5: c08526c957192192e1e7b4f622761144
        name: libxml2
        sha256: f18775ca8494ead5451d4acfc53fa7ebf7a8b5ed04c43bcc50fab847c9780cb3
        size: 588539
        subdir: osx-arm64
        timestamp: 1711318256840
        version: 2.12.6
        fn: libxml2-2.12.6-h0d0cfa8_1.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/libxml2-2.12.6-h0d0cfa8_1.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: h57fd34a_0
        build_number: 0
        depends: []
        license: LGPL-2.1 and GPL-2.0
        md5: 39c6b54e94014701dd157f4f576ed211
        name: xz
        sha256: 59d78af0c3e071021cfe82dc40134c19dab8cdf804324b62940f5c8cd71803ec
        size: 235693
        subdir: osx-arm64
        timestamp: 1660346961024
        version: 5.2.6
        fn: xz-5.2.6-h57fd34a_0.tar.bz2
        url: https://conda.anaconda.org/conda-forge/osx-arm64/xz-5.2.6-h57fd34a_0.tar.bz2
        channel: https://conda.anaconda.org/conda-forge/
      - build: hc8870d7_0
        build_number: 0
        depends: []
        license: MIT
        license_family: MIT
        md5: 8521bd47c0e11c5902535bb1a17c565f
        name: icu
        sha256: ff9cd0c6cd1349954c801fb443c94192b637e1b414514539f3c49c56a39f51b1
        size: 11997841
        subdir: osx-arm64
        timestamp: 1692902104771
        version: "73.2"
        fn: icu-73.2-hc8870d7_0.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/icu-73.2-hc8870d7_0.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: h44b9a77_0
        build_number: 0
        depends:
          - openssl >=3.0.0,<4.0a0
        license: MIT
        license_family: MIT
        md5: 4a2cac04f86a4540b8c9b8d8f597848f
        name: sigtool
        sha256: 70791ae00a3756830cb50451db55f63e2a42a2fa2a8f1bab1ebd36bbb7d55bff
        size: 210264
        subdir: osx-arm64
        timestamp: 1643442231687
        version: 0.1.3
        fn: sigtool-0.1.3-h44b9a77_0.tar.bz2
        url: https://conda.anaconda.org/conda-forge/osx-arm64/sigtool-0.1.3-h44b9a77_0.tar.bz2
        channel: https://conda.anaconda.org/conda-forge/
      - build: h0d3ecfb_1
        build_number: 1
        constrains:
          - pyopenssl >=22.1
        depends:
          - ca-certificates
        license: Apache-2.0
        license_family: Apache
        md5: eb580fb888d93d5d550c557323ac5cee
        name: openssl
        sha256: 519dc941d7ab0ebf31a2878d85c2f444450e7c5f6f41c4d07252c6bb3417b78b
        size: 2855250
        subdir: osx-arm64
        timestamp: 1710793435903
        version: 3.2.1
        fn: openssl-3.2.1-h0d3ecfb_1.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/openssl-3.2.1-h0d3ecfb_1.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: hf0a4a13_0
        build_number: 0
        depends: []
        license: ISC
        md5: fb416a1795f18dcc5a038bc2dc54edf9
        name: ca-certificates
        sha256: 49bc3439816ac72d0c0e0f144b8cc870fdcc4adec2e861407ec818d8116b2204
        size: 155725
        subdir: osx-arm64
        timestamp: 1706844034242
        version: 2024.2.2
        fn: ca-certificates-2024.2.2-hf0a4a13_0.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/ca-certificates-2024.2.2-hf0a4a13_0.conda
        channel: https://conda.anaconda.org/conda-forge/
    run_exports:
      perl:
        weak:
          - perl >=5.32.1,<5.33.0a0 *_perl5
        noarch:
          - perl >=5.32.1,<6.0a0 *_perl5
  host:
    specs:
      - source: raw
        spec: zlib
    resolved:
      - build: h0d3ecfb_0
        build_number: 0
        depends:
          - libzlib 1.3.1 h0d3ecfb_0
        license: Zlib
        license_family: Other
        md5: 7ae2a86abebc82333e585a40b60fb1ab
        name: zlib
        sha256: c6c947aa8bf6f471f58c37aa7a20bc121adfd1b3a92e3f73e7962b2cfb288990
        size: 85372
        subdir: osx-arm64
        timestamp: 1709241186776
        version: 1.3.1
        fn: zlib-1.3.1-h0d3ecfb_0.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/zlib-1.3.1-h0d3ecfb_0.conda
        channel: https://conda.anaconda.org/conda-forge/
      - build: h0d3ecfb_0
        build_number: 0
        constrains:
          - zlib 1.3.1 *_0
        depends: []
        license: Zlib
        license_family: Other
        md5: 2a2463424cc5e961a6d04bbbfb5838cf
        name: libzlib
        sha256: 9c59bd3f3e3e1900620e3a85c04d3a3699cb93c714333d06cb8afdd7addaae9d
        size: 47040
        subdir: osx-arm64
        timestamp: 1709241137619
        version: 1.3.1
        fn: libzlib-1.3.1-h0d3ecfb_0.conda
        url: https://conda.anaconda.org/conda-forge/osx-arm64/libzlib-1.3.1-h0d3ecfb_0.conda
        channel: https://conda.anaconda.org/conda-forge/
    run_exports:
      zlib:
        weak:
          - libzlib >=1.3.1,<1.4.0a0
  run:
    depends:
      - source: run_export
        spec: libzlib >=1.3.1,<1.4.0a0
        from: host
        source_package: zlib
    constrains: []
    run_exports: null
finalized_sources:
  - url: http://curl.haxx.se/download/curl-8.0.1.tar.bz2
    sha256: 9b6b1e96b748d04b968786b6bdf407aa5c75ab53a3d37c1c8c81cdb736555ccf
system_tools:
  codesign: ""
  rattler_build: 0.14.2
```
