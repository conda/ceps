# CEP XXXX - OCI Registries as conda Channels

<table>
<tr><td> Title </td><td> OCI Storage of conda Artifacts </td>
<tr><td> Status </td><td> Proposed </td></tr>
<tr><td> Author(s) </td><td> Wolf Vollprecht &lt;wolf@prefix.dev&gt;<br /> Hind Montassif &lt;hind.montassif@quantstack.net&gt;<br /> Matthew R. Becker &lt;becker.mr@gmail.com&gt;<br /> Jaime Rodríguez-Guerra &lt;jaime.rogue@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> April 12, 2024</td></tr>
<tr><td> Updated </td><td> March 10, 2025</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/115; https://github.com/conda/ceps/pull/70 </td></tr>
<tr><td> Implementation </td><td>  </td></tr>
</table>

## Table of Contents

- [Abstract](#abstract)
- [Background on OCI Registries and OCI Artifacts](#background-on-oci-registries-and-oci-artifacts)
- [Specification](#specification)
  - [Specification Version and Compatible OCI Specifications](#specification-version-and-compatible-oci-specifications)
  - [Example Forms of a Valid OCI conda URL](#example-forms-of-a-valid-oci-conda-url)
  - [Channel Base URL and Subdirs](#channel-base-url-and-subdirs)
  - [Subdir Repository Namespace Designations](#subdir-repository-namespace-designations)
  - [Conda Artifact OCI Repository Names](#conda-artifact-oci-repository-names)
  - [Conda Artifact OCI Tags](#conda-artifact-oci-tags)
  - [Repodata, Run Exports, and Patch Instructions Artifact Names and Tags](#repodata-run-exports-and-patch-instructions-artifact-names-and-tags)
  - [Channeldata Artifact Names and Tags](#channeldata-artifact-names-and-tags)
  - [Further Stipulations Related to OCI conda Chennal Repositories and Tags](#further-stipulations-related-to-oci-conda-chennal-repositories-and-tags)
  - [Allowed Blob mediaTypes](#allowed-blob-mediatypes)
  - [OCI Artifact Structure for Conda Packages](#oci-artifact-structure-for-conda-packages)
  - [OCI Artifact Structure for Repodata, etc.](#oci-artifact-structure-for-repodata-etc)
- [Rationale](#rationale)
- [Backwards Compatibility](#backwards-compatibility)
- [Alternatives](#alternatives)
- [Sample Implementation](#sample-implementation)
- [References](#references)
- [Copyright](#copyright)

## Abstract

This CEP defines how to use an *OCI registry* as a conda channel and how store conda packages/repodata in an *OCI registry*
as *OCI artifacts* (see the [Open Containers Initiative][oci] (OCI) and the definitions below for more details on these terms).
While conda channels are essentially any valid URL (possibly percent-encode and with a specific path hierarchy), OCI registries
have comparably tighter constraints (reproduced below for completeness) on the allowed characters, formats, and lengths of the
*OCI artifact* `<name>` and the artifact's *OCI tag* (i.e., `<name>:<tag>`). This situation creates the non-trivial problem of
how to translate the various conda URL components (e.g., channel, subdir, label) and conda artifact components (e.g., package
name, version, and build string) into a valid OCI artifact `<name>:<tag>`. This CEP resolves this situation by first, restricting
the set of allowed channel, subdir and label names to a subset that is OCI-compatible, and second, defining a custom encoding of
the conda package name, version, and build string into an OCI-compatible form. Finally, this CEP defines how to map the data in
a conda package and in conda repodata into OCI artifacts.

This CEP does NOT describe how to generate conda repodata from an existing OCI registry. It also does NOT describe how to store
sharded repodata, defined in [CEP 16][cep16], in an OCI registry. We leave these topics for future CEPs.

> [!NOTE]
> The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT",
> "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as
> described in [RFC2119][RFC2119] when, and only when, they appear in all capitals, as shown here.

## Background on OCI Registries and OCI Artifacts

The [Open Containers Initiative][oci] (OCI) defines an open standard for container images and their distribution. They define the following terms used in this CEP:

- *OCI registry*: A service that implements the [OCI Distribution Spec][ocidist] (e.g., `ghcr.io`).
- *OCI artifact*: A container image stored in an OCI registry, specified by its OCI repository and OCI tag `<name>:<tag>`.
  Internally, an artifact consists of an OCI manifest and a set of OCI blobs (layers) that hold the artifact's data.
- *OCI repository*: A collection of OCI artifacts with the same container or image `<name>` in an OCI registry.
- *OCI tag*: A label for a specific container image within an OCI repository, identified by its `<tag>`.
- *OCI blob*: A binary blob stored in an OCI registry identified by its mediaType, digest, and size.
- *OCI manifest*: A JSON document that describes the contents of an OCI artifact, organized as some metadata and a number of blobs.
  The manifest is also stored in the registry as a blob.

We have given informal definitions of the terms above. See the full OCI specifications, the [OCI Image Spec][ociimage] and the
[OCI Distribution Spec][ocidist], for precise definitions of these terms.

Finally, per the [OCI Distribution Spec][ocidist] `v1.*`, the `<name>` and `<tag>` of an OCI repository MUST match the following regexes:

- `<name>`: `^[a-z0-9]+((\.|_|__|-+)[a-z0-9]+)*(\/[a-z0-9]+((\.|_|__|-+)[a-z0-9]+)*)*$`
- `<tag>`: `^[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}$`

The [OCI Distribution Spec][ocidist] further notes that "Many clients impose a limit of 255 characters on the length of the
concatenation of the registry hostname (and optional port), /, and `<name>` value."

These constraints play an important role in the design of this specification, as they limit the allowed characters,
character ordering, and lengths to a subset of conda's allowed namespace.

## Specification

In this specification, we use the following conda-specific terminology:

- *OCI-compatible `<channel path/subdir/label>`*: A conda channel, subdir, or label that is valid according to the regexes
  that define valid OCI repository `<name>`s. This regex is given above.
- *OCI-encoded package name*: The name of a conda package that is encoded to a specific format (defined below) for use in
  an OCI repository `<name>`. The language "encoded to OCI form" is used below to refer to this process.
- *OCI-encoded version/build string*: A conda package version or build string that is encoded to a specific format
  (defined below) for use in an OCI image `<tag>`. The language "encoded to OCI form" is used below to refer to this process.
- *hashed `<component>`*: A string component of an OCI repository name or OCI tag, possibly the entire `<name>` or `<tag>`,
  hashed with SHA256 and then formatted as `h<SHA256 in hexadecimal>`.

### Specification Version and Compatible OCI Specifications

This specification is labeled `v1`. Any implementation of this specification MUST use the `v1.*` OCI specification.

### Example Forms of a Valid OCI conda URL

The following are valid example forms of an OCI conda URL:

```text
oci://<authority>/<OCI-compatible channel path>[/label/<OCI-compatible label>]/<OCI-compatible subdir>/<OCI-encoded package name>:<OCI-encoded version>-<OCI-encoded build>
oci://<authority>/<OCI-compatible channel path>[/label/<OCI-compatible label>]/<OCI-compatible subdir>/mrepodata.json:latest
oci://<authority>/<OCI-compatible channel path>[/label/<OCI-compatible label>]/<OCI-compatible subdir>/mcurrent_repodata.json:latest
oci://<authority>/<OCI-compatible channel path>[/label/<OCI-compatible label>]/<OCI-compatible subdir>/mrepodata_from_packages.json:latest
oci://<authority>/<OCI-compatible channel path>[/label/<OCI-compatible label>]/<OCI-compatible subdir>/mrun_exports.json:latest
oci://<authority>/<OCI-compatible channel path>[/label/<OCI-compatible label>]/<OCI-compatible subdir>/mpatch_instructions.json:latest
oci://<authority>/<OCI-compatible channel path>[/label/<OCI-compatible label>]/channeldata.json:latest
```

The various parts of the URL are defined below.

### Channel Base URL and Subdirs

The base URL for an OCI conda channel MUST be formatted as follows:

```text
oci://<authority>/<OCI-compatible channel path>[/label/<OCI-compatible label>]
```

where `<authority>` is any valid [RFC 3986][rfc3986] authority which is also supported by the OCI `v1.*` specification.
This string will typically be `<hostname>[:<port>]` (e.g., `ghcr.io` with no port specified). OCI conda channel URLs MUST
use `oci` as the scheme. OCI-compatible channel path and labels are defined below. If the `<OCI-encoded label>` is `main`,
the entire optional label component MUST be omitted. Otherwise, the label component MUST be present.

The base URL for an OCI conda channel is the canonical, unique identifier for the channel itself and SHOULD be used in
conda ecosystem tools to refer to the channel.

Conda `<OCI-compatible subdir>`s are appended to this base URL as follows:

```text
<OCI conda channel base URL>/<OCI-compatible subdir>
```

where `<OCI-compatible subdir>` is defined below.

The following regexes MUST be satisfied by the `<OCI-compatible channel path>`, `<OCI-compatible subdir>`, and `<OCI-compatible label>` strings:

- `<OCI-compatible channel path>`: `^[a-z0-9]+((\.|_|__|-+)[a-z0-9]+)*(\/[a-z0-9]+((\.|_|__|-+)[a-z0-9]+)*)*$` (same as the regex for an OCI repository `<name>`)
- `<OCI-compatible label>`: `^[a-z0-9]+((\.|_|__|-+)[a-z0-9]+)*(\/[a-z0-9]+((\.|_|__|-+)[a-z0-9]+)*)*$` (same as the regex for an OCI repository `<name>`)
- `<OCI-compatible subdir>`: `^(([a-z0-9]+-[a-z0-9]+)|noarch)$`

### Subdir Repository Namespace Designations

The namespace after the combination `<OCI conda channel base URL>/<OCI-compatible subdir>/` has the following designations
(where the `*` wildcard indicates any valid OCI repository `<name>` component or part of a component as allowed by
the OCI repository `<name>` regex):

- `<OCI conda channel base URL>/<OCI-compatible subdir>/m*`: reserved for metadata specific to subdirs (e.g., various
  forms of repodata, repodata patches, run exports, etc.)
- `<OCI conda channel base URL>/<OCI-compatible subdir>/c*`: reserved for OCI-encoded conda package names (The character `c`
  is prepended to the conda package name to indicate that it is an OCI-encoded conda package name as described below.)
- `<OCI conda channel base URL>/<OCI-compatible subdir>/h*`: reserved for hashed OCI-encoded conda package names

These designations are used to prevent namespace collisions between the various components of an OCI conda channel. Any other string prefixes MUST NOT be used.

### Conda Artifact OCI Repository Names

Conda artifacts MUST be stored in the OCI repository of an OCI conda channel under their `<OCI-compatible subdir>` as the OCI repository

```text
<OCI conda channel base URL>/<OCI-compatible subdir>/<OCI-encoded package name>
```

The contents and mediaTypes of OCI blobs that make up the conda package artifact, along with how to compute the OCI tag, are defined below as well.

The `<OCI-encoded package name>` MUST be computed according to the following rules:

- All package names MUST be prepended by the character `c`.
- If the `<OCI-encoded package name>` exceeds 64 characters in length, the
  `<OCI-encoded package name>` MUST be replaced by the SHA256 hash of the
  `<OCI-encoded package name>` in hexadecimal form as `h<SHA256 in hexadecimal>`.
  The letter `h` is reserved to indicate a hashed OCI-encoded package name as described above.

`<OCI-encoded package name>`s that are not hashed can be decoded by reversing the encoding rules above.

For example, the package name `_libgcc_mutex` is encoded to OCI-form as `c_libgcc_mutex`, and the package name `c_libgcc_mutex`
is encoded to OCI-form as `cc_zlibgcc_mutex`. A very long package name like `gblah000...000` would be encoded to its OCI-form
`cgblah000...000`, then hashed via SHA256, yielding something like `h<hexdigest of SHA256 hash>`.

### Conda Artifact OCI Tags

The OCI tag for a conda package MUST be computed from the packages `<OCI-encoded version>` and `<OCI-encoded build string>` as follows.

First, the `<OCI-encoded version>` and `<OCI-encoded build string>` are computed from conda package's `<version>` and `<build string>`
respectively. To do this, one MUST apply the mapping rules below to the conda package's `<version>` or `<build string>`
in the order listed, top to bottom:

- `_` -> `__`
- `+` -> `_P`
- `!` -> `_N`

To undo this encoding, one MUST apply the rules in reverse, starting at the bottom of the list and moving to the top.
OCI Tags, unlike OCI Repository `<name>`s, have no limit on the number of separators that can be used in a row. Thus,
the double underscore `__` is safe to use here as a separator.

Next, the `<OCI-encoded version>` and `<OCI-encoded build string>` MUST be combined with a `-` to form the OCI `<tag>`

```text
<OCI-encoded version>-<OCI-encoded build>
```

Finally, if the entire OCI `<tag>` exceeds 128 characters in length, the entire tag MUST be hashed with the SHA256 algorithm
and the resulting OCI tag is then `h<SHA256 in hexadecimal>`.

### Repodata, Run Exports, and Patch Instructions Artifact Names and Tags

The unsharded repodata, repodata from packages (if present), run exports (if present), current repodata (if present)
and patch instructions (if present) for an OCI conda channel MUST be stored as an OCI artifact under the
`<OCI-compatible subdir>` as

```text
<OCI conda channel base URL>/<OCI-compatible subdir>/mrepodata.json:latest
<OCI conda channel base URL>/<OCI-compatible subdir>/mrepodata_from_packages.json:latest
<OCI conda channel base URL>/<OCI-compatible subdir>/mrun_exports.json:latest
<OCI conda channel base URL>/<OCI-compatible subdir>/mcurrent_repodata.json:latest
<OCI conda channel base URL>/<OCI-compatible subdir>/mpatch_instructions.json:latest
```

respectively. The contents and mediaTypes of the OCI blobs that make up each of these kinds of data are defined below.
The `mcurrent_repodata.json`, `mrepodata_from_packages.json`, `mpatch_instructions.json`, and `mrun_exports.json`
artifacts MAY not be present on all OCI conda channels.

The OCI tag `latest` MUST always refer to the copy of the repodata / run exports currently in use.

Older copies of the repodata / run exports MAY be stored as well. If older copies of the repodata / run exports are stored,
they MUST use an OCI tag that is the UTC time formatted as `YYYYMMDDThhmmssZ`.

### Channeldata Artifact Names and Tags

The `channeldata.json` for an OCI conda channel MUST be stored as an OCI artifact as

```text
<OCI conda channel base URL>/channeldata.json:latest
```

where the contents and mediaTypes of the OCI blobs that make up the `channeldata.json` artifact are defined below.

The OCI tag `latest` MUST always refer to the copy of the `channeldata.json` currently in use.

Older copies of the `channeldata.json` MAY be stored as well. If older copies of the `channeldata.json` are stored, they
MUST use an OCI tag that is the UTC time formatted as `YYYYMMDDThhmmssZ`.

### Further Stipulations Related to OCI conda Chennal Repositories and Tags

- If either of the `<OCI-encoded package name>` or the OCI tag for the conda package are hashed, then both MUST be hashed.
- If an OCI registry implementation errors due to length when dealing with the full OCI conda URL for the package, then
  that package cannot be stored in that registry and an error MUST be raised.
- The encoding rules defined above are solely for internal storage of conda packages within an OCI registry. Outside of
  dealing with the OCI registry itself, the original forms of the channel, subdir, label, name, version and build string MUST be used.

### Allowed Blob mediaTypes

We define the following custom media types that MUST be used for the storage of conda repodata, run exports, channel data,
and packages in an OCI registry:

| Blob type                  | Content type                           | mediaType                                             |
|----------------------------|----------------------------------------|-------------------------------------------------------|
| conda package v1           | .tar.bz2 package                       | application/vnd.conda.package.v1                      |
| conda package v2           | .conda package                         | application/vnd.conda.package.v2                      |
| package info               | `info` folder as gzip                  | application/vnd.conda.info.v1.tar+gzip                |
| package index              | `info/index.json` file                 | application/vnd.conda.info.index.v1+json              |
| repodata v1                | v1 repodata JSON                       | application/vnd.conda.repodata.v1+json                |
| repodata v1 gzipped        | v1 repodata JSON w/ gzip comp.         | application/vnd.conda.repodata.v1+json+gzip           |
| repodata v1 bzipped        | v1 repodata JSON as bzip2 comp.        | application/vnd.conda.repodata.v1+json+bz2            |
| repodata v1 zstd           | v1 repodata JSON as zstd comp.         | application/vnd.conda.repodata.v1+json+zst            |
| repodata v2                | v2 repodata JSON                       | application/vnd.conda.repodata.v2+json                |
| repodata v2 gzipped        | v2 repodata JSON w/ gzip comp.         | application/vnd.conda.repodata.v2+json+gzip           |
| repodata v2 bzipped        | v2 repodata JSON as bzip2 comp.        | application/vnd.conda.repodata.v2+json+bz2            |
| repodata v2 zstd           | v2 repodata JSON as zstd comp.         | application/vnd.conda.repodata.v2+json+zst            |
| channeldata                | channeldata JSON                       | application/vnd.conda.channeldata.v1+json             |
| run_exports                | run exports JSON                       | application/vnd.conda.run_exports.v1+json             |
| run_exports gzipped        | run exports JSON w/ gzip comp.         | application/vnd.conda.run_exports.v1+json+gzip        |
| run_exports bzipped        | run exports JSON as bzip2 comp.        | application/vnd.conda.run_exports.v1+json+bz2         |
| run_exports zstd           | run exports JSON as zstd comp.         | application/vnd.conda.run_exports.v1+json+zst         |
| patch instructions         | patch instructions JSON                | application/vnd.conda.patch_instructions.v1+json      |
| patch instructions gzipped | patch instructions JSON w/ gzip comp.  | application/vnd.conda.patch_instructions.v1+json+gzip |
| patch instructions bzipped | patch instructions JSON as bzip2 comp. | application/vnd.conda.patch_instructions.v1+json+bz2  |
| patch instructions zstd    | patch instructions JSON as zstd comp.  | application/vnd.conda.patch_instructions.v1+json+zst  |

### OCI Artifact Structure for Conda Packages

In order to store a conda package as an OCI artifact, we need to define how the data within the conda package is mapped
into the OCI blobs and what additional metadata (if any) is stored in the OCI manifest.

A conda package as an OCI artifact MUST have the following layers:

- a layer holding either the `.tar.bz2` or `.conda` package file with the mediaType
  `application/vnd.conda.package.v1` or `application/vnd.conda.package.v2`, respectively.
- a layer holding the `info` folder as a gzipped tarball with extension `.tar.gz` and mediaType `application/vnd.conda.info.v1.tar+gzip`.
- a layer holding the `info/index.json` file as plain JSON with the mediaType `application/vnd.conda.info.index.v1+json`.

Additional layers are NOT allowed in the OCI artifact. If a conda package exists in both `.tar.bz2` and `.conda` format, the `.conda`
version MUST be chosen to be in the OCI artifact.

The manifest MUST have the following [OCI Annotations][annotations]

- `org.conda.oci.schema` with the value `1` indicating the `v1` specification (defined by this document).
- `org.conda.package.name` with the name of the conda package.
- `org.conda.package.version` with the version of the conda package.
- `org.conda.package.build` with the build string of the conda package

Additional annotations under the `org.conda` namespace are NOT allowed.

### OCI Artifact Structure for Repodata, etc

All artifacts in the following OCI repositories

```text
<OCI conda channel base URL>/<OCI-compatible subdir>/mrepodata.json
<OCI conda channel base URL>/<OCI-compatible subdir>/mcurrent_repodata.json
<OCI conda channel base URL>/<OCI-compatible subdir>/mrepodata_from_packages.json
<OCI conda channel base URL>/<OCI-compatible subdir>/mrun_exports.json
<OCI conda channel base URL>/<OCI-compatible subdir>/mpatch_instructions.json
```

MUST have a layer with the data as JSON and the appropriate mediaType from the table above. Additional layers with
`gzip`, `bz2`, or `zst` compressed copies of the data MAY be included.

The manifest MUST have the following [OCI Annotation][annotations]:

- `org.conda.oci.schema` with the value `1` indicating the `v1` specification (defined by this document).

Additional annotations under the `org.conda` namespace are NOT allowed.

## Rationale

The set of rules defined above ensure that

- Nearly all conda packages can be stored in an OCI registry without hashing. As of 2025-03-10, the maximum lengths across
  `defaults` and `conda-forge` for the various components are ~90 characters, well below the OCI limits.
- Conda packages whose OCI artifact `<name>:<tag>` are not hashed retain human-readability.
- For conda packages whose OCI artifact `<name>:<tag>` are not hashed, the underlying conda package information can be
  decoded from the OCI artifact `<name>:<tag>` without needing to access the OCI registry or consult a lookup table.
- For conda packages whose OCI artifact `<name>:<tag>` are hashed, the underlying conda package information can be extracted
  from the [OCI Annotations][annotations] stored in the OCI manifest.
- Most labels on `anaconda.org` for the `conda-forge` channel can be used as-is, though a few with capital letters or some
  special characters will be excluded.

Some specific choices were made to ease parsing and avoid edge cases:

- The encoding of versions and build strings is purposefully short to avoid excessively increasing the length of OCI tags.
- The individual version and build string for a conda package can be extracted from the OCI `<tag>` by splitting on `-`.
- The `main` label, which is the default label for conda packages in a channel, is not explicitly listed in the OCI `<name>`
  in order to reduce the length of the OCI `<name>` and to reduce clutter.

## Backwards Compatibility

This specification is not fully backwards compatible with the original `v0` proof-of-concept implementation/specification of
conda packages in an OCI registry in the [conda-oci-mirror](https://github.com/channel-mirrors/conda-oci-mirror) project.
See the [Alternatives](#alternatives) section below. The main differences are the construction of the OCI artifact `<name>:<tag>`
from the conda package information and the addition of OCI Annotations to the manifest. However, the OCI blob structure is
unchanged, so cheap conversion may be possible by uploading only new OCI manifests with the new OCI artifact `<name>:<tag>`
and the required OCI Annotations.

The conda channel, subdir, label, and package name regexes are fully backwards compatible with the current conda implementation,
but not all existing packages on `anaconda.org`, `defaults` and `conda-forge` can be put into an OCI conda channel. In particular,
labels that use `:`, more than `.` in a row, more than two `_` in a row, start with a non-alphanumeric character, end with
non-alphanumeric character, use uppercase letters, or use whitespace characters cannot be distributed in an OCI conda registry.
Further, a small percentage of channel names on anaconda.org, ~0.4%, are not compatible with the OCI repository `<name>` regex
(see this [comment](https://github.com/conda/ceps/pull/116#discussion_r1992154574) from [Cheng H. Lee](https://github.com/chenghlee)).
Several alternatives, discussed below, would define encodings that would enable these channels and labels to be distributed.
However, they come at a significant cost in terms of readability and increasing the length of the OCI conda URLs. Thus we
choose to exclude them from the specification.

## Alternatives

- An initial version of this specification was proposed in [CEP PR #70](https://github.com/conda/ceps/pull/70) and received
  substantial feedback from the community. The current version of the specification is a result of that feedback. Particularly
  notable feedback included the suggestion of
  [symbol name mangling techniques and the first version of the shortened encoding used above](https://github.com/conda/ceps/pull/70/files#discussion_r1740438239)
  by [Bas Zalmstra](https://github.com/baszalmstra).
- The [channel-mirrors project](https://github.com/channel-mirrors) with its associated package
  [conda-oci-mirror](https://github.com/channel-mirrors/conda-oci-mirror) developed a proof-of-concept implementation of
  conda packages and repodata stored in an OCI registry. This specification is based on the experience gained from that project, but is not
  fully backwards compatible with the original implementation. See the [Backwards Compatibility](#backwards-compatibility) section above.
  This original implementation and implied specification is referred to as `v0`.
- One alternative to excluding certain labels and channels from distribution via an OCI conda channel is to define a further custom
  encoding of the channel path parts of the URL. For example, one could use an encoding inspired by percent-encoding for URLs. This encoding
  could, for example, first percent-encode the letter `u` and all characters not in the set `[0-9a-z]`. Then the percent sign could be replaced
  by the special code `u_`. This encoding would significantly hinder readability, but would allow nearly arbitrary channel names and labels to be used.
- Another alternative which also suffers from readability issues, is to encode all channel and label names to bytes via say UTF-8
  and then represent them as hex strings. This would allow arbitrary channel names and labels to be used as well, but would also
  lengthen channel names towards the OCI limits.

## Sample Implementation

### conda-oci

The [conda-oci](https://github.com/conda-incubator/conda-oci) repository has reference implementations of the procedures defined above
for computing the OCI artifact `<name>:<tag>` and for converting conda artifacts, repodata, etc. into an OCI artifact with a manifest and layers/blobs.

### mamba & rattler

Both [mamba](https://github.com/mamba-org/mamba) and [rattler](https://github.com/conda/rattler) can be used with OCI registries of
conda packages conforming to the `v0` specification.

## References

- Open Containers Initiative: <https://opencontainers.org/>
- CEP 16: <https://github.com/conda/ceps/blob/main/cep-0016.md>
- RFC 2119: <https://datatracker.ietf.org/doc/html/rfc2119>
- OCI Distribution Spec: <https://github.com/opencontainers/distribution-spec>
- OCI Image Spec: <https://github.com/opencontainers/image-spec>
- OCI Annotations: <https://github.com/opencontainers/image-spec/blob/main/annotations.md#annotations>
- RFC 3986: <https://datatracker.ietf.org/doc/html/rfc3986#section-3.2>
- channel-mirrors project: <https://github.com/channel-mirrors>
- conda-oci-mirror project: <https://github.com/channel-mirrors/conda-oci-mirror>
- mamba project: <https://github.com/mamba-org/mamba>
- rattler project: <https://github.com/conda/rattler>
- conda-oci project: <https://github.com/conda-incubator/conda-oci>

[oci]: https://opencontainers.org/ (Open Containers Initiative)
[cep16]: https://github.com/conda/ceps/blob/main/cep-0016.md (CEP 16)
[RFC2119]: https://datatracker.ietf.org/doc/html/rfc2119 (RFC 2119)
[ocidist]: https://github.com/opencontainers/distribution-spec (OCI Distribution Spec)
[ociimage]: https://github.com/opencontainers/image-spec (OCI Image Spec)
[rfc3986]: https://datatracker.ietf.org/doc/html/rfc3986#section-3.2 (RFC 3986)
[annotations]: https://github.com/opencontainers/image-spec/blob/main/annotations.md#annotations (OCI Annotations)

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
