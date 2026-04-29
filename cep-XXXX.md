# CEP XXXX - The `__cuda_arch` virtual package

<table>
<tr><td> Title </td><td> The <code>__cuda_arch</code> virtual package </td></tr>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Daniel Ching &lt;dching@nvidia.com&gt;</td></tr>
<tr><td> Created </td><td> Mar 13, 2026</td></tr>
<tr><td> Updated </td><td> Mar 13, 2026</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/157 </td></tr>
<tr><td> Implementation </td><td> https://github.com/conda-incubator/nvidia-virtual-packages </td></tr>
<tr><td> Requires </td><td> </td></tr>
</table>

> The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT",
  "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as
  described in [RFC2119][RFC2119] when, and only when, they appear in all capitals, as shown here.

## Abstract

This CEP standardizes the `__cuda_arch` virtual package, which exposes the minimum CUDA compute
capability of detected NVIDIA devices. This extends the virtual package framework defined in
[CEP 30](cep-0030.md).

## Motivation

The `__cuda` virtual package (defined in CEP 30) exposes the maximum CUDA version supported by the
installed GPU driver. However, the driver version is a distinct property from the compute capability
of the GPU hardware itself. Compute capability is a hardware property that determines which
instructions and features a GPU supports, and it does not change with driver updates.

The `__cuda_arch` virtual package addresses use cases that `__cuda` cannot:

* **Declaring minimum compute capability requirements**: Packages that require specific GPU
  instructions (e.g. tensor cores, FP8 support) can declare a minimum `__cuda_arch` version as a
  dependency, ensuring they are only installed on compatible hardware.
* **Distributing per-architecture variants**: A package may be built and distributed as multiple
  variants targeting different SASS (Streaming ASSembler) or PTX (Parallel Thread Execution)
  targets. The solver can select the correct variant for the detected GPU hardware using the
  `__cuda_arch` virtual package.

## Specification

Implementing the `__cuda_arch` virtual package is RECOMMENDED. If a conda-compatible client
chooses to implement the `__cuda_arch` virtual package, it MUST follow these specifications:

The `__cuda_arch` virtual package MUST be absent when the `__cuda` virtual package is
absent.

When present, the version value MUST be set to the lowest compute capability of all CUDA
devices detected on the system, formatted as `{major}.{minor}`; subarchitecture letters
(e.g. `a`, `f`) are excluded. The build string MUST be `0`.

The `__cuda_arch` virtual package MUST be present when a CUDA device is detected EXCEPT when
`CONDA_OVERRIDE_CUDA_ARCH` is set as described below.

For systems without CUDA devices (e.g. a driver is installed but no devices are present),
the virtual package MUST be absent EXCEPT when `CONDA_OVERRIDE_CUDA_ARCH` is set as
described below.

If the `CONDA_OVERRIDE_CUDA_ARCH` environment variable is set to a non-empty value that can
be parsed as a compute capability string and build string separated by `=`, the
`__cuda_arch` virtual package MUST be exposed with that version and build string EXCEPT as
noted above.

If the `CONDA_OVERRIDE_CUDA_ARCH` environment variable is set to a non-empty value that can
be parsed as a compute capability string and no build string, the `__cuda_arch` virtual
package MUST be exposed with that version with the build string set to `0` EXCEPT as noted
above.

## Rationale

There is no mechanism by which a conda package may express multiple versions simultaneously.
Therefore, it is not possible for a single virtual package to express multiple unique
compute capabilities in a multi-device system. Therefore, the `__cuda_arch` virtual package
is set to the **minimum** compute capability among all detected devices rather than the
maximum. A package that declares a minimum `__cuda_arch` requirement must run correctly on
every GPU in the system. Using the minimum ensures the solver only selects packages that are
compatible with the least-capable device present. Adding PTX (Parallel Thread Execution)
code to a CUDA binary enables forward compatibility with new architectures; there is no
mechanism to provide arbitrary backward compatibility for a CUDA binary. If the maximum
compute capability were used instead, a package could be installed that runs on the newest
GPU but fails on another older GPU in the same system.

## Alternatives

Providing multiple virtual packages (one for each major compute capability) or one for the
minimum and maximum compute capability on the system would provide more information to the
solver, but would be more difficult to work when defining constraints in conda recipes.

## Backwards Compatibility

Adding the `__cuda_arch` virtual package is backwards compatible. It does not effect
preexisting packages in the ecosystem. Like `__archspec`, using this virtual package in a
conda recipe is opt-in. However, once a package depends on `__cuda_arch` it is not
installable by clients who do not have the `__cuda_arch` virtual package implemented because
the absence of `__cuda_arch` is equivalent to declaring that there are no CUDA-capable
devices installed on the system.

## Notes on usage

When building packages that target specific GPU compute capabilities, package authors SHOULD
always include PTX (Parallel Thread Execution) code for the highest targeted compute
capability. PTX is forward-compatible, meaning it can be JIT-compiled for newer GPU
generations that were not available/targeted at build time. Package authors SHOULD NOT leave
compatibility gaps between the lowest and highest targeted compute capabilities.
Family-specific instruction sets such as those for compute capability `9.0a` or `12.0f` are
not forward-compatible and MUST NOT be used as the sole binary target.

## References

* [nvidia-virtual-packages implementation](https://github.com/conda-incubator/nvidia-virtual-packages)
* [CUDA compute capability documentation](https://docs.nvidia.com/cuda/cuda-programming-guide/05-appendices/compute-capabilities.html)
* [CUDA Driver API: `cuDeviceGetAttribute()`](https://docs.nvidia.com/cuda/cuda-driver-api/group__CUDA__DEVICE.html#group__CUDA__DEVICE_1g9c3e1414f0ad901d3278a4d6645fc266)
* [CUDA Driver API: `cuDriverGetVersion()`](https://docs.nvidia.com/cuda/cuda-driver-api/group__CUDA__VERSION.html)
* [Virtual packages framework (CEP 30)](cep-0030.md)

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

[RFC2119]: https://datatracker.ietf.org/doc/html/rfc2119
