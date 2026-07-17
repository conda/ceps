# CEP XXXX - Specification of <code>conda_build_config.yaml</code> variant configuration files

<table>
<tr><td> Title </td><td> Specification of <code>conda_build_config.yaml</code> variant configuration files </td></tr>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Ryan Keith &lt;rkeith@anaconda.com&gt;</td></tr>
<tr><td> Created </td><td> Jun 4, 2026 </td></tr>
<tr><td> Updated </td><td> Jun 4, 2026 </td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
<tr><td> Requires </td><td> NA </td></tr>
</table>

> The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC2119][RFC2119] when, and only when, they appear in all capitals, as shown here.
>
> [RFC2119]: https://datatracker.ietf.org/doc/html/rfc2119

## Abstract

This CEP standardizes the format of conda build variant configuration YAML files (most commonly named `conda_build_config.yaml` or CBC as a shorthand). The goal being a single, testable contract shared by `conda-build`, `rattler-build`, and channel-wide configuration (for example conda-forge’s and Anaconda’s global CBCs).

## Motivation

Historically, important conda ecosystem files standards have not been fully spec'd. In particular, the CBC file is used for `conda-build` and is a valid input for `rattler-build`. It is used in both recipe and channel specs. It is foundational configuration of `main`, `conda-forge` and `bioconda` in order to set channel global settings so the channel ecosystem can solve globally.

During a recent bug fix for conda-build, it was noticed that the exact same rules were being applied to the CBC file as package recipe files. Though similar, it is important to distinguish their roles and thus provide a rules and a schema for documentation and linters.

Variant configuration drives the build matrix, compiler pins, `zip_keys` coupling, and platform-specific defaults across the ecosystem. Behavior is described primarily in conda-build documentation and implemented in a couple tools, but no CEP defines the file format today.

This CEP proposes a standard for CBC files in order to officially declare what the exact standards are and reduce drift for evolving standards.

## Nomenclature

- **CBC**: informal shorthand for `conda_build_config.yaml`.
- **cbc.yaml**: also another shortand seen in some documentation and in code repositories.  Not used in this document.
- **Variant configuration file** (VCF): a YAML document that supplies the variant dictionary used at render/build time.
- **Canonical filename**: `conda_build_config.yaml` (underscores). This is the name recognized by conda-build discovery, rattler-build legacy loading, and both:
  - [AnacondaRecipes/aggregate](https://github.com/AnacondaRecipes/aggregate/blob/master/conda_build_config.yaml)
  - [conda-forge-pinning-feedstock](https://github.com/conda-forge/conda-forge-pinning-feedstock/blob/main/recipe/conda_build_config.yaml)

## Relationship to other standards

| Standard | Relationship |
|----------|----------------|
| [CEP 24](./cep-0024.md) | The `environment.yml` specification standard. Both use comment-based `# [<expr>]` selectors. |
| [CEP 39](./cep-0039.md) | v1 recipes consume variant keys; CBC is the usual source for global/channel keys like `c_compiler`. |
| [CEP 40](./cep-0040.md) | `variant_config.yaml` in artifacts records keys *used* in one build, not the full CBC. |
| [CEP 34](./cep-0034.md) | `./info/hash_input.json` stores the resolved variant subset that affected the hash. |
| [CEP 14](./cep-0014.md) | Per-recipe `variant:` overrides complement but do not replace CBC. |

## Rationale

The documented purpose of `conda_build_config.yaml` (CBC) is to define *variants*: building a binary package multiple times against different pinned dependencies to support different usage environments (for example, building against different NumPy or Python C ABIs). This is a per-recipe, matrix-generating mechanism, and it is the only purpose the upstream conda-build documentation describes.

A second purpose is built on the same machinery: a centralized CBC serves as a channel-wide ABI/binary-compatibility baseline. By declaring the canonical version of each shared dependency (e.g. `openssl`, `libabseil`, `hdf5`) in a single file, a channel establishes the ABI that all of its packages build against.

The altnerative to not having a centeralized CBC file would be updating many individual recipes. This would become difficult to maintain over time and over a large number of package recipes.

 Both Anaconda's `main` channel and `conda-forge` build from their own global CBC files (`AnacondaRecipes/aggregate` and `conda-forge-pinning`, respectively) and because those baselines can differ, packages from the two channels are not always ABI-compatible. This is one reason mixing the channels in a single environment can cause problems.

These two purposes operate on different axes. The first answers *what to build* (the matrix); the second answers *what to build against* (the baseline). CBC is the shared substrate for both, which is why the baseline role has remained implicit in the upstream documentation despite being the dominant real-world use.

### Document requirements

- A variant configuration file (VCF) is a single YAML document whose root is a mapping.
- The canonical filename is `conda_build_config.yaml`. CBC is informal shorthand used in prose and documentation, not a filename the format defines.
- Keys at the root are either variant keys (arbitrary names that become variables in recipe templating) or one of the reserved keys defined in Reserved top-level keys.

### Variant keys

Variants are defined as name/value pairs. Each such name becomes a variable available to recipe templating, and its value supplies what that variable can be. (Names with special meaning — the [reserved keys](#reserved-top-level-keys) — are the exception.)

- A variant key's name must be a valid Jinja identifier: letters, digits, and underscores, not starting with a digit. **No hyphens**. Any case is fine (`openssl`, `CONDA_BUILD_SYSROOT`).
- Its value is a scalar, or a list of scalars. A bare scalar means a one-element list.
- A scalar is an opaque token — a version (`"1.14.6"`), a `version build` pair (`"3.9.* *netlib"`), a name (`gcc`), a path, an int, or a boolean. It is substituted verbatim; match-spec operators (`>=`, `<`) are not used.
- Quote version-like values so YAML keeps them as strings (`python: ["3.10", "3.11"]`); unquoted, `3.10` parses as the float `3.1`.
- Values are data, not templates — no Jinja (`{{ }}`).

### Build matrix

A variant key with more than one value defines an axis of variation. When several keys each carry multiple values, the builds produced are the Cartesian product of those axes. This is the per-recipe "define variants" purpose: building the same recipe against, for example:

- Building a package against several versions of Python (probably the most common use case)
- Several Python versions crossed with different modalites of a library (such as CPU and GPU verisons)

In practice, channel-wide baselines exercise this very little. In both `AnacondaRecipes/aggregate` and `conda-forge-pinning`, nearly every key holds a single value, and the few multi-valued keys (such as `python`/`numpy`) are coupled with [`zip_keys`](#reserved-top-level-keys) rather than multiplied. The matrix collapses to a near-single point, and the file acts as a set of pinned defaults.

Two mechanisms alter the default product:

- [`zip_keys`](#reserved-top-level-keys) couples axes so they advance together instead of multiplying.
- [Preprocessing selectors](#preprocessing-selectors) remove values that do not apply to the target platform.

Which combinations a tool actually materializes — build order, skipping, deduplication — is outside this specification.

### Reserved top-level keys

Five root-level keys have defined meaning and are not treated as variant keys. They are used to control config file behavior. This set is fixed (conda-build handles them specially in variant parsing):

| Key | Value shape | Role |
|-----|-------------|------|
| `zip_keys` | list of key names, or list of lists of names | Couples variant keys so their value lists advance together by index rather than forming a Cartesian product. |
| `pin_run_as_build` | map of package name → `{min_pin, max_pin}` | Sets the default run pin for packages that are both build and run dependencies. |
| `ignore_version` | list of key names | Suppresses automatic version pinning for the listed keys. |
| `ignore_build_only_deps` | list of key names | Excludes the listed keys from affecting the build environment only. Defaults to `python`, `numpy`. |
| `extend_keys` | list of key names | Names keys whose values aggregate across combined sources instead of being replaced. Includes the reserved keys above and is itself extendable. |

Package names inside `pin_run_as_build` may contain hyphens (e.g. `r-base`); the no-hyphen rule below applies only to top-level key names.

#### `zip_keys` forms

A single group is a flat list:

    zip_keys:
      - python
      - numpy

Multiple independent groups are a list of lists:

    zip_keys:
      - [c_compiler_version, cxx_compiler_version]
      - [python, is_python_min]

Also valid for multiple independent groups (more common as well):

    zip_keys:
      -
        - c_compiler_version
        - cxx_compiler_version
      -
        - python
        - is_python_min

A CBC MUST satisfy, for `zip_keys`:

- every key named in a group is defined in the configuration;
- no key appears in more than one group;
- all keys within a group have value lists of equal length.

### Preprocessing selectors

A line in a CBC may carry a trailing selector, `# [<expr>]`. Before the YAML is parsed, each such line is kept if `<expr>` is truthy and dropped otherwise. Selection is line-by-line on raw text, prior to loading.

`<expr>` is a restricted expression. Comparisons, `and`/`or`/`not`, `in`, attribute access, and a fixed set of calls are allowed, not arbitrary code.

#### Available names

Selectors evaluate against names external to the file:

- **Platform and architecture predicates** (booleans): `linux`, `osx` `win`, `unix`, `linux64`, `win64`, `arm`, `x86`, per-subdir OS/arch names, and `build_platform`.
- **Environment variables**: every set variable is available both as a bare name and via `environ` / `os.environ.get(...)`.

An unknown name (one not defined above) evaluates as `False`, dropping its line. This is how an optional flag works: `# [SOME_FLAG]` is false when unset and true when the variable is present.

Note the truthiness trap with bare flags: a bare `# [FLAG]` is true whenever the variable is a non-empty string — so `FLAG=False` is *truthy* and keeps the line. To gate on an explicit value, compare it: `# [os.environ.get("FLAG", "False") == "True"]`. Both idioms appear in practice — aggregate uses the bare form, conda-forge the explicit `== "True"` form for its CUDA gating.

#### Selectors must not branch on file-defined values

A VCF exists to *declare* the build axes and pins. A selector in a VCF MUST NOT branch on a value the same file defines. In particular, the interpreter-derived names, such as, `py`, `py2k`, `py3k`, `py26`–`py315`, `np`, `pl`, `lua`, `luajit`,  MUST NOT be used: they are computed from the `python`, `numpy`, `perl`, and `lua` variant keys, so branching on them re-derives, inside the file, a value the file is meant to set. That circularity does not belong in a definition.

Per-interpreter conditionals belong in recipe metadata, not in a VCF. Within a VCF, a value that must vary across an axis is expressed by defining the axis directly and, where values must correspond, coupling keys with [`zip_keys`](#reserved-top-level-keys).

> *Why this matters.* Limiting VCF selectors to platform and environment predicates keeps the
> file evaluable from the build target and environment alone — no interpreter/variant namespace,
> no Jinja — which permits a simpler, faster VCF reader than full recipe rendering requires.

### Disallowed in CBCs

- **Jinja templating.** A VCF MUST NOT contain Jinja: neither `{{ ... }}` expressions nor `{% ... %}` statements. A VCF is not rendered as a template — it supplies the values that recipe Jinja later consumes. Selectors (`# [...]`) are the only reprocessing a VCF undergoes.
- **Hyphens in key names.** A top-level variant key name MUST NOT contain `-` (the name is used as a template variable). Hyphenated package names MAY appear as keys under pin_run_as_build (e.g. netcdf-cxx4, r-base). The no-hyphen rule applies only to top-level CBC keys.
- **Interpreter-derived selectors.** `py`, `np`, and the other variant-derived selector names MUST NOT appear in a VCF (see [Preprocessing selectors](#preprocessing-selectors)).

### Merging

A build may draw variant configuration from more than one CBC. This CEP specifies how an ordered sequence of sources combines into a single variant dictionary.

Sources are applied in order. A later source's value **replaces** an earlier one for that key.

Example (later source `b` wins for both keys):

```python
a = {"python": ["2.7", "3.5"], "numpy": ["1.10", "1.11"]}
b = {"python": ["3.14", "3.15"], "numpy": ["2.3", "2.5"]}
# merged = {"python": ["3.14", "3.15"], "numpy": ["2.3", "2.5"]}
```

#### Reserved keys

Reserved keys are **additive** across sources (they do not last-wins overwrite):

| Key | Accumulation |
|-----|----------------|
| `pin_run_as_build` | Map merge (later entry for the same package name wins) |
| `ignore_version`, `ignore_build_only_deps`, `extend_keys` | List concat, then de-duplicated |
| `zip_keys` | Whole groups are appended and de-duplicated; existing groups are not grown or edited in place |

#### `extend_keys`

Keys listed in `extend_keys` accumulate across sources.  Values are concatenated and then de-duplicated (order not preserved).

Every source that sets an extended key MUST also list that key under `extend_keys`, or the merge MUST fail.

## Backwards compatibility

This CEP largely specifies existing conda-build behavior; most of it is descriptive and introduces no change. The normative constraints have limited impact:

- **Jinja prohibition** and the **no-hyphen rule** for key names match what conda-build already does
- **Both channel baselines already conform.** `AnacondaRecipes/aggregate` and `conda-forge-pinning` use only platform and environment-driven selectors; neither uses interpreter-derived selectors. The selector restriction costs them nothing.
- **The one potential breakage** is a recipe-local CBC that uses an interpreter-derived selector (`# [py<X]`, `# [np...]`). Such files would need those conditionals moved into recipe metadata. Whether any exist in practice is an open question (see below); until that is settled, the all-CBC scope of this rule is provisional.

## Alternatives

1. **Specify the full renderer, including Jinja in CBCs.** Rejected. Treating a VCF as a template would preserve conda-build's current shared-rendering behavior but defeats a primary goal of this CEP: a CBC that requires full recipe rendering cannot be read by a simple, fast reader. Keeping CBCs declarative is the point.
2. **Leave selectors unrestricted.** Rejected. Permitting interpreter-derived selectors keeps the circularity described in [Preprocessing selectors](#preprocessing-selectors) and forces any reader to construct the full variant-derived namespace, which precludes a format-only reader.

## Open questions

1. **Do any recipe-local CBCs use interpreter-derived selectors?** This determines whether the interpreter-selector MUST NOT can apply to all CBCs or must be scoped to channel-baseline files. Needs a survey of recipe-local `conda_build_config.yaml` files in the wild for `# [py`, `# [np` usage.  A strong perference to move away from this practice and move that information into the recipe would be highly endorsed.
2. **Is the reserved-key set stable across conda-build versions?** This CEP treats `zip_keys`, `pin_run_as_build`, `ignore_version`, `ignore_build_only_deps`, and `extend_keys` as the closed set, per current source. Future conda-build changes could alter it; the CEP may need a versioning story if so.
3. **Should the interpreter-selector restriction be MUST NOT or SHOULD NOT?** Currently MUST NOT, on the grounds that no known file violates it. If review surfaces legitimate uses, this relaxes to SHOULD NOT.

## FAQ

**Does this CEP change how conda-build works?**
Mostly no — it writes down existing behavior (file shape, keys, merging, selector evaluation). The one tightening is the selector restriction, which no known conforming file violates.  Accepting this as a standard would allow some performance improvements.

**Why isn't rattler-build's variant format covered?**
rattler-build has its own native format (`variants.yaml`, with `if`/`then`/`else` maps) that is a different artifact. rattler-build can also read conda-build-format VCFs, but specifying its native format and any compatibility mapping is out of scope here.

**What does a VCF selector actually evaluate against?**
Platform/architecture predicates and environment variables — nothing derived from the file's own variant keys. An unknown name evaluates as `False`. See [Preprocessing selectors](#preprocessing-selectors).

## Sample implementation

Current behavior is defined by conda-build's variant handling:
- `conda_build/variants.py`:
  - `find_config_files`
  - `parse_config_file`
  - `validate_spec`
  - `combine_specs`
  - `get_package_combined_spec`
- `conda_build/metadata.py`:
  - `get_selectors`
  - `eval_selector`
  - `select_lines`

## References

- [conda-build: Build variants](https://docs.conda.io/projects/conda-build/en/latest/resources/variants.html)
- [conda-build: Preprocessing selectors](https://docs.conda.io/projects/conda-build/en/latest/resources/define-metadata.html#preprocessing-selectors)
- [conda-build `variants.py`](https://github.com/conda/conda-build/blob/main/conda_build/variants.py) — reserved keys, `validate_spec`, `combine_specs`, config-file discovery
- [conda-build `metadata.py`](https://github.com/conda/conda-build/blob/main/conda_build/metadata.py) — `get_selectors`, `eval_selector`, selector namespace and evaluation
- [AnacondaRecipes/aggregate `conda_build_config.yaml`](https://github.com/AnacondaRecipes/aggregate/blob/master/conda_build_config.yaml) — Anaconda `main` channel baseline
- [conda-forge-pinning-feedstock `conda_build_config.yaml`](https://github.com/conda-forge/conda-forge-pinning-feedstock/blob/main/recipe/conda_build_config.yaml) — conda-forge channel baseline
- [rattler-build: Variant configuration](https://prefix-dev.github.io/rattler-build/latest/variants/) — native rattler format (out of scope; for contrast)

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
