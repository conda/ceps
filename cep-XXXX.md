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
> Ray Donnelly: Do we not really want to use a different run_export type here? Dropping all but the package name?

> Isuru Fernando: I don't understand. Are you suggesting a different run_exports scheme ('noarch' in addition to
> 'weak', 'strong') that would be applied if the package is a dependency of a `noarch` package?

> Ray Donnelly: I am.

This is a relatively little-used feature, c.f. this approximate [search](https://github.com/search?q=org%3Aconda-forge+%2F%28%3Fs%29%5Csrun_exports%3A.*noarch%3A%2F+path%3Arecipe%2F*.yaml&type=code)
(note: many false positives, but should be exhaustive), though crucially including core packages like
python and R, which are of course key use-cases for building noarch consumers on top.

Perhaps most notably, since the linked PR, regular run-exports (either weak or strong) do not apply to
`noarch: {generic, python}` packages anymore, as thereafter, those received their own special export type.

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
    noarch_to_run:          # matches `noarch:` run-export; does apply to noarch packages
      - a_dependency_exported_when_consumer_is_noarch
```

As indicated by the comments, `host_to_run:` matches the existing weak run-export. If taken together with
`build_to_run:` this produces the same effect of a strong run-export. Similarly for `host_to_constraints:`
and `build_to_constraints:`. The other keys introduce new functionality, which is explained below.

Before explaining the transitive case, we note though that this design has the advantage that it's
immediately clear from the key pattern `<source>_to_<target>` under which conditions a given export
triggers (i.e. the package carrying the export finds itself in an environment matching `<source>`),
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
by originating package or by name of the export), regardless of which environment it comes from.

### Omitted combinations

In all cases, dependency exports address constraints or interactions arising from compilation. At runtime,
when the build process is long past, the situation simplifies back to the question whether another package
is a dependency or not, which is why no `run_to_run:` key is proposed here.

Furthermore, one could ask about a possible `host_to_build:` key. While this would arguably be an even better
fit for the C++/Fortran modules ABI issue described above, the reason this proposal refrains from suggesting
such a key is to limit implementation complexity, by having an implicit order of environment resolution from
`build:` to `host:` to `run:`. Allowing both `host_to_build:` as well as `build_to_*:` would complicate this
process unnecessarily, and we believe the relevant use-cases are fully expressible using `build_to_host:`
together with constraints (such as `_fortran_modules_abi`) attached to packages that appear in `host:`.

Summing up, `build:` can export to all others (i.e. `build:`, `host:`, `run:`, `constraints:`), `host:` can
export to everything but `build:`, while nothing can be exported from either `run:` or `constraints:`. None
of these exports apply when building noarch packages, which have a separate `noarch_to_run:` export type.

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
every individual package first. This effort refrained from touching `repodata.json`, among other reasons because
> It would require extending the `repodata` schema, currently not formally standardized.

Indeed, inspection of package-level `repodata_record.json` of contemporary (mid-2025) packages shows that run-exports
do not appear in the regular package-metadata.

CEP 21 (building on top of [CEP 16](cep-0016.md)) added channel-level run-export information, though in contrast
to CEP 12, added this to the physically shareded but logically unified repodata.

### Transition plan

It's easy to map the new export structure to the respective metadata, the complexity lies in providing a smooth
transition for the ecosystem across various versions of tools that build or consume packages and metadata.

The suggested transition approach looks as follows. The intention is to avoid having to introduce a repodata v2,
but if such an [effort](https://github.com/conda/ceps/pull/111) should come to fruition, the below should certainly
be simplified.

* Package-level:
  * Add another `exports.json` next to `repodata_record.json` and `run_exports.json`, to be preferred by tools
    which know how to handle it.
  * Populate `run_exports.json` with "compatible" metadata
* Channel-level:
  * Add another `exports.json` to the monolithic channel metadata, to be preferred by tools who which how to handle it.
  * Add the structure of run-exports within sharded metadata, as the same argument to footprint applies as in CEP 21,
    i.e. the data is highly compressible and will not have more than ~5% impact. Long-term, the existing `run_exports:`
    information should be removed, freeing up the additional space again.

The reason to add separate files is that this provides the easiest compatibility story: tools which are aware of this
CEP can prefer `exports.json` and equivalents, whereas older versions of these tools continue to work unchanged.

### Compatibility mapping back to `run_exports.json`

To smooth the transition, even tools that are aware of this CEP should still populate `run_exports.json` etc., to
avoid breaking behaviour changes in older versions during the transition. For setting the values, we propose a
conservative approach, in the sense that we default to strong exports in case of doubt:

* replace keys that have a 1:1 equivalent
  * `host_to_run:` --> `weak:`
  * `host_to_constraints:` --> `weak_constrains:`
  * `build_to_constraints:` -- > `strong_constrains:`
  * `noarch_to_run:` --> `noarch:`
* use strong run-export in case of doubt
  * `build_to_host:` --> `strong:`
  * `build_to_run:` --> `strong:`
* do not map unknown keys `host_to_host:` & `build_to_build:`

## Specification

### Recipes, Parsing, Package Building

TODO!

### Package and Channel Metadata

On package-level, if an output has any `exports:` specified, build tools MUST produce an `exports.json` in the
root of the artefact (next to `index.json` etc.), and populate the following schema with the exports as specified
in the rendered recipe. If the output has no (or empty) `exports:`, populating `exports.json` MAY be omitted.
If not, it MUST still conform to the schema below, with empty lists as values for the respective export keys.

```json
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
```

On channel-level the `exports.json` file MUST be populated when indexing the channel, in the same way
as for `run_exports.json`:

```
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

Within the sharded repodata, indexers MUST add an `exports:` key and populate it with the respective
package-level metadata.

### Patching

TODO!

### Open questions

- if we change the keys, do we need to bump the recipe version to v2?
- do we want to specify that implementations need to automatically map `run_exports:` to the corresponding newer keys?
- do we need repodata changes to represent the new, more granular, export metadata?
- how does this interact with sharded repodata (c.f. [CEP 21](cep-0021.md))?
- do we need to specify that installers need to be updated to not choke on unknown keys?
