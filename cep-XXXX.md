# CEP XXXX - Specification of <code>environment.yml</code> input files

<table>
<tr><td> Title </td><td> CEP XXXX - Specification of <code>environment.yml</code> input files </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Jaime Rodríguez-Guerra &lt;jaime.rogue@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> June 4, 2024 </td></tr>
<tr><td> Updated </td><td> June 4, 2024 </td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/81 </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
</table>

## Abstract

This CEP standardizes the format of `environment.yml` input files for conda clients.

## Motivation

The motivation of this CEP is merely informative. It describes the details of an existing file format.

## Nomenclature

The `environment.yml` file format was introduced by `conda env`. It has been traditionally referred to as "the YAML input file", but other YAML files exist in the ecosystem now. To avoid confusion, in this CEP we will only use the term `environment.yml`. Do note that the actual filename of an input file using this format might be a different one (e.g. `env.yml`).

## Specification

`environment.yml` files are YAML documents that encode the necessary information to create a new conda environment. They can contain up to seven top-level keys:

- `name`: The preferred name for the environment.
- `prefix`: The preferred full path to the environment. Often ignored.
- `dependencies`: List of package specifications that MUST be installed in the new environment.
- `channels`: conda channels that will be used to resolve the dependencies.
- `variables`: Environment variables that SHOULD be added to the `conda-meta/state` file in the resulting environment.
- `platforms`: Target subdirs for the solver.
- `category`: Free-form field to label the dependencies as a group.

Additional sections can be present, but they MUST be ignored and the user SHOULD receive an informative warning about them.

The file name is not standardized, but the extension MUST be `yml` or `yaml`.

### `name` and `prefix`

Optional, `str`.

Both fields refer to the _preferred_ name or path for the newly created environment. Tools SHOULD allow these suggestions to be overridden by the user with additional CLI flags or equivalent. If the proposed environment path exists, tools MUST NOT overwrite silently by default.

Special names `base` and `root` SHOULD NOT be accepted. Prefixes targetting protected system paths SHOULD be rejected. Paths can contain tildes (`~`) and environment variables, and they MUST be expanded when present.

The name of the environment (and the last component of the expanded `prefix` path) MUST NOT contain any of these characters: `/`, ` `, `:`, `#`.

### `dependencies`

Required, `list[str | dict[str, Any]]`.

The simplest form for this section is a list of `str` encoding `MatchSpec`-compatible requirements. These items MUST be processed as conda requirements and submitted to the solver (along with `channels`) to obtain the contents for the resulting conda environment.

This section can also contain "subsection" dictionaries that map `str` to arbitrary values. Each key refers to a non-conda installer tool that will process the associated contents as necessary. The additional subsections MUST be processed after the conda requirements. They SHOULD only add new contents. These keys SHOULD NOT overwrite existing contents.

Currently known subsections include `pip`, the contents of which encode a list of `str` referring to PyPI requirements. How this list is processed is left as an implementation detail, but common approaches involve invoking the `pip` command-line directly.

Additional subsections are allowed. The conda client MUST error out if it cannot process unknown sections.

### `channels`

Optional, `list[str]`.

These are the conda channels that will be queried to solve the requirements added in `dependencies`. They can be expressed with names, URLs and local paths.

If not specified, the conda client MUST use the default configuration. When specified, these channels MUST be used to populate the channel list passed to the solver. Then default channel configuration MUST be appended, unless the special name `nodefaults` is present. When this is the case, the default configuration MUST no be appended. The `nodefaults` name MUST NOT be passed to the solver.

### `variables`

Optional, `dict[str, str]`.

Keys MUST be valid environment variable names for the target operating system. We recommend sticking to names compatible with both Windows and POSIX standards. Values SHOULD be `str`. If they are not, they MUST be converted to `str`.

These contents SHOULD be dumped into the `conda-meta/state` file of the target environment, or equivalent, so they can be set upon environment activation.

### `platforms`

Optional, `list[str]`.

Platforms for which the environment must be solved. Mostly used by tools that generate lockfiles
without installing to a prefix on the running machine. Each string MUST belong to the set of
valid `subdirs`, with one exception: `noarch` MUST be rejected as a valid platform value.

In the absence of the field, the single value MUST be assumed to correspond to a user-specified
value, falling back to the running platform value . For example, running on Linux x86_64 the `platforms` would default to `[linux-64]`.

### `category`

Optional, `str`.

A free-form field where users can annotate the type of dependencies handled in the environment
file. For example, `dev` or `test`.  Mostly used by tools that generate lockfiles.

## Examples

Simplest possible `environment.yml`:

```yaml
dependencies:
  - numpy
```

With a name:

```yaml
name: test
dependencies:
  - numpy >=1.10
```

With channels:

```yaml
name: test
channels:
  - conda-forge
dependencies:
  - numpy
```

With a `pip` section:

```yaml
name: test
channels:
  - conda-forge
dependencies:
  - numpy
  - pip:
      - scipy
```

With variables:

```yaml
name: test
channels:
  - conda-forge
dependencies:
  - numpy
variables:
  MY_ENV_VAR: "My Value"
```

With platforms:

```yaml
name: test
channels:
  - conda-forge
dependencies:
  - numpy
platforms:
  - linux-64
```

## Reference

- [Allowed extensions](https://github.com/conda/conda/blob/24.5.0/conda/env/specs/yaml_file.py)
- [Allowed keys](https://github.com/conda/conda/blob/24.5.0/conda/env/env.py#L25)
- [Extra subsections in `dependencies`](https://github.com/conda/conda/blob/841d9d57fd96ad27cda4b7c43549104a96f961ce/conda/cli/main_env_create.py#L167-L185)

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
