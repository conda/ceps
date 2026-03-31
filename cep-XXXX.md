# CEP XXXX - The staging output in v1 recipes / rattler-build

<table>
<tr><td> Title </td><td> The staging output in v1 recipes / rattler-build </td>
<tr><td> Status </td><td> In Discussion </td></tr>
<tr><td> Author(s) </td><td> Wolf Vollprecht &ltw.vollprecht@gmail.com&gt; </td></tr>
<tr><td> Created </td><td> Nov 27, 2024</td></tr>
<tr><td> Updated </td><td> </td></tr>
<tr><td> Discussion </td><td>  </td></tr>
<tr><td> Implementation </td><td> rattler-build </td></tr>
</table>

> The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC2119][RFC2119] when, and only when, they appear in all capitals, as shown here.

## Abstract

This CEP defines staging outputs for v1 multi-output recipes.

## Background

Sometimes it is very useful to build some code once, and then split it into multiple build artifacts (such as shared library, header files, etc.). For this reason, `conda-build` has a special, implicit top-level build.

There are many downsides to the behavior of `conda-build`: it's very implicit, hard to understand and hard to debug (for example, if an output is defined with the same name as the top-level recipe, this output will get the same requirements attached as the top-level).

For the v1 spec we are attempting to formalize the workings of the "top-level" build. For this, we introduce a new `staging` output, that has the same values as a regular output, but does not produce a package artifact. Instead, we keep changes from the `staging` output in a temporary location on the filesystem and restore from this checkpoint when building other outputs that _inherit_ from this `staging` cache.

## Specification

[CEP 13](./cep-0013.md) and [CEP 14](./cep-0014.md) define the v1 recipe format. This CEP extends these specifications by introducing _staging outputs_ that can exist alongside _package outputs_.

### Staging outputs

A recipe can have zero or more staging outputs. A staging output is defined in the outputs section, and differs from a regular output in the following ways:

- The `package` subsection MUST NOT be present
- A `staging` subsection MUST be present, with a single key `name`. The value MUST be a string, following same rules as `package.name`. Every name MUST be unique among all package and staging outputs.
- In the `requirements` subsection, the `run` and `run_constraints` fields MUST NOT be present.
- In the `build` subsection, no other fields than `script` MUST be present.

### Outputs inheritance

A new `inherit` field is added to both staging and package outputs. When present, it MAY specify an output to inherit from.

When present, the `inherit` field MUST have one of the three following values:

- `null` indicating "top-level" inheritance (the default, when no `inherit` field is present)
- a string specifying the output to inherit from
- a map, with the following keys:
  - a REQUIRED `from` key, specifying the output to inherit from, as a string
  - an OPTIONAL `run_exports` key, specifying whether to inherit `run_exports` (defaults to true)

Both staging and package outputs MAY inherit, however, a staging output MUST NOT inherit from a package output.

When inheriting, values from `build` and `about` sections MUST be deeply merged with the values from the inherited output, except for the value of `build.script`.

Requirements MUST NOT be inherited. However, `run_exports` MUST be, unless the `run_exports` key is set to `false` in the `inherit` map. The implementation MUST support ignoring Specific run-exports either in the staging output or in the package output (both follow the same rules).

### Top-level inheritance

Inheriting from the top-level is a special case of regular "staging" inheritance. If the output does not specify any `inherit` key or explicitly sets `inherit: null` then the output inherits from the top-level. The `recipe.version`, `source`, `build` and `about` top-level fields MUST be applied to the output. In the case of top-level inheritance, `requirements` and `build.script` are forbidden and thus ignored. This unifies the rules for both staging and top-level.

### File filtering

A new `build.files` field is added to package outputs. It can be used to restrict which files from `$PREFIX` are included in the package output.

When the field is not present, the output follows the usual rules for determining the files to include.

When it is present, it MUST either be:

- a list of include patterns
- a map with at least one of the following keys:
  - `include` specifying a list of include patterns (defaults to `[**]`)
  - `exclude` specifying a list of exclude patterns (defaults to empty)

In other to determine the files to include in a package output, the implementation MUST first determine the list of new files in the `$PREFIX`. This list MUST then be filtered to include only files matching at least one of the include patterns. Afterwards, all files matching at least one of the exclude patterns MUST be removed from it.

### Example

A recipe with staging output looks as follows:

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
      version: "1.0.0"

    # long form of newly added `inherit` key
    inherit:
      from: foo-cache
      run_exports: false

    build:
      files:
        - include/

  - package:
      name: foo
      version: "1.0.0"

    # short form, inherits run exports by default
    inherit: foo-cache

    # will bundle everything else except files already present in `foo-headers`
    requirements:
      host:
        - ${{ pin_subpackage("foo-headers", exact=True) }}
```

### Building outputs

When computing variants and used variables, the implementation MUST look at the union of a given output and the outputs it inherits from. That means, even if a package output does not define any requirements, the inherited staging output could introduce variants. In the example, the `foo-cache` output would add a variant for the `c_compiler`.

When executing the recipe, the implementation MUST build the inherited outputs that are appropriate for the current variant first. This is computed by looking at all "used-variables" for the inherited output and computing a "hash" for it. The build itself MUST be executed in the same way as any other build.

The variant keys that are injected at build time are the subset used by the inherited output.

When the build of an inherited output is done, the newly created files MUST be moved outside of the `host-prefix`. Post-processing MUST NOT be performed on the files beyond memorizing what files contain the `$PREFIX` (which is later replaced in binaries and text files with the actual build-prefix). The host environment (`$PREFIX`) and the source directory MUST be restored to the original state, including reverting any changes that were made by the build script.

When the inheriting output is being built, these changes MUST be restored. If the two builds were not running in the same exact location, the path leading up to the work directory and the host prefix MUST be replaced in the inherited artifacts (for example when running time-stamped builds in folders such as `/folder/to/bld/libfoo_1745399500/{work_dir,h_env_...}`).

When a package output adds a `source` and inherits from an output, the user is responsible not to clobber files (e.g. by using `target_directory`). The build program SHOULD warn if files are overwritten in the work directory.

New files in the prefix (from the staging output) can be used in the outputs with the `build.files` key.
