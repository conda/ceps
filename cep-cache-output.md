# CEP for the staging output in v1 recipes / rattler-build

<table>
<tr><td> Title </td><td> The staging output in v1 recipes / rattler-build </td>
<tr><td> Status </td><td> In Discussion </td></tr>
<tr><td> Author(s) </td><td> Wolf Vollprecht &ltw.vollprecht@gmail.com&gt; </td></tr>
<tr><td> Created </td><td> Nov 27, 2024</td></tr>
<tr><td> Updated </td><td> </td></tr>
<tr><td> Discussion </td><td>  </td></tr>
<tr><td> Implementation </td><td> rattler-build </td></tr>
</table>

## Abstract

This CEP aims to define the staging output for v1 multi-output recipes.

## Background

Sometimes it is very useful to build some code once, and then split it into multiple build artifacts (such as shared library, header files, etc.). For this reason, `conda-build` has a special, implicit top-level build.

There are many downsides to the behavior of `conda-build`: it's very implicit, hard to understand and hard to debug (for example, if an output is defined with the same name as the top-level recipe, this output will get the same requirements attached as the top-level).

For the v1 spec we are attempting to formalize the workings of the "top-level" build. For this, we introduce a new `staging` output, that has the same values as a regular output, but does not produce a package artifact. Instead, we keep changes from the `staging` output in a temporary location on the filesystem and restore from this checkpoint when building other outputs that _inherit_ from this `staging` cache.

## Specification

The staging output looks as follows:

```yaml
outputs:
  - staging:
      name: foo-cache   # required, string, follows rules of `PackageName`

    source:
      - url: https://foo.bar/source.tar.bz
        sha256: ...

    requirements:
      build:
        - ${{ compiler('c') }}
        - cmake
        - ninja
      host:
        - libzlib
        - libfoo
      # the `run` and `run_constraints` sections are not allowed here
      ignore_run_exports:
        by_name:
          - libfoo

    build:
      # only the script key is allowed here
      script: build_cache.sh

  - package:
      name: foo-headers

    # long form of newly added `inherit` key
    inherit:
      from: foo-cache
      run_exports: false

    build:
      files:
        - include/

  - package:
      name: foo

    # short form, inherits run exports by default
    inherit: foo-cache

    # will bundle everything else except files already present in `foo-headers`
    requirements:
      host:
        - ${{ pin_subpackage("foo-headers", exact=True) }}
```

> [!WARNING]
> When using `outputs` we are going to remove the implicit `build.script` pointing to `script.sh`. Going forward, the script name / content has to be set explicitly.

When computing variants and used variables, rattler-build looks at the union of a given `output` and the `staging` cache. That means, even if an output does not define any requirements, the `staging` cache would still add a variant for the `c_compiler`.

When rattler-build executes the recipe, it will start by building the `staging` cache output that is appropriate for the current variant. This is computed by looking at all "used-variables" for the `staging` cache output and computing a "hash" for it. The build itself is executed in the same way as any other build.

The variant keys that are injected at build time is the subset used by the `staging` output.

When the `staging` build is done, the newly created files are moved outside of the `host-prefix`. Post-processing is not performed on the files beyond memoizing what files contain the `$PREFIX` (which is later replaced in binaries and text files with the actual build-prefix).

The cache restores files that were added to the host environment (`$PREFIX`) and the "dirty" source directory, including any changes that were made by the build script. They are cloned to a special cache location from which they are restored.

If the `staging` build and the package build are not running in the same exact location, the path leading up to the work dir / host prefix needs to be replaced in the `staging` artifacts (for example when running time-stamped builds in folders such as `/folder/to/bld/libfoo_1745399500/{work_dir,h_env_...}`).

When a package output adds a `source` and inherits from a cache, care must be taken by the user to not clobber files (e.g. by using `target_directory`). The build program should warn if files are overwritten in the work dir.

New files in the prefix (from the cache) can be used in the outputs with the `build.files` key:

```yaml
outputs:
  - cache:
      name: foo-cache

  - package:
      name: foo-headers

    inherit:
      name: foo-cache
      run_exports: false

    build:
      files:
        - include/**

  - package:
      name: libfoo

    inherit: foo-cache

    build:
      files:
        - lib/**

  - package:
      name: foo-devel

    inherit: foo-cache

    requirements:
      run:
        - ${{ pin_subpackage("libfoo") }}
        - ${{ pin_subpackage("foo-headers") }}
```

The glob list syntax can also be a dictionary with `include / exclude` keys, e.g.

```yaml
files:
  include:
    - include/**
  exclude:
    - lib/**
```

## The `inherit` key and the logic of inheritance

The `inherit` key is used to inherit from a staging output. We also generalize the logic to "top-level" inheritance, which is what happens when the inherit key is set to `null`.

Both, `staging` and `package` outputs can inherit, however, a `staging` cannot inherit from a `package`.

When inheriting, values from `build` and `about` are deeply merged with the values from the staging output, except for the value of `build.script`.

Requirements are not inherited, however, `run_exports` are. The inheritance of `run_exports` can be disabled by setting the `run_exports` key to `false` in the `inherit` map. To ignore certain run-exports they can be either ignored in the staging output or in the package output (both follow the same rules).

### Top-level inheritance

Inheriting from the top-level is a special case of regular "staging" inheritance. If the output does not specify any `inherit` key or explicitly sets `inherit: null` then we inherit from the top-level and apply `recipe.version`, `source`, `build` and `about` from the top-level to each output. In the case of top-level inheritance, requirements and build script are forbidden and thus ignored. This unifies the rules for both cache and top-level.
