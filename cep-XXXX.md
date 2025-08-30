# CEP XXXX - Improving dependency export infrastructure

<table>
<tr><td> Title </td><td> Improving dependency export infrastructure </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Axel Obermeier &lt;h.vetinari@gmx.com&gt;</td></tr>
<tr><td> Created </td><td> Aug 29, 2025 </td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/129 </td></tr>
<tr><td> Implementation </td><td> N/A </td></tr>
</table>

## Abstract

This CEP proposes to overhaul the way that packages "export" some required dependency
or constraint, in a way that considers both the source environment during the build phase
(one of `build:`, `host:` and `run:`) as well as the target environment where the respective
dependency or constraint should be applied. This has a wide variety of important uses which
are so far difficult or impossible to express, in addition to increasing clarity.

This document builds upon [CEP 13](cep-0013.md) and [CEP 14](cep-0014.md), which define what
is known as the "v1" recipe format.

## History

From the beginning, one of the big advantages of `conda` over `pip` has been the ability to
track dependencies sufficiently well in order to be able to share artefacts between packages,
rather than vendoring dependent libraries for every consumer.

In contrast to static or header-only libraries, a shared library `foo` occurs not just during build
time of `bar` (the headers for `# include <foo.h>` to work and `libfoo.so` for linkage to succeed),
but needs to be present in the final environment for `bar` as well. Aside from corner-cases,
this runtime dependency *always* follows, and it is therefore natural to ask the build system to do
this work for us.

This is what the original [design discussion](https://github.com/conda/conda-build/issues/1142) started
out from, which was first implemented first as [`pin_downstream`](https://github.com/conda/conda-build/commit/e344bbae369658ca7e2defab8a3960d8570fbf8a)
and soon after renamed to [`run_exports`](https://github.com/conda/conda-build/commit/d90aa3135cc81a5db28e8160b521f11d27083453).
The original [documentation](https://github.com/conda/conda-docs/pull/414) for this feature provides
additional context.

This yielded a feature that at the time of conda-build 3.0.0 (CB3)
[looked like](https://github.com/conda/conda-build/blob/3.0.0/tests/test-recipes/variants/10_runtimes/uses_run_exports/meta.yaml):

```yaml
build:
  run_exports:
    - foo  {{ pin_compatible('foo') }}

requirements:
  build:
    - foo
```

It's worth noting that the introduction of "variants" and "run_exports" happened during the same CB3 timeframe
which also saw the introduction of the separation into `build:`/`host:`/`run:` environments (necessary to correctly
handle more complex scenarios like cross-compilation). As well as can be gleaned from the history of the repository,
it appears that the design for run-exports did not originally take this new tripartite environment separation into
account.

This was [rectified](https://github.com/conda/conda-build/commit/f7133b61c75ba1b5c82b5fb20729a37d05ae28a5)
by introducing a separation into strong and weak run-exports, where the scenario described above is default, in
which a `host:` dependency exports a dependency to `run:`, whereas "strong" exports are necessary for a `build:`
dependency to have the same effect (in some way, the jump between `build:` and `run:` is farther than the one
between `host:` and `run:`, and hence needs a bigger push).

However, this doesn't cover the full gamut of scenarios how packages may influence or constrain each other
between environments, and opens further questions along the lines of:
> If `qux` has a strong run-export, and appears in a `run:` environment of another package,
  does the export trigger or not?

Later still, the constraint variants `weak_constrains` and `strong_constrains` were
[added](https://github.com/conda/conda-build/pull/4125).

The v1 recipe format moved the `run_exports:` key from the `build:` section to the `requirements:` of the
respective output, but otherwise did not change the semantics of this feature, aside from renaming
`run_constrained` to `run_constraints` and `{weak,strong}_constrains` to `{weak,strong}_constraints`.

### Run-exports vs. noarch

In 2020, a `noarch:` type of run-exports got [added](https://github.com/conda/conda-build/pull/3868); the
design for this seems to come only from comments in that PR and boils down to:
> > > Ray Donnelly: Do we not really want to use a different run_export type here? Dropping all but the package name?
> >
> > Isuru Fernando: I don't understand. Are you suggesting a different run_exports scheme ('noarch' in addition to
> > 'weak', 'strong') that would be applied if the package is a dependency of a `noarch` package?
>
> Ray Donnelly: I am.

This is a relatively little-used feature, c.f. this approximate [search](https://github.com/search?q=org%3Aconda-forge+%2F%28%3Fs%29%5Csrun_exports%3A.*noarch%3A%2F+path%3Arecipe%2F*.yaml&type=code)
(note: many false positives, but should be exhaustive), though crucially including core packages like
python and R, which are of course key use-cases for building noarch consumers on top.

Perhaps most notably, since the linked PR, regular run-exports (either weak or strong) do not apply to
`noarch: {generic, python}` packages anymore, as thereafter they had their own special export type.

## Motivation

One key motivation for this proposal is that even with the weak/strong distinction, run-exports are not
powerful enough to handle relevant scenarios that are a natural consequence of the separation into
`build:` / `host:` / `run:` environments.

Abstractly speaking, this separation introduces more cases where one wants to express relations between
environments, e.g. from `build:` to `host:` (see <https://github.com/conda/ceps/issues/77>). For this case
in particular, the urgency was reduced by the fact that it could be passably emulated by using strong
run-exports; while this would "over-export" things into the `run:` environment, this is harmless in many cases.

However, there are cases where that is not so, and the relevant constraints cannot currently be expressed
(resp. where abuse of the strong run-export would require all consumers to ignore the run-exports, which
is not feasible at scale, and would be a constant tripping hazard).

For example, C++ and Fortran modules (as of 2025) are not portable between compilers and need to be consumed
by the same compiler that produced them. Assuming we have a package `foo-devel` containing Fortran modules,
to which we would like to attach a `_fortran_modules_abi =*=compiler_flavour*` constraint that ensures that
it can only be combined with the appropriate compiler. The problem in this case is that with a recipe like

```yaml
  - name: i-consume-fortran-modules
    requirements:
      build:
        - {{ stdlib("c") }}
        - {{ compiler("fortran") }}
      host:
        - foo-devel
```

there's no way to make the "wrong" fortran compiler conflict with `foo-devel`, because we explicitly
do not want a strong run-export from the general-purpose `{{ compiler("fortran") }}` to enforce a specific
compiler ABI in `run:` (making the package unusable with other compilers unnecessarily).

The solution in this case would be to add an export to `{{ compiler("fortran") }}` that injects
`_fortran_modules_abi =*=compiler_flavour*` *only* into the `host:` environment; this would impose the
right constraints (i.e. conflict if ABI between the compiler and the constraint attached to `foo-devel`
doesn't match), while avoiding too-tight constraints at runtime. The situation is explained/discussed
in more detail in <https://github.com/conda-forge/conda-forge.github.io/issues/2525>.

## Design

We begin with the following observations based on the above:

- There is a need for a flexible mechanism to do cross-environment dependency injection in the conda ecosystem.
- There are cases where the "run" in `run_exports:` is not appropriate (e.g. `build:` to `host:`), because
  no aspect of the export in question involves something related to the `run:` environment or runtime.
- Just as important as where we're exporting *to* is where we're exporting *from*. Leaving this implicit
  gets exponentially more complicated the more export-flavours there are.
- Already the existing strong run-exports can be subject to this confusion (e.g. "does a strong run-export
  trigger in a host environment?"), [even](https://github.com/conda/ceps/issues/77#issuecomment-3187310320)
  by very experienced contributors.
- It would be nice to cover constraints as well as dependencies with the same pattern.
- There are other use-cases ([example](https://github.com/conda-forge/ctng-compiler-activation-feedstock/blob/e2bdf15eb170008eda386056a900ce93e0f9cb16/recipe/meta.yaml#L147-L150))
  which have so far been under-served by the existing run-export infrastructure.
- Run-exports are not applied when building `noarch` packages, except if the export is of type `noarch:`.
- The v1 recipe format unified all requirement-related topics (including run-exports) under `requirements:`.

Based on this, we propose the following pattern:

```yaml
requirements:
  build:
    - [...]
  host:
    - [...]
  run:
    - [...]
  # relying on the surrounding "requirements" key for context
  exports:
    host_to_run:            # matches `weak:` run-export
      - a_shared_library
    build_to_host:          # "host-export"
      - a_build_constraint =*=*foo
    build_to_run:           # produces same effect as `strong:` run-export when used together with build_to_host
      - a_compiler_runtime
    host_to_constraints:    # matches `weak_constrains:` (v0) / `weak_constraints:` (v1)
      - a_run_constraint
    build_to_constraints:   # matches `strong_constrains:` (v0) / `strong_constraints:` (v1)
      - a_run_constraint
    host_to_host:           # see below
      - a_transitive_dependency
    build_to_build:         # see below
      - a_transitive_dependency
    # all the above _do not_ apply when building `noarch: generic` or `noarch: python` packages
    noarch_to_run:          # matches `noarch:` run-export; _does_ apply when building noarch packages
      - a_dependency_exported_when_consumer_is_noarch
```

As indicated by the comments, `host_to_run:` matches the existing weak run-export. If taken together with
`build_to_run:` this produces the same effect of a strong run-export. Similarly for `host_to_constraints:`
and `build_to_constraints:`. The other keys introduce new functionality, which is explained below.

Before explaining the transitive case, we note though that this design has the advantage that it's
immediately clear from the key pattern `<source>_to_<target>` under which conditions a given export
triggers (i.e. the package carrying the export finds itself in conditions matching `<source>`),
and what it influences (i.e. the export gets added to `<target>`). This avoids a lot of mental arithmetic
(and ideally, implementation complexity) in keeping track of which export triggers when.

The case for `build_to_host:` was already made in the Motivation section, though there are other cases
beyond C++/Fortran modules where the ability to constrain interactions between compilers and host variants
is desirable (e.g. openmp, openmpi, etc.).

The `noarch_to_run:` breaks from the pattern of using a `<source>` that is an existing type of environment.
Given how existing run-exports do not apply to noarch packages at all, and how important use-cases like
python require this functionality, we cannot remove it just for the sake of foolish consistency, and this
seems like the most natural way to incorporate it. The overall rule can still be summarized as "exports do
not apply when building noarch packages, unless the export is of type `noarch_to_run:`."

### Transitive compilation requirements

The most surprising additions might be `host_to_host:` and `build_to_build:`. It would be natural to ask
why whatever is being exported in such a manner could not be a direct (run-)dependency of the package.
The answer is that there may be transitive dependencies *at compilation time* that we do not want
consumers to inherit at runtime (similar to the situation with the Fortran modules ABI).

An example of this is if a library `foo` depends on the headers of another library `bar` at compile-time,
but we do not want packages built atop of `foo` to carry along those `bar` headers or related version
constraints (because at that point they're not needed anymore; the concern is about a compile-time
quantity, which only concerns either `build:` and/or `host:`).

### Other modifications

Additionally, to keep the `<valid_requirements_key>_to_<valid_requirements_key>` pattern (aside from
the special case for `noarch`), we rename

```yaml
requirements:
  constraints:  # changed from run_constraints
    - [...]
```

because constraints only make sense when that package gets installed somewhere in any case, so the
"run_" is superfluous (aside from being inconsistent with the proposed schema). On top of that, the
"run_" is also confusing, because if a package with `run_constraints:` gets installed into a `host:`
or `build:` environment, those constraints will still take effect.

Likewise we rename `ignore_run_exports`

```yaml
  requirements:
    ignore_exports:  # changed from ignore_run_exports
      from_package:
        - zlib
      by_name:
        - libzlib
```

which should ignore any exports into `run:` or `constraints:` matching the conditions (whether
by originating package or by name of the export), regardless of which export type it comes from.

### Omitted combinations

In all cases except `noarch` packages, dependency exports address constraints or interactions arising from
compilation. At runtime, when the build process is long past, the situation simplifies back to the question
whether another package is a dependency or not, which is why no `run_to_run:` key is proposed here.

Furthermore, one could ask about a possible `host_to_build:` key. While this would arguably be an even better
fit for the C++/Fortran modules ABI issue described above, the reason this proposal refrains from suggesting
such a key is to limit implementation complexity, by having an implicit order of environment resolution from
`build:` to `host:` to `run:`. Allowing both `host_to_build:` as well as `build_to_*:` would complicate this
process unnecessarily, and we believe the relevant use-cases are fully expressible using `build_to_host:`
together with constraints (such as `_fortran_modules_abi`) attached to packages that appear in `host:`.

Summing up, `build:` can export to all others (i.e. `build:`, `host:`, `run:`, `constraints:`), `host:` can
export to everything but `build:`, while nothing can be exported from either `run:` or `constraints:`. None
of these exports apply when building noarch packages, which only take into account `noarch_to_run:` exports.

### No convenience shorthand

Owing to the twists and turns of the way the feature was introduced, conda-build has allowed

```yaml
build:
  run_exports:
    - libfoo
```

to be equivalent to

```yaml
build:
  run_exports:
    weak:
     - libfoo
```

which was introduced later (as discussed in History section). The v1 recipe format has kept this shorthand.
Even though it is likely that `host_to_run:` will represent the overwhelming majority of occurrences of exports,
we do not believe it is worth allowing a similar shortcut for `exports.host_to_run:`

```yaml
requirements:
  exports:
    - libfoo  # NOT PROPOSED!
```

For one, it complicates the schema definition and handling unnecessarily, and saving a few characters is not worth
the resulting ambiguity. Finally, using `host_to_run:` improves clarity for the recipe reader and will naturally
(we believe) lead to understanding the other export types (or even run-exports as a concept in the first place).

## Impacts on package and channel metadata

### Background

Both [CEP 12](cep-0012.md) and [CEP 21](cep-0021.md) worked in the area of specifying how run-exports are
represented in package and channel metadata.

To the best of our knowledge, the format of `run_exports.json` on a per-package level has not been formalized,
though, unsurprisingly, it is [simply](https://github.com/conda/conda-build/blob/25.7.0/conda_build/build.py#L1378-L1387)
a JSON-extract of the relevant `run_exports:` portion of the rendered recipe.
CB3 originally introduced this as `run_exports.yaml`, which got [switched](https://github.com/conda/conda-build/commit/1347f3df264c57d79ab078f88fae2d8862a58d9f)
to JSON (by default) in 2018. In practice, it is fair to assume that only `run_exports.json` files exist nowadays.

CEP 12 introduced a channel-level `run_exports.json` which provides the information in aggregated format, allowing
extraction of run-export metadata (e.g. for conda-forge's bot infrastructure) at scale without having to download
every individual package first. This effort refrained from touching `repodata.json`, among other reasons because:
> It would require extending the `repodata` schema, currently not formally standardized.

Indeed, inspection of package-level `repodata_record.json` of contemporary (mid-2025) packages shows that run-exports
do not appear in the regular package-metadata.

CEP 21 (building on top of [CEP 16](cep-0016.md)) added channel-level run-export information, though in contrast
to CEP 12, added this to the physically sharded but logically unified repodata.

### Transition plan

It's easy to map the new export structure to the respective metadata, the complexity lies in providing a smooth
transition for the ecosystem across various versions of tools that build or consume packages and metadata.

The approach suggested here is based on the intention to avoid having to introduce a repodata v2, but if such
an [effort](https://github.com/conda/ceps/pull/111) should come to fruition, the below could certainly be
simplified. We suggest to:

- Output-level:
  - Add another `exports.json` next to `repodata_record.json` and `run_exports.json`, to be preferred by tools
    which know how to handle it.
  - Populate `run_exports.json` with "compatible" metadata derived from `exports:` (see below).
- Channel-level:
  - Add another `exports.json` to the monolithic channel metadata, to be preferred by tools who which how to handle it.
  - Indexers should populate `run_exports.json` with "compatible" metadata derived from `exports:` (see below).
  - Add an `exports:` key within sharded metadata without touching `run_exports:`. The same argument with respect to
    the storage footprint as in CEP 21 applies, i.e. the data is highly compressible and will not have more than
    ~5% impact. Long-term, the existing `run_exports:` information should be removed, freeing up the additional
    space again.

The reason to add separate files is that this provides the easiest compatibility story: tools which are aware of this
CEP can prefer `exports.json` and equivalents, whereas older versions of these tools continue to work unchanged.

### Compatibility mapping back to `run_exports.json`

To smooth the transition, even tools that are aware of this CEP should still populate `run_exports.json` etc., to
avoid breaking behaviour changes in older versions during the transition. For setting the values, we propose a
conservative approach, in the sense that we default to strong exports in case of doubt:

- Reuse values for keys which have a 1:1 equivalent in `run_exports:` schema:
  - `host_to_run:` --> `weak:`
  - `host_to_constraints:` --> `weak_constrains:`
  - `build_to_constraints:` --> `strong_constrains:`
  - `noarch_to_run:` --> `noarch:`
- Add `strong:` run-export in case of doubt, i.e. merge any values of `build_to_host:` & `build_to_run:` into `strong:`.
- Do not map keys that have no equivalent in `run_exports:`, i.e. omit `host_to_host:` & `build_to_build:`.

## Specification

### Open questions

- if we change the keys, do we need to bump the recipe version to v2?
- do we need to update `patch_instructions_version` or other changes to patching infrastructure?

### Recipes, Parsing, Package Building

TODO!

### Package and Channel Metadata

On output-level, if there are any non-empty `exports:` specified, build tools MUST produce an `exports.json`
in the root of the artefact (next to `index.json` etc.), and populate the values with the exports as specified
in the rendered recipe for that output. If the output has no (or empty) `exports:`, populating `exports.json`
MAY be omitted. If the file `exports.json` gets created, its content MUST be a valid JSON object according to
the schema below, where keys that have empty values MAY be omitted.

```json
{
    "build_to_build": [
        "string",
    ],
    "build_to_constraints": [
        "string",
    ],
    "build_to_host": [
        "string",
    ],
    "build_to_run": [
        "string",
    ],
    "host_to_constraints": [
        "string",
    ],
    "host_to_host": [
        "string",
    ],
    "host_to_run": [
        "string",
    ],
    "noarch_to_run": [
        "string",
    ]
}
```

We define the following translation between this schema and the previous `run_exports:` schema:

| `exports:` | `run_exports:` |
|---|---|
| `build_to_build:` | IGNORED |
| `build_to_constraints:` | `strong_constrains:` |
| `build_to_host:` | `strong:` |
| `build_to_run:` | `strong:` |
| `host_to_constraints:` | `weak_constrains:` |
| `host_to_host:` | IGNORED |
| `host_to_run:` | `weak:` |
| `noarch_to_run:` | `noarch:` |

Except for cells marked with "IGNORED", build tools MUST populate the output-level `run_exports.json` file
unchanged from the values of `exports:` in the recipe, though exact duplicates from the merge between
`build_to_host:` and `build_to_run:` into `strong:` MAY be removed. Values from `build_to_build:` and
`host_to_host:` MUST be ignored when populating `run_exports.json`.

On channel-level, the `exports.json` file MUST be populated when indexing the channel, in the same way
as described for `run_exports.json` in CEP 12, but using the following schema. Where artefacts do not yet
have `exports.json` metadata, the values in `exports:` MUST be populated from the respective keys in
`run_exports:` according to the above schema mapping.

```json
{
    "info": {
        "platform": "string",
        "arch": "string",
        "subdir": "string",
        "version": 0
    },
    "packages": {
        "package-version-build.conda": {  # or package-version-build.tar.bz
            "exports": {
                "build_to_build": [
                    "string",
                ],
                "build_to_constraints": [
                    "string",
                ],
                "build_to_host": [
                    "string",
                ],
                "build_to_run": [
                    "string",
                ],
                "host_to_constraints": [
                    "string",
                ],
                "host_to_host": [
                    "string",
                ],
                "host_to_run": [
                    "string",
                ],
                "noarch_to_run": [
                    "string",
                ]
            }
        }
    },
}
```

Indexers MUST (continue to) populate the channel-level `run_exports.json` from the output-level `run_exports.json`.

For sharded repodata following CEP 16 & 21, indexers MUST add an `exports:` key and populate it with the respective
output-level metadata. Where outputs do not yet provide `exports.json` the values of `exports:` MUST be populated
from the respective keys in `run_exports:` according to the above schema mapping. Furthermore, indexers MUST
(continue to) populate the value `run_exports:` derived from output-level `run_exports.json`.

Tools MUST take information from `exports:` / `exports.json` (if available) over `run_exports:` / `run_exports.json`.

### Patching

TODO!
