# CEP XXXX - Channel Registration of Virtual Package Detectors

<table>
<tr><td> Title </td><td> Channel Registration of Virtual Package Detectors </td></tr>
<tr><td> Status </td><td> Proposed </td></tr>
<tr><td> Author(s) </td><td> Julian Hofer &lt;julian@prefix.dev&gt;, Wolf Vollprecht &lt;wolf@prefix.dev&gt;, Tobias Hunger &lt;tobias@prefix.dev&gt;</td></tr>
<tr><td> Created </td><td> Aug 5, 2026</td></tr>
<tr><td> Updated </td><td> Sep 18, 2026</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/188, https://github.com/conda/ceps/pull/192 </td></tr>
<tr><td> Implementation </td><td> https://github.com/conda/rattler/pull/2701 (stack) </td></tr>
<tr><td> Requires </td><td> https://github.com/conda/ceps/pull/191 (Virtual Package Detector Protocol), CEP 16, CEP 26, CEP 30, CEP 36, CEP 42 </td></tr>
</table>

> The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT",
> "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as
> described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) when, and only when, they appear in all capitals, as shown here.

## Abstract

This CEP lets channels register virtual package detectors in `repodata.json`.
Clients resolve the detectors from the registering channel and its related channels, then use the detected virtual packages in the solve.
The [detector protocol](https://github.com/Hofer-Julian/ceps/blob/virtual-package-detector-protocol/cep-XXXX.md) defines execution, and this CEP adds channel discovery, priority and consent.

## Motivation

The conda-forge external MPI packages require users to install their detector into conda before creating an environment.
Channel registrations remove that setup step: adding the channel also makes its detection available.

## Specification

Channels and subdirs follow [CEP 26](./cep-0026.md); package-name comparisons MUST use normalized names.
Repodata follows [CEP 36](./cep-0036.md), and channel relations and priority follow [CEP 42](./cep-0042.md).
A channel's registrations participate whenever the channel does, whether configured directly or loaded through relations.

### Registration metadata

A channel MAY include `virtual_package_detectors` in the `info` dictionary of `repodata.json`.
For example, conda-forge could register a proposed `mpi-detect` package to report the names used by its [existing MPI detector](https://github.com/regro/conda-forge-conda-plugins):

```json
{
  "info": {
    "subdir": "linux-64",
    "virtual_package_detectors": {
      "mpi-detect": ["__conda_forge_openmpi", "__conda_forge_mpich"]
    }
  }
}
```

Each key is equal to both the detector package name and the name of its [executable](https://github.com/Hofer-Julian/ceps/blob/virtual-package-detector-protocol/cep-XXXX.md#the-detector-package).
Its array lists the virtual packages reported by the detector.

A client MUST read the field as an opaque JSON value before validating it, so invalid registrations do not prevent parsing the rest of the repodata.
An absent field or empty dictionary registers no detectors. Otherwise:

- The value MUST be a dictionary mapping detector package names to arrays of virtual package names. `null` and incorrectly shaped values are registration errors.
- Each key MUST be a valid installable package name, not a virtual package name beginning with `__`, and MUST name a package served by the declaring channel in one of its subdirs. An invalid key is a registration error.
  Failure to resolve a syntactically valid name is a [detector failure](https://github.com/Hofer-Julian/ceps/blob/virtual-package-detector-protocol/cep-XXXX.md#failure-handling).
- Each array MUST contain 1 to 16 entries. Names MUST satisfy the detector protocol's [name rules](https://github.com/Hofer-Julian/ceps/blob/virtual-package-detector-protocol/cep-XXXX.md#registrations).
- Clients MUST drop invalid virtual package names, SHOULD report them, and MUST ignore detectors left with no valid names. The remaining names are the registration's virtual package names.

#### Subdirs and limits

Clients MUST combine registrations from the target platform's subdir and `noarch` only.

The following are registration errors in the combined registration set:

- Detectors in different subdirs that have the same normalized name but specify different virtual packages.
- An array outside the 1 to 16 entry limit, or a detector's union exceeding 16 names, counted before invalid names are dropped.
- More than 64 distinct detectors, counted before empty registrations are removed.
- Two detectors declaring the same normalized virtual package name, or a duplicate normalized name within one array.
- Distinct virtual package names mapping to the same [override variable](https://github.com/Hofer-Julian/ceps/blob/virtual-package-detector-protocol/cep-XXXX.md#registrations).
- Duplicate normalized detector keys within one subdir's dictionary. Clients whose JSON parser cannot expose duplicate keys need not detect them.

Clients MUST report any registration error and ignore the channel's entire combined registration set.
They MUST NOT reject the surrounding repodata or abort the solve.

#### Sharded repodata

For [CEP 16](./cep-0016.md) sharded repodata, `virtual_package_detectors` MAY appear in the shard index's `info` dictionary with the same schema and semantics.
A channel serving both forms MUST publish consistent registrations. Clients need only read the form they loaded.

### Names and channel priority

A virtual package name has one meaning throughout a solve.
For names not standardized by a CEP, channels SHOULD include their channel name, for example `__conda_forge_mpi_abi` rather than `__mpi_abi`.
Channels SHOULD register standardized names only to replace client detection, following the detector protocol's [standardized-name rules](https://github.com/Hofer-Julian/ceps/blob/virtual-package-detector-protocol/cep-XXXX.md#results-in-the-solve).

Clients MUST be able to deal with different channels registering the same virtual package names.
Clients MUST process registrations in CEP 42's resolved channel order.
A registration MUST be rejected if any of its virtual package names conflicts with an already accepted registration by normalized name or override variable; otherwise it MUST be accepted.
Accepted registrations reserve all their names for the solve across all channels.
Rejected registrations reserve no names, and their detectors MUST NOT be run.

### Resolution and participation

A registration's origin is the registering channel's [CEP 26](./cep-0026.md) base URL.

Its resolution channels are the ordered channels [CEP 42](./cep-0042.md) would resolve with that channel.
If a cycle or depth limit prevents relation resolution, clients MUST use the registering channel alone and SHOULD warn.

### Consent and user controls

Configuring a channel consents to running its registered detectors, including those of channels loaded through its relations.
Clients MAY require additional opt-in.

## Example

Suppose conda-forge registers `mpi-detect` as above and adds `__conda_forge_openmpi >=5.0,<6.0a0` to an external Open MPI build's dependencies.
When solving for that build on the host platform, the client installs `mpi-detect` and its dependencies from conda-forge in a detector environment.
The detector finds `/opt/openmpi/bin/ompi_info` on `PATH`, identifies Open MPI 5.0.10, and reports:

```json
{
  "version": 1,
  "virtual_packages": {
    "__conda_forge_openmpi": { "version": "5.0.10" },
    "__conda_forge_mpich": null
  }
}
```

The `__conda_forge_openmpi 5.0.10` record satisfies the dependency through ordinary MatchSpec matching.
Without Open MPI, the detector reports `null` for `__conda_forge_openmpi` too, leaving that external build's dependency unsatisfiable.
Packages from other channels, including those that load conda-forge through a relation, use the same result.

## Backwards compatibility

The optional `info.virtual_package_detectors` field requires no `repodata_version` change.
Under CEP 36, clients SHOULD ignore unrecognized `info` keys; clients without detector support cannot satisfy dependencies on names they do not otherwise provide.
Channels without registrations are unaffected, and detector packages need no new `index.json` fields.

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
