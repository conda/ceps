# CEP XXXY - Self-exports

<table>
<tr><td> Title </td><td> Self-exports </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Axel Obermeier &lt;h.vetinari@gmx.com&gt;</td></tr>
<tr><td> Created </td><td> Dec 21, 2025 </td></tr>
<tr><td> Discussion </td><td> TBD </td></tr>
<tr><td> Implementation </td><td> TBD </td></tr>
<tr><td> Requires </td><td> https://github.com/conda/ceps/pull/111, https://github.com/conda/ceps/pull/129 </td></tr>
</table>

## Abstract

This CEP builds on https://github.com/conda/ceps/pull/129 and is currently just a draft.

## Motivation

Consider the following use-case: `libB` depends on `libA` as usual, but compiling against `libB` needs
*the specific version* of `libA` used to build `libB`, e.g. due to the way ABI and headers between
`libA` and `libB` interact. This is a scenario that happens with increasing frequency for C++ for example,
where the adoption of templates and `contexpr` functions effectively push dependencies into public headers.

This can be regarded as a "compile-time-only" dependency of `libB`; `libA` is not necessary at runtime, but
_compiling against_ `libB` requires the correct `libA` to be present. For example, if `libB 1.0.0 *_1` is built
against `libA=1` and `libB 1.0.0 *_2` is built against `libA=2`, then a package `mypkg` that (generically) depends
on `libB` needs to match the `libA` version that was used to build the *specific* artefact of `libB` that is in
`host:` at build time of `mypkg`.

Other use-cases that require such machinery involve the compiler stack, where various constraints of the compiler
runtimes or standard libraries should be transitive to consumers of the (non-compiler) package being built.

To illustrate this better, let us look at some example recipes:

```yaml
# output: libA
requirements:
  # omitted: regular build/host/run environments
  exports:
    host_to_run:
      - ${{ pin_compatible("libA") }}
```

This is a standard `host_to_run:` export (previously `run_export:`). Before we consider the recipe of `libB`,
let us consider `mypkg` first, because it illustrates that using `libB` _necessarily_ needs to inject a
constraint on `libA` that's not present in the consuming recipe:

```yaml
# output: mypkg
requirements:
  # omitted: regular build environment
  host:
    - libB
    # injected!
    # - libA  # matches libA-constraint of libB
  run:
    # regular host_to_run export from libB
    # - libB >={{ver_B}},<{{next_ver_B}}
    # host_to_run export from injected libA!
    # - libA >={{ver_A}},<{{next_ver_A}}
    - some_other_regular_dependency
```

Clearly, this is an usual situation deserving of very explicit syntax. Fortunately, the `<from>_to_<to>`
pattern from CEP XXXX provides a very natural way to do this:

```yaml
# output: libB
requirements:
  # omitted: regular build environment
  host:
    - libA
  run:
    # regular host_to_run export from libA
    # - libA >={{ver_A}},<{{next_ver_A}}
  exports:
    host_to_run:
      - ${{ pin_compatible("libB") }}
    # export that injects libA whenever libB is a named dependency in a host environment!
    host_to_host:
      - ${{ pin_compatible("libA") }}
```

The main additional complication this introduces, is that one cannot simply follow the previous process of:

- resolve environment
- collect any exports of concrete packages
- inject those packages into next environment

anymore, because the resolution process becomes entangled with the exports. Doing this iteratively is not an
option because arbitrarily pathological behaviour is possible (e.g. the addition of a `host_to_host:` export
could add constraints that end up evicting the package that caused the export in the first place!).

## Design

The design of CEP XXXX explicitly considered self-exports from the beginning, so the changes are purely additive:

```yaml
requirements:
  exports:
    build_to_build:                 # NEW
      - a_compile_time_only_dependency
    build_to_host:
      - a_host_constraint =*=*foo
    build_to_run:
      - a_compiler_runtime
    build_to_constraints:
      - a_run_constraint
    host_to_host:                   # NEW
      - a_compile_time_only_dependency
    host_to_run:
      - a_shared_library
    host_to_constraints:
      - a_run_constraint
    # all the above _do not_ apply when building `noarch: generic` or `noarch: python` packages
    noarch_to_run:
      - a_dependency_exported_when_consumer_is_noarch
```

Likewise, the expanded form of `ignore_exports` gains a key:

```yaml
requirements:
  ignore_exports:
    to_build:       # NEW
      from_package:
        - zlib
      by_name:
        - libzlib
    to_host:
      [...]         # same inner schema
    to_run:
      [...]
    to_any:
      [...]
```

The changes to `exports.json` follow the existing pattern and just need to add the respective keys.

## Implementation strategy

The key question with self-exports is how to avoid the need for multiple solves to inject the exports
in the environment being resolved. Any number of solves greater than one can trivially lead to pathological
behaviour and must therefore be avoided.

As hinted at by "compile-time-only dependency" in the motivation section, CEP XXX1 (conditional dependencies)
provides the right tool for this. The trick to avoid multiple solves is to implement self-exports as conditional
dependencies, where the condition is a question along the lines of "is the target environment of type `host:`?".

This allows applying (or ignoring) self-exports in the same pass that is necessary anyway to process repodata
with conditional dependencies, before it can be handed over to the SAT solver.

To clarify this further, we need to look at the process for how this would work concretely. Assuming an
already-parsed recipe for some package `mypkg`, let us follow the resolution order mandated by CEP XXXX and
thus begin begin with `build:`, which shall contain some named dependencies `[foo, baz, qux]`. Let's call this
set `B`. Further, let `foo` have `exports: build_to_build: bar`, `bar` have `exports: build_to_build: fizz`,
`fizz` have `exports: build_to_host: bang` and `bang` have `exports: host_to_run: boink`. Finally, let `baz`
have `exports: build_to_run: bla`.

Then, the way to build `mypkg` works as follows. The tags distinguish between metadata fetching (`[meta]`),
handling self-exports (`[self]`), solver interactions (`[solve]`), as well as regular cross-environment
exports (`[cross]`) and saving the package metadata (`[save]`).

- [meta] Fetch metadata
  - Either for entire channel (before CEP 16)
  - Or for sharded repodata (CEP 16), incrementally for all named dependencies, including all builds of their
    transitive dependencies, as well as all of their exports and their transitive dependencies.
  - Do the same for `host:` and `run:` dependencies, including their exports and all transitive dependencies.
- [self] Filter conditional dependencies of all involved packages (or the entire channel) based on current context
  (here: the fact that we're solving for a `build:` environment) before handing to the SAT solver.
  - In the example above, this pre-processing turns `bar` and `fizz` into regular transitive dependencies of `foo`.
  - Compare with `ignore_exports.{to_build,to_any}` and remove any exports that match.
  - Let `B2B` be the set of `build_to_build:` exports that were not ignored; here `B2B=[bar, fizz]`.
  - Translate other conditional dependencies (unrelated to self-exports) into solver constraints, see
    [here](https://github.com/prefix-dev/resolvo/blob/main/src/solver/conditions.rs).
- [solve] Solve constraints to receive a concrete set of artefacts per dependency for the final `build:` environment.
  - Loosely speaking, we're passing `B+B2B` to the solver.
  - Assuming no matching `ignore_exports` being specified in the `mypkg` recipe, this would amount to
    `[foo, baz, qux, bar, fizz]` (including their various constraints) for the above example.
- [cross] Determine `exports:` for the concrete artefacts in resolved `build:` environment.
  - Collect exports, but only for packages in the set `B+B2B` (this is where we extend the "only named packages
    have their exports applied" rule to also include exports of packages injected through exports themselves).
  - Filter the resulting `build_to_host:` exports by `ignore_exports.{to_host,to_any}`, call this set `B2H`.
  - Do the same (including filtering by `ignore_exports:`) for `build_to_run:` exports, call this set `B2R`.
  - Do the same for `build_to_constraints:`, call the resulting set `B2C`.
  - In the above example, `B2H=[bang]`, `B2R=[bla]` and `B2C` is empty.
- [self] Filter conditional dependencies of `host:` packages (as for `build:` above)
  - Calculate `H2H` as the set of `host_to_host:` exports, not including those that match a corresponding
    `ignore_export` rule.
  - In the above example, `H2H` is empty.
- [solve] Solve constraints for named `host:` dependencies + `B2H` + `H2H` to get the final `host:` environment
- [cross] Determine `exports: host_to_run` for the concrete artefacts in resolved `host:` environment
  - Collect exports, but only for packages in the set `H+B2H+H2H`.
  - Filter `host_to_run:` exports by `ignore_exports.{to_run,to_any}`, call the resulting set `H2R`.
  - Do the same for `host_to_constraints:`, call the resulting set `H2C`
  - In the above example, `H2R=[boink]` and `H2C` is empty.
- [save] Save `run:` + `B2R` + `H2R` as dependencies of `mypkg`, save `B2C` + `H2C` as constraints.

## Specification

TODO
