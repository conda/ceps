# OCI registries as conda channels

We want to use OCI registries as a storage for conda packages. This CEP specifies how we lay out conda packages on an OCI registry.

## Specification

An OCI artifact consists of a manifest and a set of blobs. The manifest is a JSON document that describes the contents of the artifact. The blobs are the actual data that the manifest refers to. The manifest is stored in the registry as a blob, and the blobs are stored in the registry as blobs.

The manifest consists of some metadata and a number of "layers". Each layer is a reference to a blob.

Layers can have arbitrary names and mediaTypes.

An OCI manifest is referenced by a name and a tag.

For further details, please refer to the official [OCI Distribution spec](https://github.com/opencontainers/distribution-spec/blob/v1.0/spec.md#definitions).

### Conda package artifacts on an OCI registry

The manifest for a conda package on an OCI registry should look like follows.

It should have a name and a tag. The name is `<channel>/<subdir>/<package-name>`.
The tag is the version and build string of the packages, using a `-` as a separator.

For example, a package like `xtensor-0.10.4-h431234.conda` would map to a OCI registry `conda-forge/linux-64/xtensor:0.10.4-h431234`.

### Layers

A conda package, in an OCI registry, should ship up to 3 layers:

- The package itself, as a tarball. (mandatory)
- The package `info` folder as a gzipped "tar.gz" file.
- The package `info/index.json` file as a plain JSON file.

The mediaType for the different layers is as follows:

- for a .tar.bz2 package, the mediaType is `application/vnd.conda.package.v1`
- for a .conda package, the mediaType is `application/vnd.conda.package.v2`
- for the `info` folder as gzip the mediaType is `application/vnd.conda.info.v1.tar+gzip`
- for the `index.json` file the mediaType is `application/vnd.conda.info.index.v1+json`

Using the `mediaType` field in the manifest, we can find the layer + SHA256 hash to pull the corresponding blob.
Each `mediaType` should only be present in one layer.

## Repodata on OCI registries

The `repodata.json` file is a JSON file that contains metadata about the packages in a channel.
It is used by conda to find packages in a channel.

On an OCI registry it should be stored under `<channel>/<subdir>/repodata.json`.
The repodata file should have one entry that has the `latest` tag. This entry should point to the latest version of the repodata.
All versions of the repodata should also be tagged  with a UTC timestamp of the following format: `YYYY.MM.DD.HH.MM.SS`, e.g. `2024.04.12.07.06.32`.

The mediaType for the raw `repodata.json` file is `application/vnd.conda.repodata.v1+json`. However, for large repositories it's advised to store the `zstd` encoded repodata file with the mediaType `application/vnd.conda.repodata.v1+json+zstd` as an additional layer in `<channel>/<subdir>/repodata.json`. ([ref](https://github.com/opencontainers/image-spec/blob/main/layer.md#gzip-media-types))

Other encodings are also accepted:

- `application/vnd.conda.repodata.v1+json+gzip`
- `application/vnd.conda.repodata.v1+json+bz2`

For `jlap`, the following mediaType is used:

- `application/vnd.conda.jlap.v1`

The `jlap` file should also be stored under the `<channel>/<subdir>/repodata.json` path as an additional layer.

### Mapping a conda-package to the OCI registry

A given conda-package is identified by a URL like `<subdir>/<package-name>-<version>-<build>.<ext>` where `<subdir>` is the platform and architecture, `<package-name>` is the name of the package, `<version>` is the version of the package, `<build>` is the build string of the package, and `<ext>` is the extension of the package file.

To store this package on an OCI registry, we need to map it to a name and tag. The name is `<channel>/<subdir>/<package-name>`. The tag is `<version>-<build>`. There are some special rules for OCI registry names and tags for which we need some mapping. The regex for valid names is as follows:

`[a-z0-9]+((\.|_|__|-+)[a-z0-9]+)*(\/[a-z0-9]+((\.|_|__|-+)[a-z0-9]+)*)*` ([ref](https://github.com/opencontainers/distribution-spec/blob/main/spec.md#pulling-manifests))

The regex expresses that names can only start with an alphanumeric letter.

In `conda`, names can start with an underscore and it is used by conda-forge (e.g. `_libgcc_mutex`). For this reason, we replace a leading underscore with the string `zzz`.

The tag is the version and build string of the packages, using a `-` as a separator. However, a OCI tag can only contain the following regex:

`[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}`

Some characters that are used in the conda-forge repository as part of the build string are not allowed in the OCI registry. For this reason, we use the following mapping:

- `+` is replaced by `__p__`
- `!` is replaced by `__e__`
- `=` is replaced by `__eq__`