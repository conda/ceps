# CEP XXXX - The `__amdgpu` and `__amdgpu_arch` virtual packages

<table>
<tr><td> Title </td><td> The <code>__amdgpu</code> and <code>__amdgpu_arch</code> virtual packages </td></tr>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Silvio Traversaro &lt;silvio@traversaro.it&gt; </td></tr>
<tr><td> Created </td><td> Aug 20, 2026</td></tr>
<tr><td> Updated </td><td> Aug 20, 2026</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/189 </td></tr>
<tr><td> Implementation </td><td> https://github.com/traversaro/amdgpu-virtual-packages </td></tr>
</table>

> The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT",
  "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as
  described in [RFC2119][RFC2119] when, and only when, they appear in all capitals, as shown here.

## Abstract

This CEP standardizes the `__amdgpu` and `__amdgpu_arch` virtual packages.

`__amdgpu` indicates the presence of an AMDGPU device available through the host driver.
`__amdgpu_arch` exposes the architecture of a detected AMDGPU device.

This extends the virtual package framework defined in [CEP 30](cep-0030.md).

## Motivation

The existing NVIDIA virtual packages distinguish the host driver capability, exposed through
`__cuda`, from the GPU hardware architecture, exposed through `__cuda_arch`.

A similar distinction is useful for AMD GPUs.

The name `__rocm` would be misleading because ROCm is a user-space software stack, while the
kernel driver and GPU architecture are generally referred to as AMDGPU in AMD and LLVM
documentation.

Unlike CUDA, there is no single useful AMDGPU driver version that describes compatibility
across GPU families and driver installation mechanisms. For example, some GPUs use the
AMDGPU driver provided by the operating system, while others may use an AMD-provided DKMS
driver.

Therefore, `__amdgpu` only indicates that an AMDGPU device is available. This is done my making
`__amdgpu` a "presence" virtual package, like `__unix` defined in CEP 30, in which the version and build string
carry no information, and are set to `0`.

GPU architecture is reported separately through `__amdgpu_arch`.

## Specification

Implementing the `__amdgpu` and `__amdgpu_arch` virtual packages is RECOMMENDED. If a
conda-compatible client chooses to implement them, it MUST follow these specifications.

### `__amdgpu`

The `__amdgpu` virtual package MUST be present when at least one AMDGPU device is detected
and available through the host driver.

For systems without such a device, the virtual package MUST be absent.

The version and build string MUST both be `0`.

For example:

```text
__amdgpu=0=0
```

The version MUST NOT be interpreted as an AMDGPU driver, Linux kernel, or ROCm version.

If `CONDA_OVERRIDE_AMDGPU` is set to the empty string, the `__amdgpu` virtual package MUST
be absent.

If `CONDA_OVERRIDE_AMDGPU` is set to `0`, the `__amdgpu` virtual package MUST be exposed
with version and build string `0`.

### `__amdgpu_arch`

The `__amdgpu_arch` virtual package MUST be absent when the `__amdgpu` virtual package is
absent.

When present, its version MUST be the AMDGPU ISA version formatted as
`{major}.{minor}.{stepping}`, where all three components are decimal integers.

The build string MUST be `0`.

When several AMDGPU devices with different architectures are detected, the version MUST be
set to the highest AMDGPU ISA version among the detected devices.

The ordering of these versions MUST NOT be interpreted as defining binary compatibility
between AMDGPU architectures. A greater `__amdgpu_arch` version does not imply compatibility
with binaries targeting a lower version.

If `CONDA_OVERRIDE_AMDGPU_ARCH` is set to a non-empty value that can be parsed as an AMDGPU
ISA version, the `__amdgpu_arch` virtual package MUST be exposed with that version and build
string `0`, except when `__amdgpu` is absent.

If `CONDA_OVERRIDE_AMDGPU_ARCH` is set to the empty string, the `__amdgpu_arch` virtual
package MUST be absent.

A conforming implementation MUST produce the same ISA version as the
following platform-specific procedures.

#### Linux

On Linux, the AMDGPU ISA version MUST be consistent with the one obtained from the
`gfx_target_version` property exposed in:

```text
/sys/class/kfd/kfd/topology/nodes/<node>/properties
```

`gfx_target_version` represents an unsigned 32-bit integer and is exposed
as its decimal text representation. After parsing it as a
base-10 integer `v`, the ISA version components are:

```text
major    = (v // 10000) % 100
minor    = (v // 100) % 100
stepping = v % 100
```

The `__amdgpu_arch` version MUST be
`{major}.{minor}.{stepping}`, with all components represented as decimal
integers.

For example, `gfx_target_version = 90010` produces `9.0.10`.

#### Windows

On Windows, the AMDGPU ISA version MUST be consistent with the one obtained by calling
`hipGetDeviceProperties` from the HIP runtime library installed by the
AMD GPU driver in the Windows system directory, `%SystemRoot%\System32`
(by default `C:\Windows\System32`). The library is named
`amdhip64_<major>.dll` for versioned HIP runtimes, for example
`amdhip64_7.dll`, with `amdhip64.dll` used by older runtimes.

The `gcnArchName` member of `hipDeviceProp_t` contains an AMDGPU target
ID, for example `gfx90a` or `gfx1100:xnack-`. Only the substring before
the first `:` MUST be used to determine the ISA version.

The resulting target name MUST start with `gfx`. After removing this
prefix, all characters except the final two form the major version and
MUST be interpreted as a decimal integer. The final two characters are,
respectively, the minor and stepping versions and MUST be interpreted as
hexadecimal digits.

The `__amdgpu_arch` version MUST be
`{major}.{minor}.{stepping}`, with all components represented as decimal
integers.

For example:

```text
gfx90a              -> 9.0.10
gfx90a:xnack-       -> 9.0.10
gfx1151             -> 11.5.1
gfx1201             -> 12.0.1
```

## Rationale

There is no mechanism by which a conda virtual package may expose multiple versions
simultaneously. Therefore, a single `__amdgpu_arch` cannot describe all architectures in a
heterogeneous multi-GPU system.

`__cuda_arch` addresses this limitation by reporting the minimum CUDA compute capability.
This works well with CUDA's compatibility model and the use of PTX for forward compatibility.

There is currently no equivalent mechanism universally used by HIP and ROCm libraries.
AMDGPU binaries commonly contain code objects for specific `gfx` architectures, and an older
GPU present in the system may not even be supported by the ROCm version used by an
application.

For this reason, this CEP selects the highest detected AMDGPU architecture. This is only a
rule for choosing a representative device and does not define compatibility between
architectures.

A future mechanism capable of exposing all available architectures would represent
heterogeneous GPU systems more accurately.

## Alternatives

Using `__rocm` and `__rocm_arch` was rejected because ROCm refers to the user-space software
stack rather than the GPU and host driver.

Encoding an AMDGPU driver version in `__amdgpu` was rejected because there is no single
driver version with useful compatibility semantics across supported AMDGPU systems.

Reporting the lowest architecture, as done by `__cuda_arch`, was rejected because AMDGPU
does not currently have an equivalent to the CUDA/PTX compatibility model.

## Backwards Compatibility

Adding these virtual packages is backwards compatible and does not affect existing packages.

Once a package depends on `__amdgpu` or `__amdgpu_arch`, it will not be installable by
clients that do not implement the corresponding virtual package.

## Notes on usage

Packages that only require an available AMD GPU SHOULD depend on:

```text
__amdgpu
```

Packages distributed for a specific GPU architecture MAY additionally depend on
`__amdgpu_arch`.

Package authors SHOULD NOT assume that version ordering implies AMDGPU binary compatibility.

## References

* [Virtual packages framework (CEP 30)](cep-0030.md)
* [`__cuda_arch` virtual package (CEP 46)](cep-0046.md)
* [LLVM AMDGPU usage documentation](https://llvm.org/docs/AMDGPUUsage.html)
* [AMD ROCprofiler-SDK `gfx_target_version` definition](https://rocm.docs.amd.com/projects/rocprofiler-sdk/en/docs-7.2.2/_doxygen/rocprofiler-sdk/html/agent_8h_source.html)
* [Linux KFD AMDGPU device implementation](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/amd/amdkfd/kfd_device.c)
* [MLIR AMDGPU `Chipset` version structure](https://github.com/llvm/llvm-project/blob/main/mlir/include/mlir/Dialect/AMDGPU/Utils/Chipset.h)

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

[RFC2119]: https://datatracker.ietf.org/doc/html/rfc2119
