# CEP XXXX - Wheel conda client support

<table>
<tr><td> Title </td><td> Wheel conda client support</td></tr>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td>
  Dan Yeaw &lt;dyeaw@anaconda.com&gt;
</td></tr>
<tr><td> Created </td><td> Apr 24, 2026</td></tr>
<tr><td> Updated </td><td> Apr 24, 2026</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/145 </td></tr>
<tr><td> Implementation </td><td> TBD </td></tr>
<tr><td> Requires </td><td> [CEP XXX1 – Repodata wheel support](cep-XXX1.md) https://github.com/conda/ceps/pull/151 https://github.com/conda/ceps/pull/146 https://github.com/conda/ceps/pull/155 https://github.com/conda/ceps/pull/111 </td></tr>
<tr><td> See also </td><td> [CEP XXX0 – Wheel support in conda (overview)](cep-XXX0.md) </td></tr>
</table>

> The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT",
"RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as
described in [RFC2119][RFC2119] when, and only when, they appear in all capitals, as shown here.

## Abstract

This CEP specifies how conda clients consume wheel entries published in repodata: loading `v{revision}.whl` into the package index used by the solver, applying exclusivity and preference rules, evaluating conditional dependencies and extras per [PR 111][pr-111], downloading wheel artifacts, and integrating them into the environment **as equivalent `noarch: python` conda packages** (layout, package database, and lifecycle), not as a separate pip-style install path.
The shape of the `whl` index and publisher-side `METADATA` conversion are defined in [CEP XXX1 – Repodata wheel support][cep-xxx1]. This CEP applies to pure Python wheels in the sense of that document (e.g. `py3-none-any`); it does not define binary wheel support.
Background on **why** channels and clients pursue native wheel support, plus historical context and rejected ecosystem alternatives, is in [CEP XXX0 – Wheel support in conda (overview)][cep-xxx0].

## Motivation

[CEP XXX1][cep-xxx1] makes wheel metadata available in channel repodata so environments can be solved in one pass together with conda packages.
That is not sufficient by itself: users need a single, well-defined **client** story for (1) which packages the solver may choose, (2) how optional groups and `when=` interact with the live environment, (3) where artifacts are downloaded from, and (4) how wheel contents map onto the prefix (site-packages, scripts, and conda metadata) without corrupting the environment or duplicating work already covered by conda package conventions.

## Specification

### Relationship to [CEP XXX1][cep-xxx1]

This CEP assumes repodata that conforms to [CEP XXX1 – Repodata wheel support][cep-xxx1], including the `whl` mapping under a registered `v{revision}` and valid [repodata record][repodata-record-schema] fields for each entry.

### Repodata consumption

Conda clients that implement wheel support MUST merge entries from the `whl` mapping in each supported [repodata revision](https://github.com/conda/ceps/pull/146) with candidates derived from `packages` and `packages.conda` for the same revision, so that a single index feeds dependency resolution. Clients SHOULD apply the same subdir and channel filtering hooks used for other repodata records unless a separate policy is explicitly documented.

Wheel records for pure Python packages use `subdir: "noarch"` per [CEP XXX1][cep-xxx1]; no additional platform filter is required for those wheels beyond the normal noarch and virtual-package logic for the target prefix.

### Solver: dependency resolution and package preference

Solvers MUST treat pure Python wheel records in `whl` as valid package candidates during dependency resolution with these constraints:

- **Exclusivity:** Solvers MUST NOT install both a conda package and a wheel for the same [package name][cep-26] (as used in `MatchSpec` / the solver index).
- **Dependency satisfaction:** When a wheel is selected, its `depends` list MUST be satisfied the same as for any other package record. Dependencies in `depends` MAY be satisfied by either wheel or conda package records.
- **Platform matching:** For wheel records that conform to the pure-Python rules in [CEP XXX1][cep-xxx1] (`noarch: python` and the stated tag checks), no extra platform tag filtering of the wheel artifact is required, because channels only add that class of wheel to `whl` under those validation rules.

#### User control of precedence

By default, when both a conda package and a wheel are available for the same package name, the solver SHOULD prefer the conda package unless channel priority or an explicit spec selects the wheel. Users MAY override default precedence through:

- Channel priority configuration (for example, preferring channels that publish wheels in `whl`);
- Explicit requests using `<channel name>::<package name>` (or other channel-pinned syntax supported by the client);
- Client configuration (for example, flags or settings such as `prefer_conda` or `prefer_wheel`) where the implementation documents behavior clearly.

The exact default when priorities tie is a client quality-of-implementation choice but MUST remain consistent with **Exclusivity** above (never two artifacts for the same name).

### Conditional dependencies and extras

For wheel records, [PR 111][pr-111] normatively defines `when=` on `depends` and the **`extra_depends`** object for PyPI optional groups. Clients that implement this CEP MUST:

- Evaluate `when=` for wheel `depends` entries according to the same rules as for other new-syntax records, using an environment model that provides at least Python version and, where applicable, virtual packages (see [Marker handling](#marker-handling)).
- Honor **`extra_depends`** when the user selects optional groups (for example with `extras=` in `MatchSpec`) per [PR 111][pr-111], and MUST NOT pull in `extra_depends` groups on a default install.
- Load wheel records that use `when=` or `extra_depends` in the same `v{revision}` payload and revision-handling as other records introduced under the [backwards-compatible repodata update strategy](https://github.com/conda/ceps/pull/146).

The strings on a wheel’s `depends` and `extra_depends` are produced by channel operators from wheel `METADATA` per [CEP XXX1][cep-xxx1]; the client’s job is to interpret them, not to re-parse the wheel for dependency resolution (though reading `METADATA` for validation or error messages is allowed).

### Marker handling

**Publisher output (in repodata):** [CEP XXX1][cep-xxx1] requires converting certain PEP 508 markers on `Requires-Dist` into `when=` and optional-group fields. Other markers are out of scope for the default *publisher* conversion rules; repodata may omit or simplify them.

**Client (solve time):** The solver MUST use the MatchSpec and PR 111 features carried on the repodata record: `when=` subexpressions, `python` constraints, and virtual packages, so that the effective dependency graph matches the published strings for the current environment. Clients MAY map additional environment dimensions to virtual packages where documented (non-normative per-variable notes appear in the [conda-pypi marker conversion][conda-pypi-marker-conversion] documentation).

**Out-of-scope dimensions:** Some PEP 508 variables (for example, `implementation_name`, or markers tied to a specific wheel build matrix beyond the pure-Python subset) do not have a defined mapping in the normative [CEP XXX1][cep-xxx1] record; behavior for such wheels remains undefined unless a future CEP or channel policy encodes them in repodata. Clients MUST NOT claim full PEP 508 equivalence beyond what the record expresses.

### Download

After the solver selects a wheel record, the client MUST download the `.whl` file using the same rules as for other `noarch` artifacts with a `fn` and optional `url`:

- Resolve the URL per [PR 151][pr-151] and the download examples in [CEP XXX1][cep-xxx1] (channel `base_url`, default `noarch` layout, or absolute per-record `url`).
- Verify integrity using `sha256` and `size` from the repodata record when those fields are present, consistent with other conda downloads.

### Installation layout and prefix placement

Wheels selected from repodata MUST be integrated into the target environment **as the equivalent of a `noarch: python` conda package** ([CEP 20][cep-20], [CEP 34][cep-34]): the same style of layout under the prefix, registration in conda's package database, and `conda list` / `conda remove` / upgrade behavior that matches other packages from the index—not a standalone "pip install this wheel" interaction.

Importable code MUST end up under the environment's [site-packages][cep-20] (or the site-packages / path layout for `noarch: python` described in that package’s `info/index.json` and related files per [CEP 34][cep-34]). Headers, data, and other install-tree paths from the wheel MUST be placed under prefix locations that are tracked and removed the same way as in a built conda package.
The repodata record points at a wheel file as the artifact to obtain; the **normative** requirement is conda-equivalent integration as in the preceding paragraph, not a wheel-only layout profile considered in isolation from conda's package model.

- **Metadata:** The install MUST create a valid `.dist-info` (or legacy `.egg-info` if present in the wheel) so `importlib.metadata` can load the distribution, consistent with other Python packages in the environment.
- **RECORD:** The client SHOULD verify the wheel's `RECORD` where present to detect tampering or corruption; it MUST reject path entries that escape the intended prefix or package staging area.
- **Console and GUI entry points:** Application entry points SHOULD be materialized like other conda `noarch: python` packages: through `info/link.json` and conda's link machinery per [CEP 20][cep-20] and [CEP 34][cep-34], so shebangs and `bin` scripts remain under conda's control. A client implementation MAY avoid emitting duplicate script files from the wheel when `link.json` (or an equivalent) defines the public commands.

## Rationale

### One solve, predictable layout

Native wheel support in the client avoids separate PyPI or pip phases for the packages indexed in [CEP XXX1][cep-xxx1], matches user expectations for where importable code lives, and reuses conda's environment model. Keeping download rules aligned with [PR 151][pr-151] matches existing channel URL behavior.

### Native unpack vs always converting to conda packages

On-the-fly conversion to a `.conda` artifact can still be a useful optimization or fallback (for example, sharing on a local channel). Either way, the user-visible result remains a normal conda-managed install.
This CEP requires that materializing the environment from a **wheel file** (without requiring a pre-built conda package on the channel) be possible so channels do not need a second hosting pipeline for the same file PyPI already ships as a wheel, and to avoid inflating storage with redundant formats for pure-Python content.

## Implementation Notes

### For conda client implementers

- **Index:** Parse `whl` inside each supported `v{revision}` object alongside `packages` / `packages.conda` and feed merged candidates to the solver.
- **PR 111:** Implement evaluation of `when=` and merging of `extra_depends` when the user requests extras, consistent with the published record strings.
- **Revision gating:** Treat new-syntax wheel records with the same `v{revision}` handling as the rest of the PR 146 strategy (do not expect older repodata only clients to read `whl`).
- **Download:** Reuse the channel and fetch stack used for other artifacts, including `url` and checksum verification.
- **Install:** Integrate wheels using the same prefix layout and metadata model as `noarch: python` conda packages ([CEP 20][cep-20], [CEP 34][cep-34]), including `info/link.json` for entry points when using conda's link pipeline. The [conda-pypi][conda-pypi] project demonstrates populating a conda package shape from a wheel (for example, suppressing duplicate `bin` script generation when `link.json` is used) as **non-normative** prior art.
- **Testing:** Add integration tests for exclusivity, preference, conditional edges, a wheel-only dependency, and a conda–wheel mixed graph.

## Examples

### Solver constraints (illustrative)

For a request that could be satisfied by either a conda `requests` or a wheel in `whl` with the same name, a configuration that prefers conda SHOULD select the conda build unless the user pins the wheel channel or package record.

### Install outcome (illustrative)

After installing `requests-2.32.5-py3-none-any.whl` from a wheel repodata record, the environment’s site-packages should contain the `requests` import package and a `requests-2.32.5.dist-info` (or equivalent) directory such that `import requests` and `importlib.metadata.version("requests")` succeed for that prefix’s Python.

## Backwards compatibility

- **Repodata shape:** The `whl` key appears only under a registered `v{revision}` (see [PR 146](https://github.com/conda/ceps/pull/146)). Conda clients that do not support that revision or the `whl` index MUST ignore unknown `v{revision}` members or fall back to earlier revisions per channel policy, and MUST NOT break on the presence of `whl` in repodata for revisions they do not load.
- **Record syntax:** Records that use `when=` and `extra_depends` are part of the new-syntax repodata world [PR 111][pr-111] already depends on; wheel rows are not a separate syntax fork.

## Rejected ideas

Ecosystem-level alternatives (relying on pip only, on-the-fly PyPI without repodata, build farms that convert every wheel) are discussed under **Rejected ideas** in [CEP XXX0 – Wheel support in conda (overview)][cep-xxx0]. This CEP is the client-side complement to the chosen approach: indexed wheels plus native client install.

## References

- [CEP XXX0 – Wheel support in conda (overview)][cep-xxx0]
- [CEP XXX1 – Repodata wheel support][cep-xxx1]
- [CEP 20 – `noarch` (python) packages and site-packages][cep-20]
- [CEP 34 – Package metadata and `info/`](./cep-0034.md) (`index.json`, `link.json`, etc.)
- [CEP 26 – Identifying packages and channels][cep-26]
- [PR 111 – Conditional dependencies and optional groups][pr-111]
- [PR 151 – URL field for package records][pr-151]
- [PEP 508 marker conversion (conda-pypi developer docs)][conda-pypi-marker-conversion]
- [Example `repodata.json` (conda-pypi test channel)][conda-pypi-example-repodata]
- [conda-pypi project][conda-pypi]
- [Adopting uv in pixi][uv-in-pixi]
- [rip][rip]
- [conda-pupa][conda-pupa]

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

<!-- links -->
[RFC2119]: https://datatracker.ietf.org/doc/html/rfc2119
[repodata-record-schema]: https://schemas.conda.org/repodata-record-1.schema.json
[cep-26]: https://conda.org/learn/ceps/cep-0026
[cep-20]: ./cep-0020.md
[cep-34]: ./cep-0034.md
[cep-xxx0]: cep-XXX0.md
[cep-xxx1]: cep-XXX1.md
[conda-pypi]: https://github.com/conda-incubator/conda-pypi
[conda-pypi-marker-conversion]: https://conda.github.io/conda-pypi/developer/marker-conversion/#pep-508-variables
[conda-pypi-example-repodata]: https://github.com/conda-incubator/conda-pypi/blob/main/tests/conda_local_channel/noarch/repodata.json
[pr-151]: https://github.com/conda/ceps/pull/151
[pr-111]: https://github.com/conda/ceps/pull/111
[conda-pupa]: https://github.com/dholth/conda-pupa
[uv-in-pixi]: https://prefix.dev/blog/uv_in_pixi
[rip]: https://github.com/prefix-dev/rip
