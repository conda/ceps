# CEP XYZZ - OCI Storage of Conda Artifacts

<table>
<tr><td> Title </td><td> OCI Storage of Conda Artifacts </td>
<tr><td> Status </td><td> Proposed </td></tr>
<tr><td> Author(s) </td><td> Wolf Vollprecht &lt;wolf@prefix.dev&gt;<br> Hind Montassif &lt;hind.montassif@quantstack.net&gt;<br> Matthew R. Becker &lt;becker.mr@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> April 12, 2024</td></tr>
<tr><td> Updated </td><td> March 10, 2025</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/OCI </td></tr>
<tr><td> Implementation </td><td>  </td></tr>
</table>

## Abstract

This CEP defines how to store conda packages in an *OCI registry* as *OCI artifacts* (see the [Open Containers Initiative](https://opencontainers.org/) for more details on these terms). Importantly, this CEP does NOT describe how to store conda repodata in an OCI registry or how to generate repodata from an OCI registry. We leave these topics for future CEPs.

## Specification

The conda OCI package specification has three main parts. First, we define how the data in a conda package is stored as an OCI artifact. Second, we codify the allowed characters and format of conda channels, subdirs, labels, and package names. Finally, we define how to generate the container `<name>` and container image `<tag>` (i.e., `<name>:<tag>`) for a conda package in an OCI registry.

Below we use the following terms, some of which are defined by the OCI specs and others of which are specific to conda.

OCI-define terms:

- *OCI registry*: A service that implements the OCI Distribution Spec (e.g., `ghcr.io`).
- *OCI repository*: A collection of container images with the same repository `<name>` in an OCI registry.
- *OCI tag*: A label for a specific container image within an OCI repository, identified by its `<tag>`.
- *OCI artifact*: A container image stored in an OCI registry, specified by its OCI repository `<name>:<tag>`. Internally, an artifact consists of an OCI manifest and a set of OCI blobs (layers) that hold the artifact's data.
- *OCI blob*: A binary blob stored in an OCI registry identified by its mediaType, digest, and size.
- *OCI manifest*: A JSON document that describes the contents of an OCI artifact, organized as some metadata and a number of blobs. The manifest is also stored in the registry as a blob.

Conda-specific terms:

- *OCI-encoded package name*: The name of a conda package that is encoded to a specific format (defined below) for use in an OCI repository `<name>`. The language "encoded to OCI-form" is used below to refer to this process.
- *OCI-encoded label/version/build string*: A conda package label, version, or build string that is encoded to a specific format (defined below) for use in an OCI image `<tag>`. The language "encoded to OCI-form" is used below to refer to this process.
- *hashed OCI-encoded <item>*: An `<item>` that is first encoded to its OCI-form and then hashed to a specific format (defined below) for use in an OCI repository `<name>` and/or `<tag>`.

For further details on the OCI-defined terms, see the full OCI specifications, the [Image Spec](https://github.com/opencontainers/image-spec) and the [Distribution Spec](https://github.com/opencontainers/distribution-spec).

This specification is labeled `v1` and uses only `v1.0` of the OCI specification.

### conda Packages as OCI Artifacts

In order to store a conda package as an OCI artifact, we need to define how the data within the conda package is mapped into the OCI blobs, the allowed blob mediaTypes, and what additional metadata (if any) is stored in the OCI manifest.

#### conda OIC Artifact Blob/Layer Media Types

We define the following custom media types that MUST be used for the storage of conda packages in an OCI registry.

| Blob type        | Content type              | mediaType                                   |
|------------------|---------------------------|---------------------------------------------|
| conda package v1 | .tar.bz2 package          | application/vnd.conda.package.v1            |
| conda package v2 | .conda package            | application/vnd.conda.package.v2            |
| package info     | `info` folder as gzip     | application/vnd.conda.info.v1.tar+gzip      |
| package index    | `index.json` file         | application/vnd.conda.info.index.v1+json    |

#### conda OCI Artifact Blob/Layer Structure

A valid conda package as an OCI artifact MUST have the following layers:

- a layer holding either the `.tar.bz2` or `.conda` package file with the mediaType `application/vnd.conda.package.v1` or `application/vnd.conda.package.v2`, respectively.
- a layer holding the `info` folder as a gzipped tarball with extension `.tar.gz` and mediaType `application/vnd.conda.info.v1.tar+gzip`.
- a layer holding the `index.json` file as plain JSON with the mediaType `application/vnd.conda.info.index.v1+json`.

Additional layers are NOT allowed in the OCI artifact.

#### conda Manifest Annotations

The manifest MUST have the following [Annotations](https://github.com/opencontainers/image-spec/blob/main/annotations.md#annotations):

- `org.conda.oci.schema` with the value `1` indicating the `v1` specification (defined by this document).
- `org.conda.package.name` with the name of the conda package.
- `org.conda.package.version` with the version of the conda package.
- `org.conda.package.build` with the build string of the conda package

Additional annotations are NOT allowed.

### Allowed Characters and Formats for conda Channels, Subdirs, Labels, and Package Names

The follow regexes define valid conda channel names, labels, and conda package names:

| Type         | Regex                                                         |
|--------------|---------------------------------------------------------------|
| channel      | `^[a-z0-9]+((-|_|.)[a-z0-9]+)*$`                              |
| subdirs      | `^[a-z0-9]+((-|_|.)[a-z0-9]+)*$`                              |
| label        | `^[a-zA-Z][0-9a-zA-Z_\-\.\/:\s]*`                             |
| package name | `^(([a-z0-9])|([a-z0-9_](?!_)))[._-]?([a-z0-9]+(\.|-|_|$))*$` |

All channels, subdirs, labels, and package names MUST conform to their respective regex in the table above.

Further, the following rule applies to labels:

- The label `NOLABEL` is reserved and MUST only be used for conda packages which have no other labels. In other words, in the space of labels, the empty set is represented by the label `NOLABEL`.

> [!NOTE]
> As 2025-03-10, only a single package name on the `defaults` channel violates the above regex (`__anaconda_core_depends`).
> Further, on all of `anaconda.org`, the `NOLABEL` label is not in use.

### Mapping conda Packages with Channels, Subdirs, Labels to OCI Repositories and Tags

Per the [OCI Distribution Spec](https://github.com/opencontainers/distribution-spec) v1.0, the `<name>` and `<tag>` of an OCI repository are subject to the following regexes:

- `<name>`: `^[a-z0-9]+((\.|_|__|-+)[a-z0-9]+)*(\/[a-z0-9]+((\.|_|__|-+)[a-z0-9]+)*)*$`
- `<tag>`: `^[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}$`

The [OCI Distribution Spec](https://github.com/opencontainers/distribution-spec) further notes that "Many clients impose a limit of 255 characters on the length of the concatenation of the registry hostname (and optional port), /, and <name> value."

These constraints motivate the following set of rules for mapping conda packages to OCI repositories and tags. More explanation is given below in the Rational section and the example implementation illustrate how these rules work together to create a human-readable and easily parsable OCI repository `<name>` and `<tag>` for a conda package.

#### Overall Form of the OCI Repository and Tag

A conda package with its channel, subdir, and (optional) label MUST be mapped to an OCI `<repository>:<tag>` in one of two forms.

The unhashed form of the OCI repository and tag for a conda package is:

```
<channel>/<subdir>/<OCI-encoded package name>:<OCI-encoded version, build and (optional) label in the form '<version>-<build>(-<label>)'>
```

In the hashed form, the OCI-form of the package name and the string composed of the OCI-forms of the version, build, and (optional) label (i.e., `<version>-<build>(-<label>)`) are each separately hashed via SHA1 and then replaced by the string `h<hexdigest of SHA1 hash>` as follows

```
<channel>/<subdir>/h<hexdigest of the SHA1 hash of OCI-encoded package name>:h<hexdigest of the SHA1 hash of the original OCI tag of the conda package>
```

The `<channel>` and `<subdir>` MUST be used as-is without modification. The OCI-forms of the package name, label, version, and build string are defined below.

#### Encoded Package Names, Channels, and Subdirs into OCI Repository `<name>`s

The package name MUST be encoded to OCI-form as follows:

- If the package name starts with an `_`, the `_` MUST be replaced with `z`.
- Otherwise, if the package name does NOT start with an `_`, the package name MUST be prepended by `c`.
- If the combined string `<channel>/<subdir>/<OCI-encoded package name>` exceeds 128 characters in length, the OCI-encoded package name MUST be replaced by the SHA1 hash of the OCI-encoded package name in hexadecimal form as `h<SHA1 in hexidecimal>`.

Package names in OCI-form which are not hashed can be decoded by reversing the encoding rules above.

For example, the package name `_libgcc_mutex` is encoded to OCI-form as `zlibgcc_mutex`, and the package name `zlibgcc_mutex` is encoded to OCI-form as `czlibgcc_mutex`. A very long package name like `gblah000...000` would be encoded to its OCI-form `cgblah000...000`, then hashed via SHA1, yielding something like `h<hexdigest of SHA1 hash>`.

The channel and subdir MUST be used as-is without modification.

The channel, subdir and OCI-encoded package name (or hashed OCI-encoded package name if required) MUST be combined with `/` to form the OCI repository `<name>`

```
<channel>/<subdir>/<OCI-encoded package name>
```

#### Encoding Labels, Versions and Build Strings into OCI `<tag>`s

The label, version, and build string are encoded to OCI-form as follows. First the following mapping rules MUST be applied to the label, version and build string in the order listed below:

- `_` -> `__`
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

This encoding can be undone by applying the rules in reverse, starting at the bottom of the list and moving to the top. Depending on the context, some labels may be percent-encoded for use in URLs. The percent-encoding MUST be undone before the label is encoded via the list of rules above.

After encoding each component to OCI-form, the version, build string, and (optional) label MUST be combined with a `-` to form the OCI `<tag>` as either

```
<version>-<build>-<label>
```

or if the label is not specified (i.e. the package is on the `main` label), then

```
<version>-<build>
```

with no trailing `-`.

As implied above, if no label is explicitly specified for a package, then package is by definition on the `main` label. This stipulation means the following two OCI tags for conda packages are equivalent:

```
v1.0.0-h123456__0-main
v1.0.0-h123456__0
```

Finally, if the entire OCI tag exceeds 128 characters in length, the entire tag MUST be hashed with the SHA1 algorithm and the resulting OCI tag is then `h<SHA1 in hexidecimal>`.

#### Further Odds and Ends

- If either the OCI-encoded form of package name or the OCI tag for the conda package are hashed, then both MUST be hashed. In other words, only the two forms of the OCI artifact `<name>:<tag>` combination defined above, either unhashed or hashed, are allowed.
- Once the OCI repository `<name>` and `<tag>` are computed for the conda artifact, the rest of the OCI Distribution Spec MUST be followed.
- If an OCI registry implementation errors due to length when dealing with the full OCI form of the conda package (e.g., the combination of the registry URL and full OCI repository `<name>` for the conda package exceed some internal limit in the implementation), then that package cannot be stored in that registry and an error MUST be raised.
- Within conda repodata, the download URL for a conda package in an OCI registry MUST always be prepended by `oci://` to indicate that the download URL is an OCI URL. The registry being used, any required ports etc. are prepended to the conda package OCI repository `<name>:<tag>` to form the full download URL per the OCI v1.0 specification.
- The encoding rules defined above are solely for internal storage of conda packages within an OCI registry. Outside of dealing with the OCI registry itself, the original forms of the channel, subdir, label, name, version and build string MUST be used.

## Rationale

The set of rules defined above ensure that

- Nearly all conda packages can be stored in an OCI registry without hashing. As of 2025-03-10, the maximum lengths across `defaults` and `conda-forge` for the various components are ~80 characters, well below the OCI limits.
- conda packages whose OCI artifact `<name>:<tag>` are not hashed retain human-readability.
- For conda packages whose OCI artifact `<name>:<tag>` are not hashed, the underlying conda package information can be decoded from the OCI artifact `<name>:<tag>` without needing to access the OCI registry or consult a lookup table.
- For conda packages whose OCI artifact `<name>:<tag>` are hashed, the underlying conda package information can be extracted from the OCI Annotations stored in the OCI manifest.
- Nearly all labels on `anaconda.org` can be used as-is. As of 2025-03-10 the label `NOLABEL` is not in use anywhere on anaconda.org.
- Relabeling a conda package in an OCI registry is a cheap operation since it involves retagging an existing image.

Some specific choices were made to ease parsing and avoid edge cases:

- The encoding of labels, versions, and build strings is purposefully short to avoid excessively increasing the length of OCI tags.
- The encoding of labels, versions, and build strings only generates at most two `_`s in a row and so obeys the OCI spec.
- The individual version, build string, and label for a conda package can be extracted from the OCI `<tag>` by splitting on `-`.
- The `main` label, which is the default label for conda packages in a channel, is not explicitly listed in the OCI `<tag>` in order to reduce the length of the OCI `<tag>` and to reduce clutter.

## Backwards Compatibility

This specification is not fully backwards compatible with the original `v0` proof-of-concept implementation/specification of conda packages in an OCI registry in the [conda-oci-mirror](https://github.com/channel-mirrors/conda-oci-mirror) project. See the Alternatives section below. The main differences are the construction of the OCI artifact `<name>:<tag>` from the conda package information and the addition of OCI Annotations to the manifest. However, the OCI blob structure is unchanged, so cheap conversion may be possible by uploading only new OCI manifests with the new OCI artifact `<name>:<tag>` and the required OCI Annotations.

## Alternatives

- An initial version of this specification was proposed in [CEP PR #70](https://github.com/conda/ceps/pull/70) and received substantial feedback from the community. The current version of the specification is a result of that feedback. Particularly notable feedback included the suggestion of [symbol name mangling techniques and the first version of the shortened encoding used above](https://github.com/conda/ceps/pull/70/files#discussion_r1740438239) by [Bas Zalmstra](https://github.com/baszalmstra).

- The [channel-mirrors project](https://github.com/channel-mirrors) with its associated package [conda-oci-mirror](https://github.com/channel-mirrors/conda-oci-mirror) developed a proof-of-concept implementation of conda packages and repodata stored in an OCI registry. This specification is based on the experience gained from that project, but is not fully backwards compatible with the original implementation. See Backwards Compatibility above. This original implementation and implied specification is referred to as `v0`.

## Sample Implementation

### conda-oci

The [conda-oci](https://github.com/conda-incubator/conda-oci) repository has reference implementations of the procedures defined above for computing the OCI artifact `<name>:<tag>` and for converting a conda artifact into an OCI artifact with a manifest and layers/blobs.

### mamba & rattler

Both [mamba](https://github.com/mamba-org/mamba) and [rattler](https://github.com/conda/rattler) can be used with OCI registries of conda packages conforming to the `v0` specification.
