# CEP ???? - Virtual packages

<table>
<tr><td> Title </td><td> Virtual packages </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Jaime Rodríguez-Guerra &lt;jaime.rogue@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> Dec 17, 2024</td></tr>
<tr><td> Updated </td><td> Dec 17, 2024</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/103 </td></tr>
<tr><td> Implementation </td><td> https://github.com/conda/conda/tree/24.11.1/conda/plugins/virtual_packages, https://github.com/mamba-org/mamba/blob/libmamba-2.0.5/libmamba/src/core/virtual_packages.cpp, https://github.com/conda/rattler/tree/rattler-v0.28.8/crates/rattler_virtual_packages/src </td></tr>
</table>

> The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT",
  "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as
  described in [RFC2119][RFC2119] when, and only when, they appear in all capitals, as shown here.

## Abstract

This CEP standardizes which virtual packages MUST be offered by conda solvers.

## Specification

A virtual package is defined as a package record with three fields: name, version and build string.
The name MUST start with double underscore. The version and build string MUST follow the same semantics as in regular package records.

In general, the version or build string of a virtual package MAY be overridden by the value of `CONDA_OVERRIDE_{NAME}` environment variable, with `{NAME}` being the uppercased name of the virtual package. Many exceptions apply so please observe the details in the section below.

### List of virtual packages

In alphabetical order, every conda client MUST support the following virtual packages:

- `__archspec`
- `__cuda`
- `__glibc`
- `__linux`
- `__osx`
- `__unix`
- `__win`

#### `__archspec`

This virtual package MUST be always present, with the version set to `1`. The build string SHOULD reflect the detected CPU microarchitecture. If it cannot be detected, the build string SHOULD be `0`.

The build string MUST be overridable with the `CONDA_OVERRIDE_ARCHSPEC` environment variable, if set to a non-empty value.

#### `__cuda`

This virtual package MUST be present when the system exhibits GPU drivers compatible with the CUDA runtimes. When available, the version value MUST be set to the oldest CUDA version supported by the detected drivers (i.e. the formatted value of `libcuda.cuDriverGetVersion()`), constrained to the first two components (major and minor) and formatted as `{major}.{minor}`. The build string MUST be `0`.

The version MUST be overridable with the `CONDA_OVERRIDE_CUDA` environment variable, if set to a non-empty value.

#### `__glibc`

This virtual package MUST be present when the native platform is `linux-*`. Its version value MUST be set to the system `libc` version, constrained to the first two components (major and minor) formatted as `{major}.{minor}`. The build string MUST be `0`.

The `libc` version can be computed via:

- Python's `os.confstr("CS_GNU_LIBC_VERSION")`
- `getconf GNU_LIBC_VERSION`
- `ldd --version` (in GLIBC distros)
- System's `libc.so` (in MUSL distros, location not standardized)

The version MUST be overridable with the `CONDA_OVERRIDE_GLIBC` environment variable, if set to a non-empty value.

If the `libc` version could not be estimated (e.g. the tool is not running on Linux), the tool SHOULD provide a default value (e.g. `2.17`) and inform the user of that choice and its possible overrides; e.g. via `CONDA_OVERRIDE_GLIBC`, a CLI flag or a configuration file. The environment variable MUST be ignored when the target platform is not `linux~-*`.

#### `__linux`

This virtual package MUST be present when the target platform is `linux-*`. Its version value MUST be set to the Linux kernel version, constrained to two to four numeric components formatted as `{major}.{minor}.{micro}.{patch}`. If the version cannot be estimated (e.g. because the native platform is not Linux), the fallback value MUST be set to `0`. The build string MUST be `0`.

The Linux kernel version can be obtained via:

* Python's `platform.release()`
* `uname -r`
* `cat /proc/version`

The version MUST be overridable with the `CONDA_OVERRIDE_LINUX` environment variable, if set to a non-empty value that matches the regex `"\d+\.\d+(\.\d+)?(\.\d+)?"`. The environment variable MUST be ignored when the target platform is not `linux-*`.

#### `__osx`

This virtual package MUST be present when the target platform is `osx-*`. Its version value MUST be set to the first two numeric components of macOS version formatted as `{major}[.{minor}]`. If the version cannot be estimated (e.g. because the native platform is not macOS), the fallback value MUST be set to `0`. The build string MUST be `0`.

The macOS version can be contained via:

- Python's `platform.mac_ver()[0]`
- `sw_vers -productVersion`

> If applicable, the `SYSTEM_VERSION_COMPAT` workaround MUST NOT be enabled; e.g. the version reported for Big Sur should be 11.x and not 10.16.

The version MUST be overridable with the `CONDA_OVERRIDE_OSX` environment variable. If this environment variable is set to the empty string `""`, then the `__osx` virtual package MUST NOT be present. The environment variable MUST be ignored when the target platform is not `osx-*`.

#### `__unix`

This virtual package MUST be present when the target platform is `linux-*`, `osx-*` or `freebsd-*`. The version and build string fields MUST be set to `0`.

The version or build string fields MUST NOT be overridden by the `CONDA_OVERRIDE_UNIX` environment variable. However, if this environment variable is set to a non-empty value, the `__unix` virtual package MUST be present if otherwise if would not have been. The environment variable MUST be ignored when the target platform is not `linux-*`, `osx-*` or `freebsd-*`.

#### `__win`

This virtual package MUST be present when the target platform is `win-*`. The version MUST be set to the first three numeric components of the Windows build version, formatted as `{major}.{minor}.{build}`. If the version cannot be estimated (e.g. because the target platform does not match the native platform), the fallback value MUST be set to `0`. The build string MUST be `0`.

The string `{major}.{minor}.{build}` can be obtained from:

- Python's `platform.win32_ver()`
- CMD's `ver`
- Powershell's `[System.Environment]::OSVersion.Version`, `(Get-CimInstance Win32_OperatingSystem).version`
- The command `wmic os get version`

The version MUST be overridable with the `CONDA_OVERRIDE_WIN` environment variable. If this environment variable is set to the empty string `""`, then the `__win` virtual package MUST NOT be present. The environment variable MUST be ignored when the target platform is not `win-*`.

## Motivation

Virtual packages are used to expose details of the system configuration to a conda client. They are commonly used as dependencies in regular packages to constrain on which systems they can be installed. Some examples include:

* On Linux, the minimum `libc` version that must be available in the system via the `__glibc` virtual package.
* The oldest macOS version compatible with the package via the `__osx` virtual package.
* Whether a `noarch` package should be constrained to a single operating system via the `__linux`, `__osx` or `__win` virtual packages (often with no version).
* The minimum CPU microarchitecture level that the binaries require via the `__archspec` virtual package.
* The lowest CUDA version the GPU driver is compatible with via `__cuda`.

## References

* [Virtual packages implementation in `conda/conda` 24.11.1](https://github.com/conda/conda/tree/24.11.1/conda/plugins/virtual_packages)
* [Virtual packages implementation in `libmamba` 2.0.5](https://github.com/mamba-org/mamba/blob/libmamba-2.0.5/libmamba/src/core/virtual_packages.cpp)
* [Virtual packages implementation in `rattler` 0.28.8](https://github.com/conda/rattler/tree/rattler-v0.28.8/crates/rattler_virtual_packages/src)
* [ENH: make `__win` version usable for package metadata (conda/conda#14443)](https://github.com/conda/conda/issues/14443)
* [Drop `CONDA_OVERRIDE_WIN` environment variable (mamba-org/mamba#2815)](https://github.com/mamba-org/mamba/pull/2815)

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
