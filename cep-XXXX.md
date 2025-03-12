# CEP XXXX - OCI Storage of conda Artifacts

<table>
<tr><td> Title </td><td> OCI Storage of conda Artifacts </td>
<tr><td> Status </td><td> Proposed </td></tr>
<tr><td> Author(s) </td><td> Wolf Vollprecht &lt;wolf@prefix.dev&gt;<br /> Hind Montassif &lt;hind.montassif@quantstack.net&gt;<br /> Matthew R. Becker &lt;becker.mr@gmail.com&gt;<br /> Jaime Rodríguez-Guerra &lt;jaime.rogue@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> April 12, 2024</td></tr>
<tr><td> Updated </td><td> March 10, 2025</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/115; https://github.com/conda/ceps/pull/70 </td></tr>
<tr><td> Implementation </td><td>  </td></tr>
</table>

## Abstract

This CEP defines how to store conda packages in an *OCI registry* as *OCI artifacts* (see the [Open Containers Initiative](https://opencontainers.org/) for more details on these terms). Importantly, this CEP does NOT describe how to store conda repodata in an OCI registry or how to generate repodata from an OCI registry. We leave these topics for future CEPs.

## Specification

The conda OCI package specification has three main parts. First, we define how the data in a conda package is stored as an OCI artifact. Second, we codify the allowed characters and format of conda channels, subdirs, labels, and package names for packages that can be stored in an OCI registry. Finally, we define how to generate the container `<name>` and container image `<tag>` (i.e., `<name>:<tag>`) for a conda package in an OCI registry.

Below we use the following terms, some of which are defined by the OCI specs and others of which are specific to conda.

OCI-defined terms:

- *OCI registry*: A service that implements the OCI Distribution Spec (e.g., `ghcr.io`).
- *OCI repository*: A collection of OCI artifacts with the same container or image `<name>` in an OCI registry.
- *OCI tag*: A label for a specific container image within an OCI repository, identified by its `<tag>`.
- *OCI artifact*: A container image stored in an OCI registry, specified by its OCI repository `<name>:<tag>`. Internally, an artifact consists of an OCI manifest and a set of OCI blobs (layers) that hold the artifact's data.
- *OCI blob*: A binary blob stored in an OCI registry identified by its mediaType, digest, and size.
- *OCI manifest*: A JSON document that describes the contents of an OCI artifact, organized as some metadata and a number of blobs. The manifest is also stored in the registry as a blob.

Conda-specific terms:

- *OCI-encoded package name*: The name of a conda package that is encoded to a specific format (defined below) for use in an OCI repository `<name>`. The language "encoded to OCI-form" is used below to refer to this process.
- *OCI-encoded label/version/build string*: A conda package label, version, or build string that is encoded to a specific format (defined below) for use in an OCI image `<tag>`. The language "encoded to OCI-form" is used below to refer to this process.
- *hashed OCI-encoded `<item>`*: An `<item>` that is first encoded to its OCI-form and then hashed to a specific format (defined below) for use in an OCI repository `<name>` and/or `<tag>`.

For further details on the OCI-defined terms, see the full OCI specifications, the [Image Spec](https://github.com/opencontainers/image-spec) and the [Distribution Spec](https://github.com/opencontainers/distribution-spec).

This specification is labeled `v1` and uses only OCI specifications compatible with the OCI `v1` specification.

### Conda Packages as OCI Artifacts

In order to store a conda package as an OCI artifact, we need to define how the data within the conda package is mapped into the OCI blobs, the allowed blob mediaTypes, and what additional metadata (if any) is stored in the OCI manifest.

#### Conda OCI Artifact Blob/Layer Media Types

We define the following custom media types that MUST be used for the storage of conda packages in an OCI registry.

| Blob type        | Content type           | mediaType                                   |
|------------------|------------------------|---------------------------------------------|
| conda package v1 | .tar.bz2 package       | application/vnd.conda.package.v1            |
| conda package v2 | .conda package         | application/vnd.conda.package.v2            |
| package info     | `info` folder as gzip  | application/vnd.conda.info.v1.tar+gzip      |
| package index    | `info/index.json` file | application/vnd.conda.info.index.v1+json    |

#### Conda OCI Artifact Blob/Layer Structure

A valid conda package as an OCI artifact MUST have the following layers:

- a layer holding either the `.tar.bz2` or `.conda` package file with the mediaType `application/vnd.conda.package.v1` or `application/vnd.conda.package.v2`, respectively.
- a layer holding the `info` folder as a gzipped tarball with extension `.tar.gz` and mediaType `application/vnd.conda.info.v1.tar+gzip`.
- a layer holding the `info/index.json` file as plain JSON with the mediaType `application/vnd.conda.info.index.v1+json`.

Additional layers are NOT allowed in the OCI artifact. If a conda package exists in both `.tar.bz2` and `.conda` format, the `.conda` version MUST be chosen to be in the OCI artifact.

#### Conda Manifest Annotations

The manifest MUST have the following [Annotations](https://github.com/opencontainers/image-spec/blob/main/annotations.md#annotations):

- `org.conda.oci.schema` with the value `1` indicating the `v1` specification (defined by this document).
- `org.conda.package.name` with the name of the conda package.
- `org.conda.package.version` with the version of the conda package.
- `org.conda.package.build` with the build string of the conda package

Additional annotations under the `org.conda` namespace are NOT allowed.

### Allowed Characters and Formats for conda Channels, Subdirs, Labels, and Package Names

The follow regexes define valid conda channel names, labels, and conda package names for conda packages that can be stored in an OCI registry.

- channel: `^[a-z0-9]+((-|_|.)[a-z0-9]+)*$`
- subdirs: `^[a-z0-9]+((-|_|.)[a-z0-9]+)*$`
- label: `^[a-zA-Z][0-9a-zA-Z_\-\.\/:\s]*`
- package name: `^(([a-z0-9])|([a-z0-9_](?!_)))[._-]?([a-z0-9]+(\.|-|_|$))*$`

All channels, subdirs, labels, and package names MUST conform to their respective regex in the list above if the package is to be stored in an OCI registry.

Further, the following rule applies to labels:

- The label `NOLABEL` is reserved and MUST only be used for conda packages which have no other labels. In other words, in the space of labels, the empty set is represented by the label `NOLABEL`.

### Mapping conda Packages with Channels, Subdirs, Labels to OCI Repositories and Tags

Per the [OCI Distribution Spec](https://github.com/opencontainers/distribution-spec) v1, the `<name>` and `<tag>` of an OCI repository are subject to the following regexes:

- `<name>`: `^[a-z0-9]+((\.|_|__|-+)[a-z0-9]+)*(\/[a-z0-9]+((\.|_|__|-+)[a-z0-9]+)*)*$`
- `<tag>`: `^[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}$`

The [OCI Distribution Spec](https://github.com/opencontainers/distribution-spec) further notes that "Many clients impose a limit of 255 characters on the length of the concatenation of the registry hostname (and optional port), /, and <name> value."

These constraints motivate the following set of rules for mapping conda packages to OCI repositories and tags. More explanation is given below in the Rationale section and the example implementation illustrates how these rules work together to create a human-readable and easily parsable OCI repository `<name>` and `<tag>` for a conda package.

#### Overall Form of the OCI Repository and Tag

A conda package with its channel, subdir, and (optional) label MUST be mapped to an OCI `<repository>:<tag>` in one of two forms.

The unhashed form of the OCI artifact `<name>:<tag>` for a conda package is:

```
<channel>/<subdir>/<OCI-encoded package name>:<OCI-encoded version>-<OCI-encoded build>(-<OCI-encoded label>)
```

where the `-<OCI-encoded label>` component MUST be present if the package label is not `main`.

In the hashed form, the OCI-form of the package name and the OCI tag (i.e., `<OCI-encoded version>-<OCI-encoded build>(-<OCI-encoded label>)`) are each separately hashed via SHA1 and then replaced by the string `h<hexdigest of SHA1 hash>` as follows:

```
<channel>/<subdir>/h<hexdigest of the SHA1 hash of OCI-encoded package name>:h<hexdigest of the SHA1 hash of the original OCI tag of the conda package>
```

The `<channel>` and `<subdir>` MUST be used as-is without modification. The OCI-forms of the package name, label, version, and build string are defined below.

#### Encoding Package Names, Channels, and Subdirs into OCI Repository `<name>`s

The package name MUST be encoded to OCI-form using the following rules

- All package names MUST be prepended by the character `c`.
- If the combined string `<channel>/<subdir>/<OCI-encoded package name>` exceeds 128 characters in length, the OCI-encoded package name MUST be replaced by the SHA1 hash of the OCI-encoded package name in hexadecimal form as `h<SHA1 in hexadecimal>`. The letter `h` is reserved to indicate a hashed OCI-encoded package name.

Package names in OCI-form which are not hashed can be decoded by reversing the encoding rules above.

For example, the package name `_libgcc_mutex` is encoded to OCI-form as `c_libgcc_mutex`, and the package name `c_libgcc_mutex` is encoded to OCI-form as `cc_zlibgcc_mutex`. A very long package name like `gblah000...000` would be encoded to its OCI-form `cgblah000...000`, then hashed via SHA1, yielding something like `h<hexdigest of SHA1 hash>`.

The channel and subdir MUST be used as-is without modification.

The channel, subdir and OCI-encoded package name (or hashed OCI-encoded package name if required) MUST be combined with `/` to form the OCI repository `<name>`

```
<channel>/<subdir>/<OCI-encoded package name or its SHA1 hash in hexadecimal>
```

#### Encoding Labels, Versions and Build Strings into OCI `<tag>`s

The label, version, and build string are encoded to OCI-form as follows. First the following mapping rules MUST be applied to the label, version and build string in the order listed below:

- `_` -> `_U`
- `-` -> `_D`
- `+` -> `_P`
- `!` -> `_N`
- `=` -> `_E`
- `:` -> `_C`
- `/` -> `_S`
- ` ` -> `_B`
- `\t` -> `_T`
- `\r` -> `_R`
- `\n` -> `_L`

This encoding is undone by applying the rules in reverse, starting at the bottom of the list and moving to the top. Depending on the context, some labels may be percent-encoded for use in URLs. The percent-encoding MUST be undone before the label is encoded via the list of rules above.

After encoding each component to OCI-form, the version, build string, and label (if present, see below) MUST be combined with a `-` to form the OCI `<tag>`

```
<OCI-encoded version>-<OCI-encoded build>(-<OCI-encoded label>)
```

where the `-<OCI-encoded label>` component is present is the package label is not `main`.

As implied above, if no label is explicitly specified for a package, then package is by definition on the `main` label. This stipulation means the following two OCI tags for conda packages are equivalent:

```
v1.0.0-h123456_U0-main
v1.0.0-h123456_U0
```

Finally, if the entire OCI tag exceeds 128 characters in length, the entire tag MUST be hashed with the SHA1 algorithm and the resulting OCI tag is then `h<SHA1 in hexadecimal>`.

#### Further Odds and Ends

- If either the OCI-encoded form of package name or the OCI tag for the conda package are hashed, then both MUST be hashed. In other words, only the two forms of the OCI artifact `<name>:<tag>` combination defined above, either unhashed or hashed, are allowed.
- Once the OCI repository `<name>` and `<tag>` are computed for the conda artifact, the rest of the OCI Distribution Spec MUST be followed.
- If an OCI registry implementation errors due to length when dealing with the full OCI form of the conda package (e.g., the combination of the registry URL and full OCI repository `<name>` for the conda package exceed some internal limit in the implementation), then that package cannot be stored in that registry and an error MUST be raised.
- The repodata download URL for a conda package in an OCI registry MUST use the `oci://` scheme to indicate that the artifact will be downloaded from an OCI endpoint. More specifically, it MUST follow the syntax `oci://<authority>[:<port>]/<name>:<tag>`. The `<authority>` is the URI of the OCI registry (e.g., `ghcr.io`).
- The encoding rules defined above are solely for internal storage of conda packages within an OCI registry. Outside of dealing with the OCI registry itself, the original forms of the channel, subdir, label, name, version and build string MUST be used.

## Rationale

The set of rules defined above ensure that

- Nearly all conda packages can be stored in an OCI registry without hashing. As of 2025-03-10, the maximum lengths across `defaults` and `conda-forge` for the various components are ~90 characters, well below the OCI limits.
- Conda packages whose OCI artifact `<name>:<tag>` are not hashed retain human-readability.
- For conda packages whose OCI artifact `<name>:<tag>` are not hashed, the underlying conda package information can be decoded from the OCI artifact `<name>:<tag>` without needing to access the OCI registry or consult a lookup table.
- For conda packages whose OCI artifact `<name>:<tag>` are hashed, the underlying conda package information can be extracted from the OCI Annotations stored in the OCI manifest.
- All labels on `anaconda.org` can be used as-is.
- Relabeling a conda package in an OCI registry is a cheap operation since it involves retagging an existing image.

Some specific choices were made to ease parsing and avoid edge cases:

- The encoding of labels, versions, and build strings is purposefully short to avoid excessively increasing the length of OCI tags.
- The individual version, build string, and label for a conda package can be extracted from the OCI `<tag>` by splitting on `-`.
- The `main` label, which is the default label for conda packages in a channel, is not explicitly listed in the OCI `<tag>` in order to reduce the length of the OCI `<tag>` and to reduce clutter.

## Backwards Compatibility

This specification is not fully backwards compatible with the original `v0` proof-of-concept implementation/specification of conda packages in an OCI registry in the [conda-oci-mirror](https://github.com/channel-mirrors/conda-oci-mirror) project. See the Alternatives section below. The main differences are the construction of the OCI artifact `<name>:<tag>` from the conda package information and the addition of OCI Annotations to the manifest. However, the OCI blob structure is unchanged, so cheap conversion may be possible by uploading only new OCI manifests with the new OCI artifact `<name>:<tag>` and the required OCI Annotations.

The conda channel, subdir, label, and package name regexes are backwards compatible with the current conda implementation and all existing packages on the `defaults` and `conda-forge` channels, except the `__anaconda_core_depends` package on the `defaults` channel. As of 2025-03-10 the label `NOLABEL` is not in use anywhere on anaconda.org. The regex for labels above was pulled from an anaconda.org error message describing the set of valid labels. Finally, anaconda.org usernames/channel names are case insensitive and cannot begin with an underscore.

## Alternatives

- An initial version of this specification was proposed in [CEP PR #70](https://github.com/conda/ceps/pull/70) and received substantial feedback from the community. The current version of the specification is a result of that feedback. Particularly notable feedback included the suggestion of [symbol name mangling techniques and the first version of the shortened encoding used above](https://github.com/conda/ceps/pull/70/files#discussion_r1740438239) by [Bas Zalmstra](https://github.com/baszalmstra).

- The [channel-mirrors project](https://github.com/channel-mirrors) with its associated package [conda-oci-mirror](https://github.com/channel-mirrors/conda-oci-mirror) developed a proof-of-concept implementation of conda packages and repodata stored in an OCI registry. This specification is based on the experience gained from that project, but is not fully backwards compatible with the original implementation. See Backwards Compatibility above. This original implementation and implied specification is referred to as `v0`.

## Sample Implementation

### conda-oci

The [conda-oci](https://github.com/conda-incubator/conda-oci) repository has reference implementations of the procedures defined above for computing the OCI artifact `<name>:<tag>` and for converting a conda artifact into an OCI artifact with a manifest and layers/blobs.

### mamba & rattler

Both [mamba](https://github.com/mamba-org/mamba) and [rattler](https://github.com/conda/rattler) can be used with OCI registries of conda packages conforming to the `v0` specification.

## References

- OCI Distribution Spec v1: https://github.com/opencontainers/distribution-spec/blob/v1.1.1/spec.md
- OCI Image Spec v1: https://github.com/opencontainers/image-spec/blob/v1.1.1/spec.md
- channel-mirrors project: https://github.com/channel-mirrors
- conda-oci-mirror project: https://github.com/channel-mirrors/conda-oci-mirror
- mamba project: https://github.com/mamba-org/mamba
- rattler project: https://github.com/conda/rattler
- conda-oci project: https://github.com/conda-incubator/conda-oci

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
