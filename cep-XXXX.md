# CEP XXXX - A backwards-compatible repodata update strategy

<table>
<tr><td> Title </td><td> A backwards-compatible repodata update strategy </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td>
  <td>
    Jaime Rodríguez-Guerra &lt;jaime.rogue@gmail.com&gt;,
    Bas Zalmstra &lt;bas@prefix.dev&gt;,
    Wolf Vollprecht &lt;w.vollprecht@gmail.com&gt;
  </td>
</tr>
<tr><td> Created </td><td> Jan 12, 2026 </td></tr>
<tr><td> Updated </td><td> Jan 12, 2026  </td></tr>
<tr><td> Discussion </td><td> ... </td></tr>
<tr><td> Implementation </td><td> N/A </td></tr>
<tr><td> Requires </td><td> N/A </td></tr>
</table>

## Abstract

This document addresses the challenges of updating the specification of `repodata.json` files (and its sharded derivatives) by proposing a strategy based on new top-level fields instead of `repodata_version` bumps.

## Motivation

`repodata.json` files are central to the conda ecosystem. They are the main source of packaging metadata and inform solvers about the catalog of available packages and their dependency constraints. As such, innovation efforts often refrain from modifying it, and the format itself has seen very few changes over its lifetime. However, a few ongoing efforts will inevitably result in `repodata.json` modifications (conditional dependencies, optional dependency groups, non-conda dependencies, etc).

The main problem is the introduction of backwards incompatible changes. The obvious solution is to bump the `repodata_version` field (like it was done with [CEP 15](./cep-0015.md)). However, this is not desirable for existing channels, since it immediately prevents non-compatible clients from interacting with the channel. Since most clients would update via a new version available in the channel, it creates a chichen-and-egg problem that would significantly delay the introduction of new features and hinder adoption.

There must be a strategy to introduce backwards incompatible changes without breaking existing channels. This CEP centralizes the discussion for the update strategy and consolidates that feedback into a concrete proposal.

## Rationale

### Version metadata in `info`

Adding a new field in the `info` dictionary is backwards compatible, and can be used by clients to parse the necessary keys directly without having to traverse the whole dictionary. The migration timestamp is useful for client messaging, like "the client is not recent enough to see all records in this channel, please update to ensure you can obtain access to all packages". They are not added as a top-level field to stop polluting the global namespace.

### Using top-level fields for new metadata schemas

Adding new fields is backwards compatible and does not break older clients, which will simply ignore those and continue operating as usual.

### Not retrofitting for older versions

The solver would provide different solutions depending on the supported versions, which would make behavior surprising and difficult to debug. For example, let's say that optional dependency groups are implemented in `v3`, which requires adding a new `extras` key to the package metadata. `scipy` starts using this in its release `1.20`. As such, this is release is exposed under the `v3` top-level field.

Shortly after a new package `using-scipy` is published, and it has `depends: ["scipy>=1.17"]`. `using-scipy` does not use any `v3` metadata features. If it was published under `packages.conda`, different clients would provide different solutions: older clients with no `v3` support would provide `scipy==1.19`, while newer clients would give `scipy==1.20`. This is confusing and difficult to debug.

Instead, we propose that once a channel starts using the newer repodata revision, all packages are published under the new top-level key. This way, `using-scipy` would simply not exist for older clients, preventing version mismatches in the solution. Using the `info.repodata_revisions` metadata, clients would be able to even provide hints about the possibility of new records being available once client updates are performed.

Another example is the introduction of new archive formats (e.g. `.conda-v3`) in a new repodata revision, for which conda clients would need to implement support. Once the format starts being used, all new packages should be published under the new key so solver asymmetries are minimized.

### Freezing `repodata_version` to `1`

Bumps in this number should only result in backwards incompatible changes that would anyway prevent a channel from operating completely. While `repodata_version: 2` exists (as per CEP 15), its implementations are not sufficiently old to guarantee that the majority of existing conda clients would support it:

- `rattler` supports it [v0.9.0](https://github.com/conda/rattler/blob/main/CHANGELOG.md#090---2023-09-22) (released on 2023-09-22), which means that `pixi` supports it since [v0.4.0](https://github.com/prefix-dev/pixi/blob/d8d2d8a3e8e1ce99707885aa1437e3768614456b/Cargo.toml#L38) (released on 2023-09-22 too).
- `conda` only supports it as of [v24.5.0](https://github.com/conda/conda/blob/main/CHANGELOG.md#2450-2024-05-08) (released on 2024-05-08)
- `mamba` started supporting it in [v2.0](https://github.com/mamba-org/mamba/blob/main/CHANGELOG.md#20240925) (released on 2024-09-25).

Hence, we suggest to stick to `repodata_version: 1` and _only_ use `repodata_version: 2` when a new channel needs a global `base_url` for all the entries in the `packages` and `packages.conda` fields.

## Specification

A repodata revision introduces backwards incompatible features in a way that does not disrupt existing metadata. To do so, a new CEP MUST be proposed, following these guidelines below.

A new item will be added to the `info.repodata_revisions` array, that lists the revisions found in the repodata file as dictionaries with the following schema:

- `revision: int`: The integer identifying the revision.
- `key: str`: The top-level key that contains the records for this revision. It MUST match the regex `[a-z0-9\._]+`. It MUST NOT match any of the existing top-level fields (`repodata_version`, `info`, `packages`, `packages.conda`, `removed`).
- `migrated_at: int`: The timestamp (in milliseconds) that signals when the channel started indexing packages in the new revision.

A new top-level field, with the identifier as specified in `info.repodata_revisions[*].key`. MUST map to a dictionary whose schema is presented in the relevant CEP.

Once a channel starts publishing for a new revision, all packages published after that moment SHOULD be included only in the new revision field, even if some of them may be technically backwards compatible because their record metadata does not use any new features.

The `repodata_version` MUST be `1`.

## Examples

A hypothetical new repodata revision `3` would need to present the following `info.repodata_revisions` entry, accompanied by this sample top-level `v3` field aggregating some of the proposed CEP ideas (at the time of writing, Jan 2026):

```js
{
  "repodata_version": 1,
  "info": {
    "subdir": "noarch",
    "repodata_revisions": [
      {
        "revision": 3,
        "key": "v3",
        "migrated_at": 1768249989751,  // 2026-01-12 20:33 UTC
      }
    ]
  },
  "packages": {
    "example-1.0.0-0.tar.bz2": {
      "build": "0",
      "build_number": 0,
      "depends": [],
      "md5": "82ecc40f09b9c44483e6b70cad2545d7",
      "name": "example",
      "noarch": "generic",
      "sha256": "eb65e866067865793b981c2ba74485f75bef441842b5998badc4ec66717685c7",
      "size": 1234,
      "subdir": "noarch",
      "timestamp": 1689209309623,
      "version": "1.0.0"
    }
  },
  "packages.conda": {
    "example-1.0.0-0.conda": {
      "build": "0",
      "build_number": 0,
      "depends": [],
      "md5": "82ecc40f09b9c44483e6b70cad2545d7",
      "name": "example",
      "noarch": "generic",
      "sha256": "eb65e866067865793b981c2ba74485f75bef441842b5998badc4ec66717685c7",
      "size": 1234,
      "subdir": "noarch",
      "timestamp": 1689209309623,
      "version": "1.0.0"
    }
  },
  "v3": {
    "tar.bz2": {},
    "conda": {
      "example-1.0.0-0": {  // key does not have the extension anymore
        "build": "0",
        "build_number": 0,
        "depends": [
          "package[version=3,build_number=0,if=__unix]"  // bracket syntax, w/ conditional
        ],
        "md5": "82ecc40f09b9c44483e6b70cad2545d7",
        "name": "example",
        "noarch": "generic",
        "sha256": "eb65e866067865793b981c2ba74485f75bef441842b5998badc4ec66717685c7",
        "size": 1234,
        "subdir": "noarch",
        "timestamp": 1768249989851,
        "version": "1.0.0",
        "new_field": "CRITICAL"  // new field
      }
    }
  }
}
```

## Rejected ideas

### Encoding version information in the filename

One alternative would be to create new `repodata.json` filenames (e.g. `repodata.v4.json`) for each new incompatible bump. However, this was rejected by the authors as it introduces complexity in other areas:

- It would require more HTTP calls to retrieve the latest version served by the channel.
- It would introduce duplication across `repodata.json` versions and their shards.
- Indexing tools would need to maintain the different versions of `repodata.json` in sync.

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
