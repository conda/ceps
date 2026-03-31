# CEP 0 - Channel relations in repodata

<table>
<tr><td> Title </td><td> Channel relations in repodata </td></tr>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Bas Zalmstra &lt;bas@prefix.dev&gt;</td></tr>
<tr><td> Created </td><td> Mar 6, 2026 </td></tr>
<tr><td> Updated </td><td> Mar 6, 2026 </td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
</table>

> The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC2119][RFC2119] when, and only when, they appear in all capitals, as shown here.

[RFC2119]: https://datatracker.ietf.org/doc/html/rfc2119

## Abstract

This CEP introduces a mechanism for conda channels to declare relationships to other channels directly in `repodata.json`.
Two types of relations are defined: a _base_ channel (higher priority than the declaring channel) and an _overrides_ channel (lower priority than the declaring channel).
This allows channels to formally declare their dependencies on other channels, removing the need for users to manually specify them.

## Motivation

Many conda channels are designed to be used in combination with other channels.
Two common patterns exist today:

1. **Dependent channels**: `bioconda` relies on packages from `conda-forge`.
   Users are expected to configure both channels with `conda-forge` at a higher priority.
   Failure to do so is a common source of broken environments.
2. **Label channels**: `conda-forge/label/rc` contains release candidate packages that should take priority over the main `conda-forge` channel, with `conda-forge` serving as a fallback for packages the label does not provide.

Currently, the relationship between channels is documented informally (e.g. in READMEs or installation instructions) and must be configured manually by the user.
There is no machine-readable way for a channel to declare that it depends on another channel.

By embedding channel relations in `repodata.json`, which is already fetched by conda clients during normal operation, this information becomes available without requiring additional HTTP requests.
Clients can automatically load related channels, improving the user experience and reducing misconfiguration.

## Specification

> The terms conda channel, channel subdirectory, and channel base URL MUST be understood as specified by [CEP 26](./cep-0026.md).
> The `repodata.json` schema is defined in [CEP 36](./cep-0036.md).

### Channel relations in `info`

A `repodata.json` file MAY include a `channel_relations` key in its `info` dictionary.
If present, `channel_relations` MUST be a dictionary with the following optional keys:

- `base: str`.
  A single channel reference (see [Channel references](#channel-references)) identifying a channel that SHOULD be loaded with _higher_ priority than the declaring channel.
  The base channel provides foundational packages that the declaring channel builds upon.
- `overrides: str`.
  A single channel reference identifying a channel that the declaring channel overrides.
  This channel SHOULD be loaded with _lower_ priority than the declaring channel.

Both keys are OPTIONAL.
If present, their interpretation with regards to the resolved channel list is described in [Building the relation graph](#building-the-relation-graph) below.
If `channel_relations` is absent or empty, the channel declares no relations.
Additional keys in `channel_relations` MUST be ignored to allow future extensions without breaking existing clients.

### Channel references

A channel reference in `channel_relations` MUST be a relative path starting with `../` (e.g. `../conda-forge` or `../..`).
It MUST be resolved relative to the current channel base URL (without the subdir component), as defined in [CEP 26](./cep-0026.md).

For example, if the current channel base URL is `https://conda.anaconda.org/bioconda`, the reference `../conda-forge` resolves to `https://conda.anaconda.org/conda-forge`.
Similarly, if the current channel base URL is `https://conda.anaconda.org/conda-forge/label/rc`, the reference `../..` resolves to `https://conda.anaconda.org/conda-forge`.

For local (`file://`) channels, relative path references could resolve to unintended filesystem locations.
The risk is limited because the resolved path must point to a valid channel with a `repodata.json` structure, but clients MAY apply additional validation for local channel references.

### Sharded repodata

When a channel serves sharded repodata as defined in [CEP 16](./cep-0016.md), the `channel_relations` field MAY also be included in the `info` dictionary of the shard index (`repodata_shards.msgpack.zst`).
This allows clients that use sharded repodata to discover channel relations without needing to fetch `repodata.json` separately.

The schema and semantics of `channel_relations` in the shard index are identical to those in `repodata.json`.
If a channel serves both `repodata.json` and sharded repodata, the `channel_relations` declared in both MUST be consistent.

### Resolution behavior

Channel relations form a directed acyclic graph (DAG) where each node is a channel and each edge encodes a priority relationship.
Clients MUST resolve this graph to produce a linear channel priority order using the algorithm described below.

For each channel in the resolved order, the client SHOULD fetch both the matching platform subdir and the `noarch` subdir.

#### Building the relation graph

Starting from the set of user-specified channels, the client MUST recursively discover all related channels by fetching their `repodata.json` and inspecting `info.channel_relations`.
This process continues until no new channels are discovered.
To guard against excessively deep or misconfigured chains, clients SHOULD support a configurable maximum resolution depth.
The RECOMMENDED name for this configuration option is `channel_relations_max_depth`, with a default value of 10.
A value of 0 SHOULD disable relation resolution entirely.
If the depth limit is exceeded, the client SHOULD abort resolution with an error.

The discovered relations form a directed graph with priority edges:

- A `base` declaration creates an edge from the base channel to the declaring channel, meaning the base channel MUST have higher priority.
- An `overrides` declaration creates an edge from the declaring channel to the overridden channel, meaning the declaring channel MUST have higher priority.

Clients MUST detect cycles in this graph and abort resolution with an error when a cycle is detected.

#### Interaction with user-specified channels

When a user explicitly specifies a channel list (e.g. via `-c` flags or configuration), the user-specified ordering MUST be treated as additional priority edges in the graph.
For each consecutive pair of user-specified channels (A, B), an edge from A to B MUST be added, meaning A has higher priority than B.

These user-specified edges MUST NOT be overridden by channel-declared relations.
If a channel-declared relation contradicts a user-specified edge (e.g. a relation declares that X should have higher priority than Y, but the user specified Y before X), the user-specified edge MUST take precedence.
The conflicting channel-declared edge MUST be ignored.

If a channel that would be introduced by a relation is already present in the user-specified list, it MUST NOT be added a second time.
Its position as determined by the user-specified edges MUST be preserved.

This ensures that users retain full control over channel priority when they choose to specify channels explicitly.
Channel relations only determine the placement of channels that the user did not explicitly list.

#### Topological sorting

The final channel priority order MUST be determined by performing a [topological sort](https://en.wikipedia.org/wiki/Topological_sorting) on the relation graph.
The topological sort produces a linear ordering of channels such that for every priority edge (A → B), channel A appears before channel B (i.e. A has higher priority).

When the topological sort admits multiple valid orderings, the client SHOULD prefer an ordering where channels connected by a relation edge are placed adjacent to each other when possible.
A [depth-first-search-based topological sort](https://en.wikipedia.org/wiki/Topological_sorting#Depth-first_search) naturally achieves this property.

#### Lockfiles

When generating a lockfile, tools SHOULD only record the user-specified ("head") channels, not the full resolved channel graph.
The channel each package originated from is already stored in the `channel` field of individual package records in the lockfile.
Recording only the head channels keeps lockfiles concise and avoids redundancy.
When installing from a lockfile, the `channel` field of each package record MUST take priority over any channel relations declared by the head channels.

#### Deduplication

If the same channel appears multiple times in the resolved graph (e.g. referenced by different subdirs, or by both a direct relation and a transitive relation), it MUST only be represented as a single node.
All priority edges pointing to or from that channel MUST be preserved and applied to the single merged node.

## Examples

### Dependent channels: bioconda

bioconda depends on packages from conda-forge.
Today, users must manually configure both channels.
With channel relations, bioconda's `linux-64/repodata.json` can declare:

```json
{
  "info": {
    "subdir": "linux-64",
    "channel_relations": {
      "base": "../conda-forge"
    }
  },
  "packages": {},
  "packages.conda": {}
}
```

Running `conda install -c bioconda some-package` would result in the following effective channel order (highest priority first):

1. `conda-forge` (base, highest priority)
2. `bioconda`

conda-forge is loaded first because it is bioconda's base (higher priority).
Both the matching platform subdir and `noarch` subdir are fetched for each channel.
Packages from conda-forge are preferred; bioconda adds specialized packages on top.

If the user explicitly specifies both channels, e.g. `conda install -c bioconda -c conda-forge`, the user-specified order is preserved and the relation does not cause conda-forge to be added a second time.

### Label channels: release candidates

`conda-forge/label/rc` contains release candidate packages that should take priority over the main `conda-forge` channel.
The label declares main conda-forge as an override (lower priority):

```json
{
  "info": {
    "subdir": "linux-64",
    "channel_relations": {
      "overrides": "../.."
    }
  },
  "packages": {},
  "packages.conda": {}
}
```

Here `../..` resolves from `https://conda.anaconda.org/conda-forge/label/rc` to `https://conda.anaconda.org/conda-forge`.

Running `conda install -c conda-forge/label/rc some-package` would result in:

1. `conda-forge/label/rc` (declaring channel, highest priority)
2. `conda-forge` (overridden, lower priority)

The label channel has the highest priority.
Its RC packages override the corresponding stable packages from the main channel.
For packages that the label does not provide, the main channel serves as a fallback.

### Transitive resolution

Suppose:

- `my-channel` declares `base: "../bioconda"`
- `bioconda` declares `base: "../conda-forge"`

Running `conda install -c my-channel some-package` would result in:

1. `conda-forge` (bioconda's base, highest priority)
2. `bioconda` (my-channel's base)
3. `my-channel` (lowest priority)

The entire chain is resolved transitively: conda-forge is bioconda's base, so it is loaded first with the highest priority.
bioconda follows.
my-channel comes last with the lowest priority.

### Combining base and overrides

A channel can declare both a base and an overrides:

```json
{
  "info": {
    "subdir": "linux-64",
    "channel_relations": {
      "base": "../conda-forge",
      "overrides": "../my-hotfixes"
    }
  },
  "packages": {},
  "packages.conda": {}
}
```

Effective channel order:

1. `conda-forge` (base, highest priority)
2. `my-channel` (declaring channel)
3. `my-hotfixes` (overridden, lowest priority)

### User-specified channels with relations

Suppose:

- `bioconda` declares `base: "../conda-forge"`
- The user runs `conda install -c conda-forge -c bioconda some-package`

The user has explicitly specified both channels with `conda-forge` first (highest priority).
The relation graph contains:

- User-specified edge: `conda-forge` → `bioconda` (from the `-c` order)
- Relation edge: `conda-forge` → `bioconda` (from the `base` declaration)

Both edges agree, so the resolved order is:

1. `conda-forge` (highest priority)
2. `bioconda`

Now suppose the user instead runs `conda install -c bioconda -c conda-forge some-package` (reversed order):

- User-specified edge: `bioconda` → `conda-forge` (from the `-c` order)
- Relation edge: `conda-forge` → `bioconda` (from the `base` declaration)

The edges conflict.
The user-specified edge takes precedence, and the relation edge is ignored.
The resolved order is:

1. `bioconda` (highest priority)
2. `conda-forge`

### Independent subdir declarations

Each subdir independently declares its own relations.
A channel MAY have different relations for different subdirs.
If multiple subdirs reference the same channel, the client MUST only load that channel once in the resolved channel list (see [Deduplication](#deduplication)).

## Compatibility

This CEP adds an optional key to the `info` dictionary of `repodata.json`.
As specified in [CEP 36](./cep-0036.md), additional keys in the `info` dictionary "SHOULD NOT be present and SHOULD be ignored."
Clients that do not recognize `channel_relations` will therefore ignore it.
No change to `repodata_version` is REQUIRED.

Channels that add `channel_relations` to their `repodata.json` remain fully compatible with older clients.
The only difference is that older clients will not automatically load related channels, requiring users to specify them manually as before.

## Open questions

- **Security implications**: A channel can declare relations to arbitrary other channels, causing additional package sources to be loaded without explicit user consent.
  Should clients provide a mechanism to opt out of automatic relation resolution?
  Should users be warned when new channels are pulled in via relations?
  These questions are deferred to future work or implementation-specific decisions.

## Future work

- **Indexing tools**: Channel indexing tools such as `conda-index` and `rattler-index` will need a mechanism to allow channel maintainers to specify channel relations so they can be written into the generated `repodata.json`.
  One idea discussed was to use a dedicated "meta" package (e.g. `conda-forge-channel-relations`) similar to how repodata patches work today, but this is explicitly left out of this CEP.
  The exact configuration format is left up to individual indexing tools and servers.

## Rejected ideas

### Separate metadata file for channel relations

An earlier design considered serving channel relations as a dedicated file (e.g. `channel_relations.json`) at the channel root.
This was rejected because `repodata.json` is already fetched by all conda clients during normal operation.
A separate file would require an additional HTTP request per channel, introducing latency and complexity for both clients and channel maintainers.

### Multiple base channels

An earlier version of this proposal allowed `base` to be a list of channels.
This was rejected because multiple base channels introduce ordering ambiguity: if base channels themselves declare relations, determining a correct priority order requires resolving potentially conflicting constraints.
By restricting `base` to a single channel, the base chain is always linear and easy to reason about.
Channels that need packages from multiple sources can achieve this by chaining base relations (e.g. bioconda bases on conda-forge, which could itself base on defaults).

### Channel-level rather than subdir-level declarations

Declaring relations once per channel (e.g. in `channeldata.json`) rather than per subdir was considered.
This was rejected for two reasons: first, `channeldata.json` is optional and not fetched by all clients (see [CEP 38](./cep-0038.md)), while `repodata.json` is the only file that clients are required to fetch (see [Separate metadata file for channel relations](#separate-metadata-file-for-channel-relations) for the same argument).
Second, per-subdir declarations allow channels to have different relations for different platforms if needed, which could be useful for channels that only depend on another channel for certain architectures.

### Bumping `repodata_version`

Adding `channel_relations` could have required incrementing `repodata_version` to signal the new capability.
This was rejected because the field is purely additive and backward compatible.
As specified in [CEP 36](./cep-0036.md), unrecognized keys in the `info` dictionary are ignored by existing clients.
A version bump would force older clients to reject the entire `repodata.json`, which is undesirable.

### Bare channel names and absolute URLs as references

Earlier versions of this proposal allowed channel references to be specified as bare names (e.g. `conda-forge`) or absolute URLs (e.g. `https://conda.anaconda.org/conda-forge`).
Bare names were rejected because they are ambiguous: resolving a bare name requires knowing a default channel server, which varies across client configurations.
Absolute URLs were rejected because they pose a security risk (a channel could pull in packages from an arbitrary domain) and may not work correctly behind firewalls or with mirror setups.
Restricting references to relative paths ensures that related channels always live on the same domain as the declaring channel, which is both safer and more compatible with mirroring.

### Symmetric relation types (e.g. "depends" / "supplements")

Alternative naming schemes were considered, including `parent`/`child`, `depends`/`supplements`, and `primary`/`fallbacks`.
The chosen names `base` and `overrides` were selected because they most clearly communicate the priority direction.
See [Naming: base and overrides](#naming-base-and-overrides) for the rationale.

## Rationale

### Embedding in `repodata.json` rather than a separate file

Channel relations are embedded in `repodata.json` rather than served as a separate metadata file (e.g. `channel_relations.json`) because `repodata.json` is already fetched by all conda clients during normal operation.
Adding a separate file would require an additional HTTP request per channel, introducing latency and complexity.

### Single base channel

This CEP restricts the `base` relation to a single channel rather than a list.
While multiple base channels could be useful, supporting them introduces ordering ambiguity when those base channels themselves declare relations.
A single base channel keeps the resolution algorithm simple and predictable: the transitive chain of base relations is always linear.
Channels that need packages from multiple sources can achieve this by chaining base relations (e.g. bioconda bases on conda-forge, which could itself base on defaults).

### Per-subdir declarations

Channel relations are declared per subdir rather than per channel because `repodata.json` is inherently a per-subdir file.
This also allows channels to have different relations for different platforms if needed, though in practice most channels will declare the same relations across all subdirs.

### Naming: base and overrides

The term _base_ communicates that the referenced channel provides a foundation of packages and has higher priority.
The declaring channel builds on top of it.

The term _overrides_ communicates the direction of priority: the declaring channel overrides the referenced channel.
The referenced channel has lower priority and serves as a fallback for packages the declaring channel does not provide.
This naturally fits the label channel use case, where `conda-forge/label/rc` overrides `conda-forge`.

## References

- [CEP 15 - Hosting repodata.json and packages separately](./cep-0015.md)
- [CEP 16 - Sharded repodata](./cep-0016.md)
- [CEP 26 - Identifying Packages and Channels in the conda Ecosystem](./cep-0026.md)
- [CEP 36 - Package metadata files served by conda channels](./cep-0036.md)

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
