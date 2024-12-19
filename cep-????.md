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

This CEP standardizes which virtual packages MUST be offered by conda install tools.

## Motivation

Virtual packages are used to expose details of the system configuration to a conda client. They are commonly used as dependencies in regular packages to constrain on which systems they can be installed. Some examples include:

* On Linux, the minimum GNU `libc` version that must be available in the system via the `__glibc` virtual package.
* The oldest macOS version compatible with the package via the `__osx` virtual package.
* Whether a `noarch` package should be constrained to a single operating system via the `__linux`, `__osx` or `__win` virtual packages (often with no version constraint).
* The minimum CPU microarchitecture level that the binaries require via the `__archspec` virtual package.
* The lowest CUDA version the GPU driver is compatible with via `__cuda`.

## Specification

A virtual package is defined as a package record with three fields: name, version and build string.
The name MUST start with double underscore (`__`). The version and build string MUST follow the same semantics as in regular package records. More specifically, the version field MUST follow the version string specifications, regardless its origin (computed from a system property, overridden by the user or configuration, or provided by default by the tool).

Some general considerations: 

- The version or build string of a virtual package MAY be overridden by the value of `CONDA_OVERRIDE_{NAME}` environment variable, with `{NAME}` being the uppercased name of the virtual package. Many exceptions apply so please observe the details in the section below.
- The build string MAY be zero (`0`). Some exceptions apply. See below.
- When the tool used a fallback default value instead of a computed one, it SHOULD also inform the user of that choice and its possible override options (e.g. `CONDA_OVERRIDE_{NAME}` variables, CLI flags, configuration file, etc).

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

This virtual package MUST be always present, with the version set to `1`. The build string SHOULD reflect the detected CPU microarchitecture when the target platform matches the native platform, 
as provided by the generic values in the [`archspec/archspec-json` database](https://github.com/archspec/archspec-json/blob/v0.2.5/cpu/microarchitectures.json), plus some exceptions. 

For example,  `conda/conda` reports its generic values for Intel/AMD and vendor-specific names for Apple:

- Generic: `x86_64_v1`, `x86_64_v2`, `x86_64_v3`, `x86_64_v4`, `arm`, `ppc`...
- Apple: For M1, the value is `m1`. M2 and M3 are reported as `m2` and `m3`, respectively.

If the microarchitecture cannot be detected or the target platform does not match the native platform, the build string MUST be set to the second component of the target platform, mapped with these rules:

| Target platform | Reported `archspec` build string |
| --------------- | -------------------------------- |
| `*-32`          | `x86`                            |
| `*-64`          | `x86_64`                         |
| `*-armv6l`      | `armv6l`                         |
| `*-armv7l`      | `armv7l`                         |
| `*-aarch64`     | `aarch64`                        |
| `*-arm64`       | `arm64`                          |
| `*-ppc64`       | `ppc64`                          |
| `*-ppc64le`     | `ppc64le`                        |
| `*-riscv64`     | `riscv64`                        |
| `*-s390x`       | `s390x`                          |
| `zos-z`         | `0`                              |
| Any other value | `0`                              |

The build string MUST be overridable with the `CONDA_OVERRIDE_ARCHSPEC` environment variable, if set to a non-empty value.

#### `__cuda`

This virtual package MUST be present when the system exhibits GPU drivers compatible with the CUDA runtimes. When available, the version value MUST be set to the oldest CUDA version supported by the detected drivers (i.e. the formatted value of `libcuda.cuDriverGetVersion()`), constrained to the first two components (major and minor) and formatted as `{major}.{minor}`. The build string MUST be `0`.

The version MUST be overridable with the `CONDA_OVERRIDE_CUDA` environment variable, if set to a non-empty value that can be parsed as a version string.

#### `__glibc`

This virtual package MUST NOT be present if the target platform is not `linux-*`.

This virtual package MUST be present when the native and target platforms are both the same type of `linux-*` and GNU `libc` is installed in the system. The version value MUST be set to the system GNU `libc` version, constrained to the first two components (major and minor) formatted as `{major}.{minor}`. If the version cannot be estimated, the tool MUST set the version to a default value (e.g. `2.17`). 

If the native platform does not match the target platform, the tool MAY export `__glibc` with its `version` field set to a default value (e.g. `2.17`) of its choice.  

If the `CONDA_OVERRIDE_GLIBC` environment variable if set to a non-empty value that complies to the version string specification, the tool MUST export `__glibc` with its version value set to the value of the environemnt variable.

The build string MUST always be `0`. 


> The GNU `libc` version can be computed via:
>
> - Python's `os.confstr("CS_GNU_LIBC_VERSION")`
> - `getconf GNU_LIBC_VERSION`
> - `ldd --version`. Please verify that it references GNU `libc` or GLIBC. For non-standard installs, using a GLIBC compatibility layer, this may require locating the implementation and directly querying.

#### `__linux`

This virtual package MUST be present when the target platform is `linux-*`. Its version value MUST be set to the Linux kernel version, constrained to the first two to four numeric components formatted as `{major}.{minor}.{micro}.{patch}`. If the version cannot be estimated (e.g. because the native platform is not Linux), the tool MUST set `version` to a fallback value of its choice. The build string MUST be `0`.

The version MUST be overridable with the `CONDA_OVERRIDE_LINUX` environment variable, if set to a non-empty value that matches the regex `"\d+\.\d+(\.\d+)?(\.\d+)?"`. The environment variable MUST be ignored when the target platform is not `linux-*`.

> The Linux kernel version can be obtained via:
> 
> - Python's `platform.release()`
> - `uname -r`
> - `cat /proc/version`

#### `__osx`

This virtual package MUST be present when the target platform is `osx-*`. Its version value MUST be set to the first two numeric components of macOS version formatted as `{major}.{minor}`. If applicable, the `SYSTEM_VERSION_COMPAT` environment variable workaround MUST NOT be enabled; e.g. the version reported for Big Sur should be 11.x and not 10.16. If the version cannot be estimated (e.g. because the native platform is not macOS), the fallback value MUST be set to `0`. The build string MUST be `0`.

The version MUST be overridable with the `CONDA_OVERRIDE_OSX` environment variable if set to a non-empty value that can be parsed as a version string. The environment variable MUST be ignored when the target platform is not `osx-*`.

> The macOS version can be obtained via:
> 
> - Python's `platform.mac_ver()[0]`
> -  `SYSTEM_VERSION_COMPAT=0 sw_vers -productVersion`

#### `__unix`

This virtual package MUST be present when the target platform is `linux-*`, `osx-*` or `freebsd-*`. The version and build string fields MUST be set to `0`.

The `CONDA_OVERRIDE_UNIX` environment variable MUST NOT have any effect.

#### `__win`

This virtual package MUST be present when the target platform is `win-*`. The version MUST be set to the first three numeric components of the Windows build version, formatted as `{major}.{minor}.{build}`. If the version cannot be estimated (e.g. because the target platform does not match the native platform), the tool MUST set the version to a default value of its choice.

The version MUST be overridable with the `CONDA_OVERRIDE_WIN` environment variable if set to a non-empty value that can be parsed as a version string. The environment variable MUST be ignored when the target platform is not `win-*`.

The build string MUST be `0`.

> The version string `{major}.{minor}.{build}` can be obtained from:
> 
> - Python's `platform.win32_ver()`
> - CMD's `ver`
- Powershell's `[System.Environment]::OSVersion.Version`, `(Get-CimInstance Win32_OperatingSystem).version`
> - The command `wmic os get version`

## Potential future work

This CEP focuses on the standardization of existing virtual package implementations.

The following items are not considered here. Though would be open for discussion in future CEP work:

- Additional OSes, like `__freebsd` or `__netbsd`.
- Coarse grain architecture information, like `__x86_64` or `__arm64`, or, more generally, [`__arch`](https://github.com/conda/conda/issues/13420).
- More `libc` implementations, like `__musl`.

## References

* [Virtual packages implementation in `conda/conda` 24.11.1](https://github.com/conda/conda/tree/24.11.1/conda/plugins/virtual_packages)
* [Virtual packages implementation in `libmamba` 2.0.5](https://github.com/mamba-org/mamba/blob/libmamba-2.0.5/libmamba/src/core/virtual_packages.cpp)
* [Virtual packages implementation in `rattler` 0.28.8](https://github.com/conda/rattler/tree/rattler-v0.28.8/crates/rattler_virtual_packages/src)
* [ENH: make `__win` version usable for package metadata (conda/conda#14443)](https://github.com/conda/conda/issues/14443)
* [Drop `CONDA_OVERRIDE_WIN` environment variable (mamba-org/mamba#2815)](https://github.com/mamba-org/mamba/pull/2815)
* [`__arch` feature request](https://github.com/conda/conda/issues/13420)

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
