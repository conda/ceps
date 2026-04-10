# CEP XXXX - Index timestamp in package record metadata

<table>
<tr><td> Title </td><td> Index timestamp in package record metadata </td></tr>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Jannis Leidel </td></tr>
<tr><td> Created </td><td> Mar 4, 2026 </td></tr>
<tr><td> Updated </td><td> Apr 10, 2026 </td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/154 </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
<tr><td> Requires </td><td> CEP 36 </td></tr>
</table>

> The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC2119][RFC2119] when, and only when, they appear in all capitals, as shown here.

[RFC2119]: https://datatracker.ietf.org/doc/html/rfc2119

## Abstract

This CEP proposes adding an optional `indexed_timestamp` field to per-record metadata in `repodata.json`, as specified by [CEP 36](./cep-0036.md). Unlike the existing `timestamp` field (which records build time and is set by the package builder), `indexed_timestamp` is set by the channel server when an artifact first appears in the channel index, providing a trustworthy, server-controlled record of when the package became available to users.

## Motivation

The conda ecosystem currently lacks a reliable, per-artifact indicator of when a package was made available on a channel. This gap has practical consequences for two emerging use cases: supply chain security and environment reproducibility.

### The `timestamp` field is builder-controlled

[CEP 34](./cep-0034.md) defines `timestamp` in `info/index.json` as "Starting time of the package build", expressed as Unix time in milliseconds. This value propagates into `repodata.json` as specified by [CEP 36](./cep-0036.md). Because it is set by the build tool (`conda-build`, `rattler-build`), a package author or malicious actor can set it to any value. The `common-1` schema at schemas.conda.org also marks this field as `patchable: true`.

### `channeldata.json` is too coarse

[CEP 38](./cep-0038.md) specifies a `timestamp` field in `channeldata.json`, defined as "Upload date of the most recently published artifact". While this is server-controlled, it is per-package-name, not per-artifact. It only reflects the most recent upload and cannot be used to determine when a specific version or build was published.

### Ecosystem precedent

PyPI provides server-controlled `upload_time` and `upload_time_iso_8601` fields per release file in its JSON API. These are set by the PyPI server at upload time and cannot be modified by package authors. This is the foundation for reliable tools like:

- `uv --exclude-newer` and `pip --exclude-newer` for reproducible resolution
- Dependency cooldown features that delay installation of recently published packages as a supply chain security measure

Within the conda ecosystem, pixi already provides an [`exclude-newer`](https://pixi.prefix.dev/latest/reference/pixi_manifest/#exclude-newer-optional) option, but it currently relies on the builder-controlled `timestamp` field. The conda ecosystem would benefit from a trustworthy server-controlled equivalent.

### Channel models have different risk profiles

The value of a server-controlled index timestamp varies by channel model. Curated channels like Anaconda's defaults already have human review gates before packages reach users, similar to the Debian model. Community forges like conda-forge release at the speed of volunteer CI, where packages can go from merged PR to indexed artifact in minutes. Cooldown support is most critical for these faster-moving channels.

### Use cases

1. **Dependency cooldowns**: A configurable time window that excludes packages published too recently from being installed, giving security vendors time to flag malicious packages. See [conda/conda#15759](https://github.com/conda/conda/issues/15759) and [William Woodruff's analysis](https://blog.yossarian.net/2025/11/21/We-should-all-be-using-dependency-cooldowns) of supply chain attack windows.

2. **Reproducible environments**: Resolving an environment as it would have looked at a specific point in time (similar to `uv --exclude-newer`), using the publication date rather than the build date.

3. **Auditing and forensics**: Determining exactly when a given artifact appeared on a channel, independent of when it was built.

## Specification

### Package record metadata

[CEP 36](./cep-0036.md) defines the schema for entries in `packages` and `packages.conda` within `repodata.json`. This CEP adds one optional field to the package record metadata:

- `indexed_timestamp: int`. Optional. Unix time in milliseconds when the artifact was added to the channel index. It MUST be set by the channel server or indexing tool, not by the build tool. If absent, clients MAY fall back to `timestamp` for time-based operations.

### Channel server requirements

Channel servers and indexing tools (such as `conda-index`, `quetz`, or Anaconda's infrastructure) SHOULD set `indexed_timestamp` on each package record when the artifact is first indexed into the channel. The value MUST reflect the actual time the artifact became available in the channel, not the build time or any value from the artifact itself. The `repodata-record-1` schema at schemas.conda.org SHOULD be updated accordingly.

For artifacts that predate this CEP and lack an `indexed_timestamp`, channel servers MAY seed the value from the artifact's `timestamp` field or from another server-side signal such as file modification time. This is acceptable because the security benefits of `indexed_timestamp` (dependency cooldowns, exclude-newer) protect against the initial publication window, which has long closed for existing artifacts. For artifacts first indexed after this CEP is approved, the value MUST be set by the server at indexing time.

### Timestamp validation

When indexing an artifact, channel servers SHOULD validate that the artifact's `timestamp` value is not in the future and that `timestamp <= indexed_timestamp`. Artifacts that violate these constraints SHOULD be rejected or flagged, as a future `timestamp` may indicate a misconfigured build or an attempt to manipulate time-based resolution.

### Client behavior

Conda clients that implement time-based filtering (e.g., dependency cooldowns, exclude-newer) SHOULD prefer `indexed_timestamp` when present. If `indexed_timestamp` is absent, clients MAY fall back to `timestamp` with appropriate documentation that the value is builder-controlled.

## Rationale

### Why per-record, not per-package

`channeldata.json` (CEP 38) already tracks an upload date, but at the package-name level. Different versions and builds of the same package are published at different times, so a per-record field is necessary for meaningful time-based filtering.

### Why server-controlled

The `timestamp` field is builder-controlled and has known issues: it can be set to any value by the packager, and it reflects when the build started rather than when the package became available to users. A server-controlled field closes this gap.

### Why `indexed_timestamp`, not `upload_timestamp`

The field measures when the artifact appeared in the channel index, not when it was uploaded. In many conda workflows, these are distinct events. For example, conda-forge uploads built artifacts to a staging channel (`cf-staging`), validates them, and only then copies them to the production `conda-forge` channel where they are indexed into `repodata.json`. The `conda-index` maintainer also describes this as tracking when a package was "first indexed" rather than when it was uploaded. The name `indexed_timestamp` accurately reflects this, and fits naturally alongside the existing `timestamp` field in the package record schema.

### Not subject to repodata patching

Because `indexed_timestamp` is a server-controlled fact about when an artifact entered the index, it should not be modified by repodata patching. Repodata patches are intended for correcting package-side metadata (such as dependency constraints), not for altering server-side provenance.

### Why optional

Not all channel servers may be able to provide this field immediately. Making it optional allows gradual adoption while clients can fall back to `timestamp`.

### Backwards compatibility

Adding an optional field to existing package records in `packages` and `packages.conda` is a purely additive change. [CEP 36](./cep-0036.md) states that additional keys "SHOULD NOT be present and SHOULD be ignored", meaning older clients will silently ignore `indexed_timestamp`. This does not require the repodata revision mechanism proposed in [conda/ceps#146](https://github.com/conda/ceps/pull/146), though it is consistent with that proposal's philosophy of backwards-compatible evolution.

This follows the same pattern as the `url` field proposed in [conda/ceps#151](https://github.com/conda/ceps/pull/151), which also adds an optional per-record field to the existing schema.

### Why milliseconds

For consistency with the existing `timestamp` field (CEP 34) and `channeldata.json` timestamp (CEP 38), both of which use Unix time in milliseconds.

## References

- [CEP 34 - Contents of conda packages](./cep-0034.md)
- [CEP 36 - Package metadata files served by conda channels](./cep-0036.md)
- [CEP 38 - Channel-wide metadata files served by conda channels](./cep-0038.md)
- [conda/ceps#146 - A backwards-compatible repodata update strategy](https://github.com/conda/ceps/pull/146)
- [conda/ceps#151 - URL field for package records](https://github.com/conda/ceps/pull/151)
- [schemas.conda.org - repodata-record-1.schema.json](https://schemas.conda.org/repodata-record-1.schema.json)
- [schemas.conda.org - common-1.schema.json](https://schemas.conda.org/common-1.schema.json)
- [PyPI JSON API - upload_time field](https://warehouse.pypa.io/api-reference/json.html)
- [conda/conda#15759 - Dependency cooldowns](https://github.com/conda/conda/issues/15759)
- [William Woodruff - We should all be using dependency cooldowns](https://blog.yossarian.net/2025/11/21/We-should-all-be-using-dependency-cooldowns)
- [Andrew Nesbitt - Package managers need to cool down](https://nesbitt.io/2026/03/04/package-managers-need-to-cool-down.html)
- [Andrew Nesbitt - Package security defenses for AI agents](https://nesbitt.io/2026/04/09/package-security-defenses-for-ai-agents.html)

---

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
