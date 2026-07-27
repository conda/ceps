# CEP XXXX - Subdirs and virtual packages for iOS and Android

<table>
<tr><td> Title </td><td> Subdirs and virtual packages for iOS and Android </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Wolf Vollprecht &lt;wolf@prefix.dev&gt;</td></tr>
<tr><td> Created </td><td> Jul 24, 2026</td></tr>
<tr><td> Updated </td><td> Jul 24, 2026</td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> https://github.com/conda/rattler (feat/ios-android-subdirs) </td></tr>
</table>

> The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT",
  "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as
  described in [RFC2119][RFC2119] when, and only when, they appear in all capitals, as shown here.
>
> More specifically, violations of a MUST or MUST NOT rule MUST result in an error. Violations of the
  rules specified by any of the other all-capital terms MAY result in a warning, at discretion of the
  implementation.

## Abstract

This CEP defines a set of conda subdirectories (`subdir`) for building and distributing packages that
target Apple's iOS and Google's Android, together with two new virtual packages, `__ios` and
`__android`, that carry the minimum-OS-version compatibility axis. The design maps the PyPI wheel-tag
model for these platforms ([PEP 730] for iOS, [PEP 738] for Android) onto conda's existing
subdir + virtual-package machinery, so that version compatibility is resolved by the ordinary solver
in the same way as `__osx` and `__glibc` today. The goal is a single, cross-implementation set of
names so that conda, mamba, rattler, and the wider ecosystem agree on how mobile packages are
described.

## Motivation

conda has no standard way to describe packages built for mobile operating systems. Both Python
(via [PEP 730] and [PEP 738]) and the wider native toolchain ecosystem now support iOS and Android as
first-class target platforms, and tools such as pixi and rattler-build are able to produce packages
for them. Without an agreed naming scheme, each implementation would be free to invent its
own subdir tokens (`ios_arm64` vs `ios-arm64`, `ios-sim-arm64` vs `iossimulator-arm64`) and its own
way of encoding the minimum-OS version, producing packages that cannot be described consistently or
consumed across tools. That fragmentation is exactly the class of problem this CEP exists to prevent.

Two facts about these platforms shape the design:

1. **The subdir describes a target platform.** These names identify the platform a package is *for*,
   independently of the host that resolves or builds it. In practice packages are often produced by
   cross-compiling from another host, but this CEP does not assume that — an implementation may just
   as well run natively on the platform.

2. **PyPI already encodes three axes in one wheel tag.** A wheel tag such as
   `ios_13_0_arm64_iphoneos` packs together the CPU architecture (`arm64`), the ABI / platform variant
   (device `iphoneos` vs simulator `iphonesimulator`), and the minimum OS version (`13.0`). conda
   traditionally splits these axes across the *subdir* (architecture and ABI) and *virtual packages*
   (OS-version compatibility). This CEP applies the same split rather than inventing a monolithic tag.

## Specification

### Subdirectories

This CEP defines the following subdirs. As per CEP 26, each subdir is single-architecture and follows the `<os>-<arch>` syntax.

#### iOS

| Subdir               | Architecture | Platform variant              |
| -------------------- | ------------ | ----------------------------- |
| `ios-arm64`          | `arm64`      | Device (`iphoneos`)           |
| `iossimulator-arm64` | `arm64`      | Simulator (`iphonesimulator`) |
| `iossimulator-64`    | `x86_64`     | Simulator (`iphonesimulator`) |

The device/simulator distinction is a genuine ABI split: a binary built for the simulator cannot run
on a device and vice versa, even for the same architecture. Rather than introduce a second dash
(which would break subdir-splitting tools), the variant is folded into the OS token: device builds use
`ios`, simulator builds use `iossimulator`. There is no `ios-64` (Apple ships no x86_64 iOS *device*).

#### Android

| Subdir              | Architecture | Android ABI     |
| ------------------- | ------------ | --------------- |
| `android-aarch64`   | `aarch64`    | `arm64-v8a`     |
| `android-armv7a`    | `armv7a`     | `armeabi-v7a`   |
| `android-64`        | `x86_64`     | `x86_64`        |
| `android-32`        | `x86`        | `x86`           |

The `armv7a` architecture token denotes Android's `armeabi-v7a` ABI. It is deliberately distinct from
`armv7l` (used by `linux-armv7l`): both are 32-bit ARMv7, but `armeabi-v7a` uses Android's softfp
calling convention and links against Bionic rather than glibc, so binaries are not interchangeable
between the two.

#### Android is not Linux

Although Android runs a Linux kernel, `android-*` subdirs MUST NOT be treated as Linux subdirs.
`linux-*` packages express their C-library requirement through the `__glibc` virtual package, and
Android links against Bionic, which cannot satisfy a glibc constraint. Treating Android as Linux
would allow the solver to install `linux-*` packages whose libc requirement is silently violated.
iOS and Android subdirs ARE Unix subdirs for the purpose of the `__unix` virtual package.

### Virtual packages

Two new virtual packages carry the minimum-OS-version axis that the subdir intentionally omits.

#### The `__ios` virtual package

- **Name:** `__ios`
- **Version:** the *minimum supported iOS version* (the deployment target), e.g. `13.0`. This mirrors
  the `ios_<major>_<minor>` component of a PEP 730 wheel tag.
- A package that requires iOS 13.0 or newer depends on `__ios >=13.0`, exactly as an `osx-*` package
  depends on `__osx >=<version>`.

#### The `__android` virtual package

- **Name:** `__android`
- **Version:** the *minimum supported Android API level*, encoded as a version, e.g. `21`. This
  mirrors the API-level component of a PEP 738 wheel tag such as `android_21_arm64_v8a`.
- A package that requires API level 21 or newer depends on `__android >=21`.

#### Provisioning

When solving *for* an `ios-*`/`iossimulator-*` or `android-*` target subdir, an implementation MUST
make the corresponding virtual package available:

- For an `ios-*`/`iossimulator-*` target, provide `__ios` (and `__unix`).
- For an `android-*` target, provide `__android` (and `__unix`).
- `__glibc` MUST NOT be provided for `android-*` targets.

The version MAY be detected from the host when an implementation runs natively on the platform.
Otherwise (for example when cross-compiling) it SHOULD be taken from an explicit override:

- `__ios` version: from the `CONDA_OVERRIDE_IOS` environment variable, otherwise a build-tool-supplied
  default, otherwise `0` (matches any requirement).
- `__android` version: from the `CONDA_OVERRIDE_ANDROID` environment variable, otherwise a
  build-tool-supplied default, otherwise `0`.

The exact mechanism for host-based detection is not specified by this CEP and is left to
implementations.

### Compatibility summary

The following table shows how the three PyPI wheel-tag axes are distributed in conda:

| Wheel-tag axis         | PyPI example             | conda location                        |
| ---------------------- | ------------------------ | ------------------------------------- |
| CPU architecture       | `arm64`, `x86_64`        | subdir arch (`-arm64`, `-64`)         |
| ABI / platform variant | `iphoneos` / `arm64-v8a` | subdir os token (`iossimulator`, ...) |
| Minimum OS version     | `ios_13_0`, `android_21` | `__ios` / `__android` virtual package |

## Rationale and alternatives

- **A single dash per subdir.** An alternative was to encode the simulator variant as a third dash
  (`ios-simulator-arm64`). This breaks the widespread assumption that a subdir is `<os>-<arch>` and
  splits on a single `-`. Folding the variant into the OS token (`iossimulator`) preserves that
  assumption.
- **Version in the subdir vs. a virtual package.** Encoding the minimum OS version in the subdir (as
  PyPI does in the wheel tag) would multiply the number of subdirs and move compatibility resolution
  out of the solver. Using `__ios`/`__android` keeps a small, fixed set of subdirs and reuses the
  existing, well-understood `__osx`/`__glibc` mechanism.
- **Reusing `linux-*` for Android.** Rejected: Bionic is not glibc, and reuse would let the solver
  violate libc requirements silently (see [Android is not Linux](#android-is-not-linux)).

## References

- [PEP 730 - Adding iOS as a supported platform][PEP 730]
- [PEP 738 - Adding Android as a supported platform][PEP 738]
- Reference implementation: conda/rattler, branch `feat/ios-android-subdirs`

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

[RFC2119]: https://www.ietf.org/rfc/rfc2119.txt
[PEP 730]: https://peps.python.org/pep-0730/
[PEP 738]: https://peps.python.org/pep-0738/
