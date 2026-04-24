# CEP XXXX - Repodata Wheel Support

<table>
<tr><td> Title </td><td> Repodata Wheel Support</td></tr>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td>
  Dan Yeaw &lt;dyeaw@anaconda.com&gt; <br/>
  Travis Hathaway &lt;travis.j.hathaway@gmail.com&gt;
</td></tr>
<tr><td> Created </td><td> Dec 23, 2025</td></tr>
<tr><td> Updated </td><td> Apr 24, 2026</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/145 </td></tr>
<tr><td> Implementation </td><td> TBD </td></tr>
<tr><td> Requires </td><td> https://github.com/conda/ceps/pull/151 https://github.com/conda/ceps/pull/146 https://github.com/conda/ceps/pull/155 https://github.com/conda/ceps/pull/111 [CEP XXX2 (Wheel conda client support)](cep-XXX2.md) </td></tr>
<tr><td> See also </td><td> [CEP XXX0 – Wheel support in conda (overview)](cep-XXX0.md) </td></tr>
</table>

> The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT",
"RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as
described in [RFC2119][RFC2119] when, and only when, they appear in all capitals, as shown here.

## Abstract

This CEP specifies how channel operators publish pure Python wheel packages in conda's package index (repodata): the `whl` member under `v{revision}`, record fields, publisher-side dependency conversion from wheel `METADATA`, and validation rules.
It does not define conda client solver, download, or install-time behavior; those are specified in [CEP XXX2 – Wheel conda client support][cep-xxx2].
Motivation, ecosystem history, and rejected alternatives are in [CEP XXX0 – Wheel support in conda (overview)][cep-xxx0].
We limit the scope to pure Python wheels to avoid platform-specific binary compatibility issues. Even so, publishing wheels in repodata greatly increases the packages channels can expose without building conda recipes for every case.

## Relationship to companion CEPs

- **[CEP XXX0 – Wheel support in conda (overview)][cep-xxx0]** — Why native wheel support, historical context, and discussion of rejected ideas (informative).
- **[CEP XXX2 – Wheel conda client support][cep-xxx2]** — Normative client behavior: loading `whl` into the solve with other repodata records, download, and installation.

## Specification

### Expose wheels via `whl` inside a repodata revision (`v{revision}`)

According to the current schema for [repodata.json][repodata-schema], the repodata object is traditionally organized around these top-level keys (the surface unchanged clients rely on):

- repodata_version
- info
- packages
- packages.conda
- removed

Wheel support MUST follow [A backwards-compatible repodata update strategy](https://github.com/conda/ceps/pull/146): publishers SHALL register the revision in `info.repodata_revisions` and SHALL place the wheel index under the matching top-level `v{revision}` dictionary (where `revision` is the integer listed for that entry). This CEP specifies a `whl` member inside that `v{revision}` object. The value MUST be a mapping whose entries are [repodata record][repodata-record-schema] objects.

### `whl` dictionary structure

The `whl` dictionary maps conda-like filenames to repodata records. The key MUST follow the format specified in [Key naming requirements](#key-naming-requirements). The value MUST be a repodata record object that conforms to the [repodata record schema][repodata-record-schema] with the following field specifications:

- **`name`**: Taken from the wheel's METADATA `Name` field, normalized per [CEP 26][cep-26] and any name mappings aligned with the channel declared in `info.channel_relations.base` when present (see [Naming standard and channel mapping](#naming-standard-and-channel-mapping)).
- **`version`**: Taken from the wheel's METADATA `Version` field, normalized per PEP 440.
- **`build`**: Format `py{PY_MAJOR_VERSION}_{abi_tag}_{platform_tag}_{build_number}` (e.g., `py3_none_any_0`), conforming to CEP 26 build string conventions and the repodata record schema pattern `^([a-z0-9_.]+_)?[0-9]+$`. The build number MUST be at the end of the build string. The `{abi_tag}` and `{platform_tag}` are extracted from the wheel filename.
- **`build_number`**: As in regular conda packages. MUST be 0 initially. MAY be incremented for rebuilds.
- **`depends`**: Array including:
  - `python` dependency from `Requires-Python` (if present), converted to conda format
  - All `Requires-Dist` entries from METADATA, converted from PEP 440 to conda format per [Dependency conversion](#dependency-conversion)
  - Package names normalized to conda-style names per [CEP 26][cep-26]
- **`extra_depends`**: MAY be present. When present, MUST be an object mapping extra names to lists of dependency strings for optional groups, per [PR 111][pr-111]. When absent or empty, the record declares no optional groups beyond `depends`.
- **`subdir`**: MUST be `"noarch"`.
- **`noarch`**: MUST be `"python"`.
- **`url`**: MAY be present. Semantics are defined in [PR 151][pr-151] (see [Wheel download URLs](#wheel-download-urls)).
- **`fn`**: MUST be the wheel filename (`.whl`), as in standard conda repodata records (for example `requests-2.32.5-py3-none-any.whl`).
- **`sha256`**, **`size`**: Standard repodata fields for the wheel file.

### Key naming requirements

The key for each entry in `whl` MUST follow the standard conda distribution string format per [CEP 26][cep-26]: `{name}-{version}-{build string}`, where:

- `{name}` is derived from the wheel's METADATA file (the `Name` field), normalized according to conda naming conventions per [CEP 26][cep-26] and any name mappings inherited from the base channel when `info.channel_relations.base` is declared (see [Naming standard and channel mapping](#naming-standard-and-channel-mapping))
- `{version}` is the package version from METADATA
- `{build}` is the build string (e.g., `py3_none_any_0`, `py3_none_any_1`) from the `build` field, which includes the Python version, ABI tag, platform tag, and build number (with build number at the end)

Examples:

- `httpx-0.28.1-py3_none_any_0`
- `typing_extensions-4.15.0-py3_none_any_0` (METADATA name `typing-extensions` mapped to conda name `typing_extensions`)
- `requests-2.32.5-py3_none_any_1` (rebuild with build_number 1)

### Naming standard and channel mapping

The key name for wheel records SHALL follow the standard conda distribution string format `{name}-{version}-{build}` per [CEP 26][cep-26]. The build string includes the Python version, ABI tag, platform tag, and build number (e.g., `py3_none_any_0`), where the build number is at the end per the repodata record schema pattern.
The ABI and platform tags are extracted from the wheel filename. The python_tag from the wheel filename is omitted as it is redundant with the Python version in the build string. This ensures compatibility with standard conda parsing while preserving wheel tag information within the build string.

When there are naming differences between PyPI wheels and conda packages, channel operators MUST determine the appropriate conda-style name by applying conda naming conventions per [CEP 26 - Identifying Packages and Channels in the conda Ecosystem][cep-26].

To help users understand which naming conventions are being used, a wheel channel MAY declare a **base** channel using `info.channel_relations.base` as specified in [Channel relations in repodata][cep-channel-relations].
The base channel is the one clients load with higher priority. It is also the natural source of conda-style naming conventions and PyPI-to-conda name mappings for wheels published alongside that stack (for example, `conda-forge` as the base for a specialized wheel index on the same channel host).
Channel references MUST use relative paths as required by that CEP (for example `"base": "../conda-forge"`). Absolute URLs in `info` are not valid channel references for relations.

Channel operators SHOULD document any naming conventions and mappings specific to their channel, including how they relate to their declared `channel_relations`.

### Wheel download URLs

This CEP depends on the optional per-record **`url`** field as specified in [PR 151][pr-151], which enables custom download locations. This is essential for wheel support since PyPI wheels are commonly hosted in per-package subdirectories or served from CDNs.

The `whl` mapping (inside the `v{revision}` payload) and the per-record `url` field SHALL follow
the backwards-compatible update strategy ([PR 146](https://github.com/conda/ceps/pull/146)).

### Wheel-Specific Record Values

When populating repodata records for pure Python wheels:

- `build`: MUST be py`PY_MAJOR_VERSION`_`abi_tag`_`platform_tag`_`build_number` (e.g. `py3_none_any_0`), where `{abi_tag}` and `{platform_tag}` are extracted from the wheel filename, and the build number MUST be at the end of the build string per the repodata record schema pattern
- `build_number`: MUST be 0 for the initial addition of a wheel version. MAY be incremented for subsequent rebuilds of the same wheel version (e.g., to correct dependencies or metadata)
- `subdir`: MUST be "noarch"
- `noarch`: MUST be "python"
- `fn`: MUST be the wheel filename (`.whl`)
- `url`: MAY be present and follow the semantics in [PR 151][pr-151] and [Wheel download URLs](#wheel-download-urls)

### Pure Python wheel validation

Before adding a wheel to `whl`, channel operators MUST verify:

- The wheel's platform tag is `any` (i.e., wheel filenames ending in `-none-any.whl`, such as `requests-2.32.5-py3-none-any.whl`)
- The wheel's ABI tag is `none`
- The wheel contains no compiled extensions (`.so`, `.pyd`, `.dylib` files)
- The wheel's `METADATA` file is present and valid

Wheels that fail any of these checks MUST NOT be added to `whl`.

### Dependency conversion

Channel operators MUST convert Python dependency declarations—`Requires-Dist`, `Requires-Python`, and extras—into conda `depends`, **`extra_depends`** when applicable, and related fields, following the rules below.

Those declarations MAY be read from the wheel's embedded **`METADATA`** and/or from the [**PyPI JSON API**][pypi-json-api] release payload for the same **project** and **version** as the wheel being indexed. Using the API can simplify batch indexing and mirrors. Regardless of source, the same conversion rules and interoperable minimum in [PEP 508 marker translation guidance](#pep-508-marker-translation-guidance) apply.

- **Package names:** Names per [CEP 26][cep-26] and match existing conda-forge package names where they exist
- **Version specifiers:** Map PEP 440 [version specifiers][version-specifiers] to conda format:
  - The `==` operator is converted to an exact pin (removing the `==`)
  - All other PEP 440 operators (`>=`, `<=`, `<`, `>`, `~=`, `!=`) are used as-is
  - Multiple version specifiers are combined with commas (e.g., `>=1.0,<2.0`)

- **Python version requirements:** Convert Requires-Python to explicit python dependency
- **Environment markers:** Map Python-version markers on `Requires-Dist` to conditional `MatchSpec` `when=` as specified in [PR 111][pr-111]. Other markers are out of scope for the default conversion rules in this CEP (see [Limitations](#limitations)).

Example conversion:

```text
# Wheel METADATA
Requires-Python: >=3.8
Requires-Dist: requests (>=2.20.0,<3.0.0)
Requires-Dist: click (>=7.0)
Requires-Dist: numpy (>=1.20.0,!=1.24.0)
Requires-Dist: importlib-metadata (>=1.0) ; python_version < '3.10'
```

Resulting conda record:

```json
{
  "depends": [
    "python >=3.8",
    "requests >=2.20.0,<3.0",
    "click >=7.0",
    "numpy >=1.20.0,!=1.24.0",
    "importlib-metadata>=1.0[when=\"python<3.10\"]"
  ]
}
```

### PEP 508 marker translation guidance

This subsection layers interoperable expectations for the repodata format, non-normative reference material for richer mappings, and a general translation policy.

#### Interoperable minimum

For published `whl` records, the following conversions are the **normative floor** aligned with [Dependency conversion](#dependency-conversion) and [PR 111][pr-111]:

- **`Requires-Python`:** MUST appear as an explicit `python` dependency in `depends`.
- **Python-version conditions on `Requires-Dist`:** MUST be represented with conditional `MatchSpec` `when=` on the relevant dependency strings per [PR 111][pr-111].
- **`extra` (optional groups):** MUST be represented with **`extra_depends`** and optional-group selection per [PR 111][pr-111], not only as opaque marker text on `depends`.

Channels and tools MAY apply additional, stricter mappings where they can express them in repodata.

#### Non-normative extended mappings

Per-variable translation of other PEP 508 markers (for example `sys_platform`, `platform_system`) to `when=` fragments, virtual packages, or omissions is **not** fully specified in this CEP. For a non-normative, per-variable description—including how **conda-pypi** maps markers to `when=` and **`extra_depends`**—see [PEP 508 marker conversion][conda-pypi-marker-conversion] in the conda-pypi documentation.

#### Lossy translation

When a channel cannot encode a PEP 508 dimension in repodata (for example no virtual package for an architecture string, or unsupported boolean branches), the operator MAY **omit** the condition, **simplify** the requirement, or **widen** the dependency (for example listing a package in `depends` without `when=` so it applies in more environments than PEP 508 would).
Channel operators SHOULD document their policy for such cases (including any conservative “include unconditionally” behavior).

### Handling conditional dependencies and extras

Wheel `depends` entries that encode PEP 508 environment markers MUST use conditional `MatchSpec` syntax with `when=` as specified in [PR 111][pr-111].

PyPI **extras** (optional dependency groups) MUST be represented on the wheel repodata record using an **`extra_depends`** object (a mapping from extra name to lists of dependency strings) as specified in [PR 111][pr-111]. A default install uses only `depends` and MUST NOT union in `extra_depends` entries unless the user selects optional groups (for example with `extras=` in `MatchSpec` as described in [PR 111][pr-111]).

### Solver behavior

Normative rules for how conda clients treat `whl` records during dependency resolution (same candidate pool as other repodata records; no CEP-mandated default between conda builds and wheels) are defined in [CEP XXX2 – Wheel conda client support][cep-xxx2].
This CEP only requires that published `whl` records are valid [repodata records][repodata-record-schema] so that clients can consume them alongside `packages` and `packages.conda`.

### Limitations

This CEP has the following known limitations:

1. **Pure Python only:** This CEP explicitly does not address wheels with binary extensions, which require platform-specific compatibility guarantees beyond the current scope. Conda’s strength is binary compatibility, so using conda packages may be the optimal solution.
2. **Environment markers (publisher defaults):** Default conversion rules in this CEP focus on Python-version markers on `Requires-Dist`, mapped to `when=` per [PR 111][pr-111]. Other markers (for example `sys_platform`) are out of scope for those default publisher rules and are not required to be converted into repodata here; see [PEP 508 marker translation guidance](#pep-508-marker-translation-guidance).
How conda clients evaluate `when=` and optional groups at solve time (including environment context) is specified in [CEP XXX2][cep-xxx2] together with [PR 111][pr-111].
3. **Conditionals and extras:** Normative syntax and record fields for `when=` on `depends` and for optional groups in **`extra_depends`** are specified in [PR 111][pr-111], on which this repodata CEP and [CEP XXX2][cep-xxx2] rely for PyPI-aligned conditionals and extras in published records and at client solve time, respectively.
4. **Repodata size:** Supporting a significant portion of pure Python packages from PyPI (potentially hundreds of thousands of packages with multiple versions each) will substantially increase repodata size. Channels adopting wheel support at scale SHOULD implement sharded repodata ([CEP 16][cep-16]) to maintain acceptable performance.
5. **PyPI package deletion:** PyPI allows package maintainers to delete releases (as opposed to only yanking them). Releases may also be removed when classified as **malicious** or otherwise pulled by PyPI administrators. Any removal may break locked environments that reference those artifacts.
Channels using external PyPI URLs directly are subject to this risk. For production use and reproducible environments, channels MAY mirror and store wheel artifacts locally rather than relying solely on external PyPI URLs.

## Rationale

### Why wheel names may differ from conda names

Several factors can cause wheel names to differ from conda-style names:

1. **Wheel filename normalization:** Wheel filenames normalize hyphens to underscores per PEP 427, but the METADATA `Name` field contains the canonical name (which may have hyphens).
    - Example: `lazy-loader` (METADATA name) vs `lazy_loader` (wheel filename)

2. **Python-specific clarification:** PyPI packages are implicitly Python libraries
    - Example: `authzed-py` (conda-forge) vs `authzed` (PyPI)

3. **Variant differences:** Conda may offer multiple variants with different dependencies
    - Example: `seaborn-base` (conda-forge) vs `seaborn` (PyPI)

4. **Cross-channel naming:** Different conda channels may use different names
    - Example: `pyperformance` (conda-forge) vs `performance` (main)

## Implementation Notes

### For conda clients

Client behavior (loading `whl` into the solve with other repodata records, download, and installation into the environment prefix) is specified in [CEP XXX2 – Wheel conda client support][cep-xxx2]. Channel operators need not implement that CEP; they only publish repodata that conforms to this document.

### For channel operators

Channel operators adding wheel support SHOULD:

- Implement validation to ensure only pure Python wheels are included
- When using the [PyPI JSON API][pypi-json-api] for dependency metadata, consider comparing against the wheel's `METADATA` and fall back (or merge) when the API response is incomplete relative to the artifact
- Ensure that dependencies are solvable, including that compiled dependencies exist on the conda channel declared as `info.channel_relations.base` when wheels depend on conda packages from that stack
- Maintain a mapping of PyPI to conda-style names for their channel, or declare `channel_relations.base` so clients load a base channel that defines those mappings (see [Naming standard and channel mapping](#naming-standard-and-channel-mapping) and [Channel relations in repodata][cep-channel-relations])
- Consider automation to keep the repodata up to date with newer releases on PyPI
- Document any naming conventions specific to their channel
- For production channels, consider mirroring wheel artifacts locally to ensure reproducibility and protect against PyPI deletions
- Establish patching workflows to correct metadata issues and resolve dependency conflicts
- Document patching policies and maintain transparency about modified packages

### Implementation approaches

Channels MAY implement wheel support through various approaches:

- **Manual curation**: Channels can manually add specific pure-Python wheels via repodata patching, providing full control over which packages are included and allowing for quality control and metadata validation before exposure to users.
- **Semi-automated**: Channels can implement automated processes to discover and add wheels, with manual review and patching workflows for quality assurance.
- **Full automation**: Channels can automatically mirror and index wheels from PyPI, though this requires robust validation, patching infrastructure, and consideration of repodata size impacts.

A phased approach starting with manual curation and moving toward increased automation as processes mature is RECOMMENDED. This balances the lower barrier to entry (no recipes needed for many packages) with quality control. Complex packages with metadata conflicts or special requirements should still use traditional conda feedstocks.

## Examples

The JSON fragments below use revision `3` as an example (`v3`). The integer MUST match an entry in
`info.repodata_revisions` per [the backwards-compatible repodata update strategy](https://github.com/conda/ceps/pull/146).
A complete channel index also includes the traditional top-level keys (`repodata_version`, `packages`,
`packages.conda`, `removed`, and so on). A full generated example is checked in with [conda-pypi][conda-pypi-example-repodata].

### Download wheels from the default location

Below represents the default behavior when the `url` field is omitted:

```json
{
  "v3": {
    "whl": {
      "requests-2.32.5-py3_none_any_0": {
        "name": "requests",
        "version": "2.32.5",
        "build": "py3_none_any_0",
        "build_number": 0,
        "depends": [
          "charset-normalizer <4,>=2",
          "idna <4,>=2.5",
          "urllib3 <3,>=1.21.1",
          "certifi >=2017.4.17",
          "python >=3.9"
        ],
        "fn": "requests-2.32.5-py3-none-any.whl",
        "sha256": "78820a3e5d9d3b25ce8e1c99c1c89cd19caa904a92973a3e50f8426009e8a4b3",
        "size": 6899,
        "subdir": "noarch",
        "noarch": "python",
        "url": null
      }
    }
  }
}
```

With this configuration, the wheel file will be downloaded from the following location (assuming we are hosting this from `https://repo.example.com/channel`):

- `https://repo.example.com/channel/noarch/requests-2.32.5-py3-none-any.whl`

### Downloading wheels from a relative location with `base_url`

The `url` can also be relative as described above. Here's an example of what that looks like combined with setting the `base_url` property at the top level, and also showing how a channel can declare a base channel for naming and dependencies using `channel_relations` ([Channel relations in repodata][cep-channel-relations]):

```json
{
  "info": {
    "subdir": "noarch",
    "base_url": "https://packages.example.org/wheel-extra/",
    "channel_relations": {
      "base": "../core"
    }
  },
  "v3": {
    "whl": {
      "requests-2.32.5-py3_none_any_0": {
        "name": "requests",
        "version": "2.32.5",
        "build": "py3_none_any_0",
        "build_number": 0,
        "depends": [
          "charset-normalizer <4,>=2",
          "idna <4,>=2.5",
          "urllib3 <3,>=1.21.1",
          "certifi >=2017.4.17",
          "python >=3.9"
        ],
        "fn": "requests-2.32.5-py3-none-any.whl",
        "sha256": "78820a3e5d9d3b25ce8e1c99c1c89cd19caa904a92973a3e50f8426009e8a4b3",
        "size": 6899,
        "subdir": "noarch",
        "noarch": "python",
        "url": "requests/requests-2.32.5-py3-none-any.whl"
      }
    }
  }
}
```

This would result in the following being fetched by conda clients:

- `https://packages.example.org/wheel-extra/noarch/requests/requests-2.32.5-py3-none-any.whl`

### Downloading wheels from external location

The following shows an example of using an external location to download the wheel from PyPI's file hosting:

```json
{
  "v3": {
    "whl": {
      "requests-2.32.5-py3_none_any_0": {
        "name": "requests",
        "version": "2.32.5",
        "build": "py3_none_any_0",
        "build_number": 0,
        "depends": [
          "charset-normalizer <4,>=2",
          "idna <4,>=2.5",
          "urllib3 <3,>=1.21.1",
          "certifi >=2017.4.17",
          "python >=3.9"
        ],
        "fn": "requests-2.32.5-py3-none-any.whl",
        "sha256": "78820a3e5d9d3b25ce8e1c99c1c89cd19caa904a92973a3e50f8426009e8a4b3",
        "size": 6899,
        "subdir": "noarch",
        "noarch": "python",
        "url": "https://files.pythonhosted.org/packages/1e/db/4254e3eabe8020b458f1a747140d32277ec7a271daf1d235b70dc0b4e6e3/requests-2.32.5-py3-none-any.whl"
      }
    }
  }
}
```

### Name mapping

Here is an example of name mapping and normalization of the record name and dependencies.

```json
{
  "v3": {
    "whl": {
      "annotated_types-0.7.0-py3_none_any_0": {
        "name": "annotated-types",
        "version": "0.7.0",
        "build": "py3_none_any_0",
        "build_number": 0,
        "depends": [
          "typing_extensions>=4.0.0[when=\"python<3.9\"]",
          "python >=3.8"
        ],
        "fn": "annotated_types-0.7.0-py3-none-any.whl",
        "sha256": "1f02e8b43a8fbbc3f3e0d4f0f4bfc8131bcb4eebe8849b8e5c773f3a1c582a53",
        "size": 13643,
        "subdir": "noarch",
        "noarch": "python",
        "url": "https://files.pythonhosted.org/packages/78/b6/6307fbef88d9b5ee7421e68d78a9f162e0da4900bc5f5793f6d3d0e34fb8/annotated_types-0.7.0-py3-none-any.whl"
      }
    }
  }
}
```

This example demonstrates two types of name normalization:

1. Record key format: The package is indexed using the standard conda distribution string format `{conda_name}-{version}-{build}` per [CEP 26][cep-26]: `annotated_types-0.7.0-py3_none_any_0`. The name portion (`annotated_types`) comes from the METADATA `Name` field (`annotated-types`), normalized to conda conventions (mapped to `annotated_types` to match conda-forge naming).
The build string (`py3_none_any_0`) includes the Python version, ABI tag (`none`), platform tag (`any`), and build number (`0` at the end), all extracted from the wheel filename (`annotated_types-0.7.0-py3-none-any.whl`), which normalizes the package name to underscores per PEP 427.
2. Dependency name mapping: This package depends on `typing_extensions`, which is listed in the `depends` field. On PyPI, this package is named `typing-extensions` (with a hyphen), but it has been mapped to the name `typing_extensions` (with an underscore) to match the existing conda-forge package name. Such mappings may be aligned with the channel declared in `info.channel_relations.base` (see [Naming standard and channel mapping](#naming-standard-and-channel-mapping)).

This example also demonstrates conditional dependencies. The original `METADATA` file from the wheel has the following dependency information:

```text
Requires-Python: >=3.8
Requires-Dist: typing-extensions>=4.0.0; python_version < '3.9'
```

The package record expresses the conditional with `when=` so `typing_extensions` applies only when the Python version is less than 3.9, matching the original wheel METADATA and [PR 111][pr-111]. The Python version constraint of >=3.8 is directly mapped.

## References

- [CEP XXX0 – Wheel support in conda (overview)][cep-xxx0]
- [CEP XXX2 – Wheel conda client support][cep-xxx2]
- [conda-pypi project][conda-pypi]
- [PEP 508 marker conversion (conda-pypi developer docs)][conda-pypi-marker-conversion]
- [Example `repodata.json` (conda-pypi test channel)][conda-pypi-example-repodata]
- [Channel relations in repodata (PR 155)][cep-channel-relations]
- [PR 151 – URL field for package records][pr-151]
- [PR 111 – Conditional dependencies and optional groups][pr-111]
- [conda-pupa][conda-pupa]
- [PyPI JSON API documentation][pypi-json-api]

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

<!-- links -->
[RFC2119]: https://datatracker.ietf.org/doc/html/rfc2119
[repodata-schema]: https://schemas.conda.org/repodata-1.schema.json
[repodata-record-schema]: https://schemas.conda.org/repodata-record-1.schema.json
[cep-16]: https://conda.org/learn/ceps/cep-0016
[cep-26]: https://conda.org/learn/ceps/cep-0026
[version-specifiers]: https://packaging.python.org/en/latest/specifications/version-specifiers/#id5
[conda-pypi]: https://github.com/conda-incubator/conda-pypi
[conda-pypi-marker-conversion]: https://conda.github.io/conda-pypi/developer/marker-conversion/#pep-508-variables
[conda-pypi-example-repodata]: https://github.com/conda-incubator/conda-pypi/blob/main/tests/conda_local_channel/noarch/repodata.json
[cep-channel-relations]: https://github.com/conda/ceps/pull/155
[pr-151]: https://github.com/conda/ceps/pull/151
[pr-111]: https://github.com/conda/ceps/pull/111
[conda-pupa]: https://github.com/dholth/conda-pupa
[pypi-json-api]: https://docs.pypi.org/api/json/
[cep-xxx0]: cep-XXX0.md
[cep-xxx2]: cep-XXX2.md
