# Support for `abi3` Python packages

<table>
<tr><td> Title </td><td> Support for <code>abi3</code> Python packages </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Isuru Fernando &lt;ifernando@quansight.com&gt;</td></tr>
<tr><td> Created </td><td> July 01, 2023</td></tr>
</table>

## Abstract

This CEP specifies how `abi3` Python packages are supported in conda install tools
(conda/mamba/micromamba/pixi) and how they are built in conda build tools
(conda-build/rattler-build).

## Motivation

When building extensions for Python, they might use Python minor version
specific symbols. This results in the extension being usable only on that minor
version. These extensions are identified by the extension suffix.
For example, `foo.cpython-310-x86_64-linux-gnu.so` is an extension that
supports only CPython 3.10 on the `x86_64-linux-gnu` platform.

However, some symbols are available in all Python major.minor versions with some
lower bound on the Python version. These symbols are part of the
[limited C API][C_API_Stability]. It is guaranteed that the symbols Stable ABI
introduced in Python 3.X are available in Python 3.Y for any `Y >= X`.
Extensions using only these symbols are identified by the extension suffix
`abi3.so`. For example, `foo.abi3.so`.

These extensions only support the platform it was built for (e.g.
`x86_64-linux-gnu`), but this is not specified in the extension suffix.

Note that the stable ABI is only specific to CPython and is not compatible with
PyPy or other Python implementations. For a Python implementation independent
ABI, see the [HPy project][HPy].

The motivation for building `abi3` packages is that we only need to build the
extension for one Python version and the extension will work for any Python
later version. This reduces the build matrix from 4-5 Python minor versions to one
Python minor version and reduces the maintenance burden of package builders.

## noarch: Python packages

`abi3` packages are Python version independent and we will first look at
`noarch: python` packages that are also Python version independent and in addition
are arch-independent.

`noarch: python` packages have several attributes to them:

- **A1**:
 They have `subdir: noarch` in `info/index.json`.

- **A2**:
 They have `noarch: Python` in `info/index.json`.

- **A3**:
 Python files are in `<PREFIX>/site-packages`.

- **A4**:
 Entry points are recorded in `info/link.json`.

A conda install tool does four things to support them:

- **B1**:
 Files in `<PREFIX>/site-packages` are moved to the correct location. Eg:
  `<PREFIX>/lib/python3.10/site-packages`.

- **B2**:
 Python files (files ending with `*.py`) are compiled to `.pyc` files. Eg:
  `<PREFIX>/lib/python3.10/site-packages/foo.py` is compiled to
  `<PREFIX>/lib/python3.10/site-packages/__pycache__/foo.cpython-310.pyc`.

- **B3**:
  `.pyc` files created are recorded in `<PREFIX>/conda-meta/<pkg>.json`
 so that they are removed properly when the package is uninstalled.

- **B4**:
 Entry points in `info/link.json` are materialized.

### info/link.json file
An example `info/link.json` for `noarch: python` looks like

```json
{
  "noarch": {
    "entry_points": [
      "isympy = isympy:main"
    ],
    "type": "python"
  },
  "package_metadata_version": 1,
  "preferred_env": "foo"
}
```

An example for `info/link.json` for `noarch: generic` looks like

```json
{
  "noarch": {
    "type": "generic"
  },
  "package_metadata_version": 1
}
```


Here `preferred_env` is ignored by conda since 2017 and is not supported by
other conda install tools. Therefore `info/link.json` is used exclusively
for `noarch` packages and out of the two types, `noarch: generic` packages
do not require any special action.

### info/index.json file

An example of a `noarch: python` recipe.

```json
{
  "arch": null,
  "build": "pyh2585a3b_103",
  "build_number": 103,
  "depends": [
    "mpmath >=0.19",
    "python >=3.8"
  ],
  "license": "BSD-3-Clause",
  "license_family": "BSD",
  "name": "sympy",
  "noarch": "python",
  "platform": null,
  "subdir": "noarch",
  "timestamp": 1718625708903,
  "version": "1.12.1"
}
```

### Current behavior in solver tools

Conda package upload tools like `anaconda-client` use `A1` to upload
the package to the `noarch` subdir.

Conda install tools have slightly different behavior.

Conda:
1. Actions `B1, B2, B3` are applied for packages with `A3`.
2. Action `B4` is applied for packages with `A4`.

Micromamba:
1. Actions `B1, B2, B3` are applied for packages with both `A2, A3`.
2. Action `B4` is applied for packages with both `A2, A4`.


## Implementation for `abi3` packages

### Support in install tools

We require the following attributes in `abi3` packages:

- **C1**:
 They have `subdir: <platform>` where `<platform>` is the subdir
 that the package was built for.

- **C2**:
 They have `noarch: python`.

- **C3**:
  `A2, A3, A4` are applied.

This is compatible with `conda/mamba/micromamba` install tools
currently.

### Support in build tools

This requires support from build tools to set `subdir: <platform>`.

In particular recipe authors would set

```yaml
build:
  python_version_independent: true

requirements:
  host:
    - python
    - python-abi3
```

which would make the build tool

- **D1**:
Set `noarch: python` in `info/index.json`.

Note that `python-abi3` would set the runtime requirements.
This is explicitly required from recipe authors so that we do not
restrict this CEP to `abi3` packages and allow the possibility for `abi4` etc.

An example `python-abi3=3.8` package would set itself in its
`run_exports` entry and will have the following requirements:

```yaml
requirements:
  run:
    - cpython >=3.8
    - python-gil
```

## Alternatives considered

### Apply all actions in a `post-link.sh` script.

A draft work provided at [python-feedstock][Python-pr-669]
This was suggested by @mbargull, but some community members (@baszalmstra,
@wolfv) does not prefer post-link scripts as they can be used for arbitrary
code execution. However, in the author's opinion, this attack vector is not a
new one since the install tool uses the Python executable in the host
environment to compile the Python files.

### `noarch: python` packages with `__linux, __osx, __win` constrains.

This suggestion by `@wolfv` is not ideal as this clutters `noarch` subdir
`repodata.json` file with packages that are useless for the platform in question.

### A new `package_metadata_version`

Since we can work within the constraints of the current install tools we
do not need to require extra support from install tools.

<!--links-->
[C_API_Stability]: https://docs.Python.org/3/c-api/stable.html

[HPy]: https://hpyproject.org

[Python-pr-669]: https://github.com/conda-forge/Python-feedstock/pull/669
