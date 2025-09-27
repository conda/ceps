# CEP XXXX - Distributable package artifacts file formats

<table>
<tr><td> Title </td><td> CEP XXXX - Distributable package artifacts file formats </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Jaime Rodríguez-Guerra &lt;jaime.rogue@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> Sep 27, 2025</td></tr>
<tr><td> Updated </td><td> Sep 27, 2025</td></tr>
<tr><td> Discussion </td><td> N/A </td></tr>
<tr><td> Implementation </td><td> N/A </td></tr>
</table>

## Abstract

This CEP standardizes the archive file formats used for conda artifacts distribution: `.tar.bz2` and `.conda`.

## Motivation

The motivation of this CEP is merely informative. It describes the details existing archive file formats.

## Nomenclature

- Archive: A compressed file which, once extracted, may result in one or more files and/or directories.
- Artifact: The distributable file that is produced as a result of a build process. It happens to be an archive. When used as "conda artifact", it is meant to encompass both `.tar.bz2` and `.conda` archive file formats.
- Tarball: A file that has been produced by running `tar` on a set of files. The resulting `.tar` file MAY be further compressed into another file format (e.g. `.gz` or `.bz2`), and may be still called compressed tarball or simply tarball.
- Package: Roughly speaking, a distributable artifact that ships executable, libraries or resources needed to support the execution of programs. It may refer to the compressed archive, or its extracted form, without further distinction. The emphasis is on the distributed contents, not so much on the form.

## Specification

conda packages, whose contents are described and standardized in [CEP PR#133](https://github.com/conda/ceps/pull/133), MAY be archived and distributed in two formats:

- `.tar.bz2`: The first generation of conda archives.
- `.conda`: The second generation of conda archives.

### `.tar.bz2`

To produce a `.tar.bz2` file, the conda package directory as described in [CEP PR#133](https://github.com/conda/ceps/pull/133) MUST be first archived into an uncompressed tarball (`.tar`). The root level of the archive MUST match the root level of the target location once installed (i.e. no intermediate subdirectories). The resulting tarball MUST be then compressed using the BZ2 compression scheme. The filename MUST follow [CEP 26](./cep-0026.md), with a `.tar.bz2` extension. Namely: `{name}-{version}-{build}.tar.bz2`.

For example, given a package directory `project-1.2.3-0/`, GNU `tar` can be used like this:

```bash
cd project-1.2.3-0/
tar cvjf project-1.2.3-0.tar.bz2 .
```

The resulting tarball `project-1.2.3-0.tar.bz2` can be extracted using:

```bash
tar xvf project-1.2.3-0.tar.bz2
```

### `.conda`

A `.conda` artifact MUST be a ZIP file whose filename follow [CEP 26](./cep-0026.md) with a `.conda` extension (i.e. `{name}-{version}-{build}.conda`) and ships two inner compressed tarballs and a JSON document:

- `info-{name}-{version}-{build}.tar.{extension}`
- `pkg-{name}-{version}-{build}.tar.{extension}`
- `metadata.json`

The `info-*` and `pkg-*` tarballs MUST be compressed using any compression scheme, but SHOULD use ZSTD (with `extension = '.zst'`) for better results. Each tarball MUST be named with the above syntax, taking the `name`, `version` and `build` values from the `info/index.json` file as described in [CEP PR#133](https://github.com/conda/ceps/pull/133).

The `info-*` tarball MUST contain the full `info/` folder as described in [CEP PR#133](https://github.com/conda/ceps/pull/133). The `pkg-*` tarball MUST carry everything else in the package directory. The root level of the tarballs MUST match the root level of the target location once installed (i.e. no intermediate subdirectories).

The `metadata.json` MUST be a JSON document that ships a dictionary following this schema:

- `conda_pkg_format_version: int`. The version of the `.conda` format. Currently `2`.

For example, given a package directory `project-1.2.3-0/`, GNU `tar` and `zstd` can be used like this:

```bash
mkdir workspace/
cd project-1.2.3-0/
tar --use-compress-program=zstd cvf info-project-1.2.3-0.tar.zstd info/
mv info-project-1.2.3-0.tar.zstd ../workspace
tar --use-compress-program=zstd cvf pkg-project-1.2.3-0.tar.zstd !info/
mv pkg-project-1.2.3-0.tar.zstd ../workspace
cd ../workspace
touch '{"conda_pkg_format_version": 2}' > metadata.json
zip project-1.2.3-0.conda .
```

The resulting `project-1.2.3-0.conda` archive can be extracted with:

```bash
unzip project-1.2.3-0.conda
tar --use-compress-program=zstd xvf info-project-1.2.3-0.tar.zstd
tar --use-compress-program=zstd xvf pkg-project-1.2.3-0.tar.zstd
```

## Rationale

`.tar.bz2` archives can be slow to unpack and do not support arbitrary lookups without prior extraction. BZ2 is not as effective as more modern compression schemes. Hence, `.conda` was introduced as a replacement. The outer `.zip` archive layer with two inner component allows for individual component extraction, so it's possible to check the `info/` folder without downloading the whole artifact. The inner ZSTD compression allows for faster and more efficient compression and decompression.

## References

- <https://docs.conda.io/projects/conda-build/en/stable/resources/package-spec.html>
- <https://www.anaconda.com/blog/understanding-and-improving-condas-performance>

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
