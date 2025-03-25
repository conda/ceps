# CEP XXXX - Text spec input files

<table>
<tr><td> Title </td><td> CEP XXXX - Text spec input files </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Jaime Rodríguez-Guerra &lt;jaime.rogue@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> June 3, 2024 </td></tr>
<tr><td> Updated </td><td> March 18, 2025 </td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/79 </td></tr>
<tr><td> Implementation </td><td> See references </td></tr>
</table>

## Abstract

This CEP standardizes the format of `.txt` input files for conda clients.

## Motivation

The motivation of this CEP is merely informative. It describes the details of an existing file format.

## Nomenclature

This type of input file has not received a specific name. Different conda clients vaguely refer to it as [file specification](https://github.com/conda/conda/blob/841d9d57fd96ad27cda4b7c43549104a96f961ce/conda/cli/helpers.py#L90-L91), or [text spec file](https://github.com/mamba-org/mamba/blob/9300a6530cac4f5575e7f8aa4049fbb9c1150909/docs/source/user_guide/micromamba.rst?plain=1#L143).

In this CEP, we will use the term "text spec file".

## Specification

Text spec files use plain text to specify one package requirement per line. Lines starting with `#` are considered comments and SHOULD be ignored. Empty lines or lines consisting only of whitespace MUST be ignored.

Some conda clients tend to include a comment line specifying the platform the file was written for. This line often follows the syntax `# platform: {SUBDIR}`, where `{SUBDIR}` is a platform identifier like `linux-64` or `osx-arm64`. Other field comments like the version of the generator tool may be found, such as `# conda version: 24.11.0`. These lines are not required, but implementers might choose to parse it if found for logging or verification purposes.

There are two flavors of this input file: explicit and not explicit.

### Explicit input files

If the file includes a line whose only non-whitespace content is the case-sensitive word `@EXPLICIT`, the file MUST be considered and handled as explicit.

In explicit files, each package requirement line MUST specify a single, direct URL (as in RFC 3986) to a conda artifact, or a file path. File paths SHOULD be preferably expressed as `file://` URLs. Relative paths MAY be used, and SHOULD be processed as relative to the working directory, not the input file parent directory.

Each URL MAY be immediately followed by an anchor tag (`#<hash>`) that encodes the expected MD5 or SHA256 checksum of the downloaded artifact as a lowercase string of 32 or 64 hexadecimal characters, respectively. The prefix `sha256:` MAY be present in the case of SHA256 checksums.

More specifically, whitespace-stripped lines SHOULD be parsable by this Python-style regex:

```re
(?:(?P<url_p>.+)(?:[/\\]))?(?P<fn>[^/\\#]+(?:\.tar\.bz2|\.conda))(?:#((?P<md5>[0-9a-f]{32})|((sha256:)?(?P<sha256>[0-9a-f]{64}))))?$
```

Leading tildes (`~`) and environment variables MUST be replaced with their values at runtime for backwards compatibility (as Python's [`os.path.expanduser`](https://docs.python.org/3/library/os.path.html#os.path.expanduser) and [`os.path.expandvars`](https://docs.python.org/3/library/os.path.html#os.path.expandvars) would do, respectively). That said, users SHOULD NOT use environment variables in their explicit spec files for the sake of reproducibility.

When an explicit input file is processed, the conda client SHOULD NOT invoke a solver. Because of this, the lines SHOULD be sorted topologically; e.g. if a package `A` depends on `B`, then the URL of B should come first.

### Non-explicit input files

In the absence of an `@EXPLICIT` line, the file is considered regular or not explicit. Each line will encode a `MatchSpec`-compatible string. The solver SHOULD be invoked and, as such, topological sorting is not required.

## Examples

An example of an explicit TXT input file:

```text
# This line is a comment. The one below only consists of whitespace and will also be ignored.

# This file may be used to create an environment using:
# $ conda create --name <env> --file <this file>
# platform: osx-arm64
@EXPLICIT
https://conda.anaconda.org/conda-forge/osx-arm64/bzip2-1.0.8-h93a5062_5.conda#1bbc659ca658bfd49a481b5ef7a0f40f
https://conda.anaconda.org/conda-forge/osx-arm64/ca-certificates-2024.2.2-hf0a4a13_0.conda#fb416a1795f18dcc5a038bc2dc54edf9
https://conda.anaconda.org/conda-forge/osx-arm64/libexpat-2.6.2-hebf3989_0.conda#e3cde7cfa87f82f7cb13d482d5e0ad09
https://conda.anaconda.org/conda-forge/osx-arm64/libffi-3.4.2-h3422bc3_5.tar.bz2#086914b672be056eb70fd4285b6783b6
https://conda.anaconda.org/conda-forge/osx-arm64/libzlib-1.2.13-h53f4e23_5.conda#1a47f5236db2e06a320ffa0392f81bd8
https://conda.anaconda.org/conda-forge/osx-arm64/ncurses-6.5-hb89a1cb_0.conda#b13ad5724ac9ae98b6b4fd87e4500ba4
https://conda.anaconda.org/conda-forge/noarch/tzdata-2024a-h0c530f3_0.conda#7b2b69c54ec62a243eb6fba2391b5e443421608c3ae5dbff938ad33ca8db5122
https://conda.anaconda.org/conda-forge/osx-arm64/xz-5.2.6-h57fd34a_0.tar.bz2#39c6b54e94014701dd157f4f576ed211
https://conda.anaconda.org/conda-forge/osx-arm64/libsqlite-3.45.3-h091b4b1_0.conda#c8c1186c7f3351f6ffddb97b1f54fc58
https://conda.anaconda.org/conda-forge/osx-arm64/openssl-3.3.0-hfb2fe0b_2.conda#c9602073e34599f40b8c4ce9e19cabf6
https://conda.anaconda.org/conda-forge/osx-arm64/readline-8.2-h92ec313_1.conda#8cbb776a2f641b943d413b3e19df71f4
https://conda.anaconda.org/conda-forge/osx-arm64/tk-8.6.13-h5083fa2_1.conda#b50a57ba89c32b62428b71a875291c9b
https://conda.anaconda.org/conda-forge/osx-arm64/python-3.12.3-h4a7b5fc_0_cpython.conda#8643ab37bece6ae8f112464068d9df9c
https://conda.anaconda.org/conda-forge/noarch/setuptools-69.5.1-pyhd8ed1ab_0.conda#sha256:72d143408507043628b32bed089730b6d5f5445eccc44b59911ec9f262e365e7
# Note how hashes are optional
https://conda.anaconda.org/conda-forge/noarch/wheel-0.43.0-pyhd8ed1ab_1.conda
https://conda.anaconda.org/conda-forge/noarch/pip-24.0-pyhd8ed1ab_0.conda
```

A regular input file:

```text
# This file may be used to create an environment using:
# $ conda create --name <env> --file <this file>
# platform: osx-arm64
# Any of these syntaxes is also recognized as a match specification
python
scikit-learn
scipy=1.13.1
setuptools>=69.5.1
tk[build=h5083fa2_1]
```

## Reference

- [Explicit URL regex](https://github.com/conda/conda/blob/9eb05d85702aa78fd3793b840d79a910764544f1/conda/misc.py#L52-L59)
- [`explicit()` implementation in `conda`](https://github.com/conda/conda/blob/9eb05d85702aa78fd3793b840d79a910764544f1/conda/misc.py#L95-L158)
- [`explicit_environment_spec` implementation in `rattler`](https://github.com/conda/rattler/blob/41ae96e57e46d3a52a11fedfd0b72f3fd533accd/crates/rattler_conda_types/src/explicit_environment_spec.rs)
- [Implementation in `mamba`](https://github.com/mamba-org/mamba/blob/bd591115a1acca0a131289f32f5673886895018b/libmamba/src/api/install.cpp#L904-L940)

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
