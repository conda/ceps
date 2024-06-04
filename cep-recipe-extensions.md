# Extensions to the recipe spec

This document describes extensions to the recipe specification as merged in
cep-14.

## The `build.post_process` section

The `conda_build_config.yaml` configuration file has ways to specify
post-processing steps. These are regex replacements that are performed on any
new files.

Instead of adding these instructions to the `conda_build_config.yaml`, we
decided to add a new section to the recipe spec: `build.post_process`. This
section is a list of dictionaries, each with the following keys:

- `files`: globs to select files to process
- `regex`: the regex to apply
- `replacement`: the replacement string

The regex specification follows Rust `regex` syntax. Most notably, the
replacement string can refer to capture groups with `$1`, `$2`, etc. This also
means that replacement strings need to escape `$` with `$$`.

Internally, we use `replace_all` from the `regex` crate. This means that the
regex is applied to the entire file, not line by line.

### Example for `post_process`

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

## Files selector in the `build` section

A `files` key is added to the `build` section to simplify the inclusion /
exclusion of files in the package.

This key accepts a list of globs that are used to select files to include in the
package.

```yaml
build:
  files:
    - "*.txt"
    - "*.md"
```

This is especially useful when building multiple outputs, as the same build
script can be used for all outputs, but the files to include can be different.
The globs are evaluated against any new files in the prefix, after the build
script has been run.

Files that are not selected by the globs are excluded from the package.

## Update to the "globs" definition

Anywhere the recipe format accepts a list of globs is extended to accept:

- a single glob (`files: foo/*.txt`)
- a list of globs (`files: [foo/*.txt, bar/*.txt]`)
- a dictionary with `include` and `exclude` keys (`files: {include: [foo/*.txt],
  exclude: [foo/bar.txt]}`), where `include` and `exclude` are lists of globs.

The lists are "conditional" lists and can contain `if` and `else` statements.

A single glob or a list of globs is equivalent to a dictionary with only an
`include` key.

The evaluation of the globs is done in two steps:

- first record all matches for the `include` globs. If no `include` globs are
  given but an `exclude` glob is provided, all files are included.
- Any file that matched an `include` glob is tested against the `exclude` globs.
  If it matches an `exclude` glob, it is removed from the list of files to
  include. If no exclude globs are given, no files are removed.

### Example for `glob` definition

For example:

```yaml
# single glob
files: foo/*.txt

# list of globs
files:
  - foo/*.txt
  - bar/*.txt
  - if: win
    then:
      - win.txt

# dictionary with include and exclude keys
files:
  include:
    - *.txt
  exclude:
    - foo.txt
```

In conda-build, this is discussed here: [Link to PR
5216](https://github.com/conda/conda-build/pull/5216)

## Compression level

There are use cases where it is interesting for a output to set the compression
level - for example when packaging pre-compressed data. We would like to extend
the recipe format so that each output is able to set a "default" compression
level with the following syntax:

```yaml
build:
  compression_level: 1-10 # (integer)
```

The compression level maps to the following levels in the `.zstd` and `bz2`
formats:

- `zstd`: 1-19 (1 = 1, 10 = 19)
- `bz2`: 1-9 (1 = 1, 10 = 9)

Note that this compression level can still be overridden by the command line. It
also does not define wether a `.conda` or `.tar.bz2` file is created.

## System requirements

This is a new section in the `build` section that defines the lower bound system
requirements for a given package.

In this section you can define the "virtual" packages that will be injected in
the `host` sections of the specs:

```yaml
build:
  system_requirements:
    # this one is used on `osx-*` platforms
    - osx: 11.0 # (or should we call this / alias it to `macos`?)
    # the following are used on `linux-*` platforms
    - glibc: 2.17
    - linux: 3.10
    # the following is used on `win-*` platforms
    - win: 10.1
```

The system requirements are used to inject virtual packages in the `host`
section of the recipe. They will also automatically add a dependency in the
`run` section of the recipe, e.g. `__glibc >=2.17`, or `__osx >=11.0`.
