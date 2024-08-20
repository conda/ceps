<table>
<tr><td> Title </td><td> OCI registries as conda channels </td>
<tr><td> Status </td><td> Proposed </td></tr>
<tr><td> Author(s) </td><td> Wolf Vollprecht &lt;wolf@prefix.dev&gt;<br> Hind Montassif &lt;hind.montassif@quantstack.net&gt;</td></tr>
<tr><td> Created </td><td> April 12, 2024</td></tr>
<tr><td> Updated </td><td> August 7, 2024</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/70 </td></tr>
<tr><td> Implementation </td><td>  </td></tr>
</table>

# Abstract

We want to use OCI registries as a storage for conda packages. This CEP specifies how we lay out conda packages on an OCI registry.

## Specification

An OCI artifact consists of a manifest and a set of blobs. The manifest is a JSON document that describes the contents of the artifact. The blobs are the actual data that the manifest refers to. The manifest is stored in the registry as a blob, and the blobs are stored in the registry as blobs.

The manifest consists of some metadata and a number of "layers". Each layer is a reference to a blob.

Layers can have arbitrary names and mediaTypes.

An OCI manifest is referenced by a name and a tag.

For further details, please refer to the official [OCI Distribution spec](https://github.com/opencontainers/distribution-spec/blob/v1.0/spec.md#definitions).

### Layers

Each layer must be a [descriptor](https://github.com/opencontainers/image-spec/blob/main/descriptor.md#properties) containing at least the 3 required fields:

- The `mediaType` of the referenced content.
- The `digest` of the targeted content.
- The `size` of the raw content (in bytes).

### MediaTypes

Global and already defined mediaTypes are described [here](https://github.com/opencontainers/image-spec/blob/main/media-types.md#oci-image-media-types).

Custom mediaTypes defined for the conda channels use case are as follows:

| Blob type        | Content type              | mediaType                                   |
|------------------|---------------------------|---------------------------------------------|
| conda package    | .tar.bz2 package          | application/vnd.conda.package.v1            |
| conda package    | .conda package            | application/vnd.conda.package.v2            |
| package info     | `info` folder as gzip     | application/vnd.conda.info.v1.tar+gzip      |
| package info     | `index.json` file         | application/vnd.conda.info.index.v1+json    |
| repodata         | `repodata.json` file      | application/vnd.conda.repodata.v1+json      |
| repodata         | `repodata.json.zst` file  | application/vnd.conda.repodata.v1+json+zst  |
| repodata         | `repodata.json.gz` file   | application/vnd.conda.repodata.v1+json+gzip |
| repodata         | `repodata.json.bz2` file  | application/vnd.conda.repodata.v1+json+bz2  |

If needed, more mediaTypes could be specified (i.e `application/vnd.conda.info.v1.tar+zst`).

Using the `mediaType` field in the manifest, we can find the layer + SHA256 hash to pull the corresponding blob.
Each `mediaType` should only be present in one layer.

## Repodata on OCI registries

The `repodata.json` file is a JSON file that contains metadata about the packages in a channel.
It is used by conda to find packages in a channel.

On an OCI registry it should be stored under `<channel>/<subdir>/repodata.json`.
The repodata file should have one entry that has the `latest` tag. This entry should point to the latest version of the repodata.
All versions of the repodata should also be tagged with a UTC timestamp of the following format: `YYYY.MM.DD.HH.MM.SS`, e.g. `2024.04.12.07.06.32`.

The mediaType for the raw `repodata.json` file is `application/vnd.conda.repodata.v1+json`. However, for large repositories it's advised to store the `zstd` encoded repodata file with the mediaType `application/vnd.conda.repodata.v1+json+zst` as an additional layer in `<channel>/<subdir>/repodata.json`. ([ref](https://github.com/opencontainers/image-spec/blob/main/layer.md#gzip-media-types))

Other encodings are also accepted:

- `application/vnd.conda.repodata.v1+json+gzip`
- `application/vnd.conda.repodata.v1+json+bz2`

### Conda package artifacts on an OCI registry

The manifest for a conda package on an OCI registry should look like follows.

It should have a name and a tag. The name is `<channel>/<subdir>/<package-name>`.
The tag is the version and build string of the packages, using a `-` as a separator.

For example, a package like `xtensor-0.10.4-h431234.conda` would map to a OCI registry `conda-forge/linux-64/xtensor:0.10.4-h431234`.

A conda package, in an OCI registry, should ship up to 3 layers:

- The package data itself, as a tarball. (mandatory)
  - This can be either a `.tar.bz2` (v1) or a `.conda` (v2) file, or both as separate layers.
- The package `info` folder as a gzipped "tar.gz" file.
- The package `info/index.json` file as a plain JSON file.

### Mapping a conda-package to the OCI registry

A given conda-package is identified by a URL like `<subdir>/<package-name>-<version>-<build>.<ext>` where `<subdir>` is the platform and architecture, `<package-name>` is the name of the package, `<version>` is the version of the package, `<build>` is the build string of the package, and `<ext>` is the extension of the package file.

#### Mapping the package name

> [!NOTE]
> **Package names in the conda world**
> 
> The following regex is given by [`conda/schemas`](https://github.com/conda/schemas/blob/473708ac97283708d6664cbd89b8049ad1623489/common-1.schema.json#L58-L82) for a valid package name: `^[a-z0-9_](?!_)[._-]?([a-z0-9]+(\.|-|_|$))*$`
> 
> That means, a package can start with an alphanumeric character or a _single_ underscore (not multiple), and can contain dots, dashes, and underscores. It also has to end with a alphanumeric character (cannot end with a dot, dash, or underscore).

To store this package on an OCI registry, we need to map it to a name and tag. The name is `<channel>/<subdir>/<package-name>`. The tag is `<version>-<build>`. There are some special rules for OCI registry names and tags for which we need some mapping. The regex for valid names is as follows:

`[a-z0-9]+((\.|_|__|-+)[a-z0-9]+)*(\/[a-z0-9]+((\.|_|__|-+)[a-z0-9]+)*)*` ([ref](https://github.com/opencontainers/distribution-spec/blob/main/spec.md#pulling-manifests))

The regex expresses that names can only start with an alphanumeric letter.

In `conda`, names can start with an underscore and it is used by conda-forge (e.g. `_libgcc_mutex`). For this reason, we prepend packages with a leading underscore with the string `zzz`. The name would thus be changed to `zzz_libgcc_mutex`.

#### Mapping the tag

The tag is the version and build string of the packages, using a `-` as a separator. However, a OCI tag has to conform to the following regex:

`[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}`

Some characters that are used in the conda-forge repository as part of the build string are not allowed in the OCI registry. For this reason, we use the following mapping:

- `+` is replaced by `__p__`
- `!` is replaced by `__e__`
- `=` is replaced by `__eq__`

#### Authentication

Pulling a public image from a Container registry can be done anonymously ([ref](https://docs.github.com/en/packages/learn-github-packages/about-permissions-for-github-packages#visibility-and-access-permissions-for-packages)).

A token can be requested with `pull` scope, using the following URL:
`https://ghcr.io/token?scope=repository:<org>/<channel-name>/<subdir>/<package-name-or-repodata.json>:pull`

Note that in the case of pulling repodata, the name `repodata.json` is always used in the URL regardless of the encoding.

#### Implementation (conda / mamba / rattler)

##### mamba

In order to fetch packages from an OCI registry, the corresponding URL should be used as a channel (i.e `oci://ghcr.io/channel-mirrors/conda-forge`).

When a user requests installing a package, a set of requests to fetch `repodata.json` are first performed as follows:

- A token is requested to anonymously pull `repodata.json` using the following URL:\
`https://ghcr.io/token?scope=repository:channel-mirrors/conda-forge/<subdir>/repodata.json:pull`
- The manifest is then pulled using `https://ghcr.io/v2/channel-mirrors/conda-forge/<subdir>/repodata.json/manifests/<reference>`.\
`<reference>` is always set to `latest` in `mamba`.\
This is also where the repodata file encoding is handled (checking `mediaType` field in the layers).\
In `mamba`, `zstd` encoding has priority if present, otherwise, raw `repodata.json` is picked, and the corresponding SHA256 hash is set for the next step.
- Repodata blob is then downloaded using:\
`https://ghcr.io/v2/channel-mirrors/conda-forge/<subdir>/repodata.json/blobs/sha256:<HASH>`

Then, to fetch the package itself, and using the same token, the corresponding blob is downloaded using:
`https://ghcr.io/v2/channel-mirrors/conda-forge/<subdir>/<package-name>/blobs/sha256:<HASH>`
where <HASH> is the SHA256 hash of the requested package, retrieved from `repodata.json`.
