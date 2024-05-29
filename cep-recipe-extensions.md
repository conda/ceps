# Extensions to the recipe spec

This document describes extensions to the recipe specification as merged in cep-14.

## The `build.post_process` section

The `conda_build_config.yaml` configuration file has ways to specify post-processing steps. These are regex replacements that are performed on any new files. 

Instead of adding these instructions to the `conda_build_config.yaml`, we decided to add a new section to the recipe spec: `build.post_process`. This section is a list of dictionaries, each with the following keys:

- `files`: globs to select files to process
- `regex`: the regex to apply
- `replacement`: the replacement string

The regex specification follows Rust `regex` syntax. Most notably, the replacement string can refer to capture groups with `$1`, `$2`, etc.
This also means that replacement strings need to escape `$` with `$$`.

Internally, we use `replace_all` from the `regex` crate. This means that the regex is applied to the entire file, not line by line.

### Example

```yaml
build:
  post_process:
    - files:
        - "*.txt"
      regex: "foo"
      replacement: "bar"
    - files:
        - "*.cmake"
      regex: "/sysroot/"
      replacement: "$${PREFIX}/"
```

## Globs, positive and negative

Following some community discussion we would like to extend the recipe format in such a way that anywhere where a list of globs is accepted, we alternatively accept a dictionary with `include` and `exclude` keys. The values of these keys are lists of globs that are included or excluded respectively.

For example:

```yaml
files:
  include:
    - "*.txt"
  exclude:
    - "foo.txt"
```

The evaluation would go as follows:

- first record all matches for the `include` globs
- then remove all matches for the `exclude` globs

In conda-build, this is discussed here: [Link to PR 5216](https://github.com/conda/conda-build/pull/5216)

## Compression level

There are use cases where it is interesting for a output to set the compression level - for example when packaging pre-compressed data. We would like to extend the recipe format so that each output is able to set a "default" compression level with the following syntax:

```yaml
build:
  compression_level: 1-10  # (integer)
```

The compression level maps to the following levels in the `.zstd` and `bz2` formats:

- `zstd`: 1-19 (1 = 1, 10 = 19)
- `bz2`: 1-9 (1 = 1, 10 = 9)

Note that this compression level can still be overridden by the command line.
It also does not define wether a `.conda` or `.tar.bz2` file is created.


## System requirements

This is a new section in the `build` section that defines the lower bound system requirements for a given package.

In this section you can define the "virtual" packages that will be injected in the `host` sections of the specs:

```yaml
build:
  system_requirements:
    # this one is used on `osx-*` platforms
    - osx: 11.0   # (or should we call this / alias it to `macos`?)
    # the following are used on `linux-*` platforms
    - glibc: 2.17
    - linux: 3.10
    # the following is used on `win-*` platforms
    - win: 10.1
```

The system requirements are used to inject virtual packages in the `host` section of the recipe. They will also automatically add a dependency in the `run` section of the recipe, e.g. `__glibc >=2.17`, or `__osx >=11.0`.