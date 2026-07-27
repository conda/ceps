# CEP XXXX - Subdirs and virtual packages for iOS and Android

<table>
<tr><td> Title </td><td> Subdirs and virtual packages for iOS and Android </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Wolf Vollprecht &lt;wolf@prefix.dev&gt;</td></tr>
<tr><td> Created </td><td> Jul 24, 2026</td></tr>
<tr><td> Updated </td><td> Jul 27, 2026</td></tr>
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

This CEP defines conda subdirs for packages targeting Apple's iOS and Google's Android, together
with two virtual packages, `__ios` and `__android`, for OS-version compatibility. It maps the PyPI
wheel-tag model for these platforms ([PEP 730] for iOS and [PEP 738] for Android) onto conda's
existing subdir and virtual-package machinery.

## Motivation

conda has no standard way to describe packages built for mobile operating systems. Python and the
wider native toolchain ecosystem now support iOS and Android as target platforms, and conda build
tools can produce packages for them. Common subdir and virtual-package names are needed so those
packages can be described and consumed consistently across implementations.

## Specification

### Subdirs

This CEP defines the following subdirs. As per [CEP 26](./cep-0026.md), each subdir is
single-architecture and follows the `<os>-<arch>` syntax.

#### iOS

| Subdir               | Architecture | Platform variant              |
| -------------------- | ------------ | ----------------------------- |
| `ios-arm64`          | `arm64`      | Device (`iphoneos`)           |
| `iossimulator-arm64` | `arm64`      | Simulator (`iphonesimulator`) |
| `iossimulator-64`    | `x86_64`     | Simulator (`iphonesimulator`) |

#### Android

| Subdir            | Architecture | Android ABI   |
| ----------------- | ------------ | ------------- |
| `android-aarch64` | `aarch64`    | `arm64-v8a`   |
| `android-armv7a`  | `armv7a`     | `armeabi-v7a` |
| `android-64`      | `x86_64`     | `x86_64`      |
| `android-32`      | `x86`        | `x86`         |

### Virtual packages

The following virtual packages extend [CEP 30](./cep-0030.md). Their build strings MUST be `0`.

#### `__ios`

`__ios` MUST be present when the target subdir is `ios-*` or `iossimulator-*`, and MUST NOT be
present otherwise. Its version MUST represent the iOS version available in the target environment,
for example `13.0`. A package requiring iOS 13.0 or newer depends on `__ios >=13.0`.

The version MUST be overridable with `CONDA_OVERRIDE_IOS` when set to a non-empty valid version
string. Without an override, an implementation MAY use a detected native version or a
build-tool-supplied target version; if neither is available, the version MUST be `0`. The override
MUST be ignored for other target subdirs.

#### `__android`

`__android` MUST be present when the target subdir is `android-*`, and MUST NOT be present otherwise.
Its version MUST represent the Android API level available in the target environment, for example
`21`. A package requiring API level 21 or newer depends on `__android >=21`.

The version MUST be overridable with `CONDA_OVERRIDE_ANDROID` when set to a non-empty valid version
string. Without an override, an implementation MAY use a detected native API level or a
build-tool-supplied target API level; if neither is available, the version MUST be `0`. The override
MUST be ignored for other target subdirs.

The `__unix` virtual package MUST be present for every subdir defined by this CEP.

## Rationale

- **Separate iOS device and simulator subdirs.** iOS provides one API but two incompatible ABIs:
  `iphoneos` for devices and `iphonesimulator` for simulators. Even when both use `arm64`, a binary
  built for one cannot run on the other, and a fat binary cannot span the two ABIs. The existing
  `osx-*` subdirs are also unsuitable because iOS and macOS have significant platform differences
  despite both using the Darwin kernel.
- **No separate iPadOS subdirs.** iPadOS is not distinct from iOS for development purposes. Binaries
  built for the `iphoneos` and `iphonesimulator` ABIs can also be deployed to iPads.
- **The `ios` and `iossimulator` OS tokens.** Apple's `iphoneos` and `iphonesimulator` names identify
  vendor ABIs. The conda token identifies the operating system, so `ios` follows CPython's platform
  name and includes iPads. The `simulator` suffix records the ABI split without implying an
  iPhone-only target.
- **Version in a virtual package.** Encoding the minimum OS version in the subdir, as PyPI does in a
  wheel tag, would multiply the number of subdirs and move compatibility resolution out of the
  solver. `__ios` and `__android` reuse conda's existing version-compatibility mechanism.

## Rejected ideas

- **`ios-simulator-*` subdirs.** A second dash does not conform to CEP 26. The simulator variant is
  therefore folded into the OS token.
- **An `ios-64` subdir.** Apple does not provide an x86_64 iOS device ABI.
- **Using `armv7l` for Android.** Android's `armeabi-v7a` uses the softfp calling convention and
  Bionic, unlike the ABI represented by `linux-armv7l`. The `armv7a` token keeps these incompatible
  targets distinct.
- **Using `linux-*` for Android.** Modeling Bionic as a C standard-library variant in `linux-*` would
  put incompatible binaries in the same subdir and rely on every package declaring an exact standard
  library constraint. Android also has its own userspace ABI, dynamic linker, and platform APIs, so
  it receives separate subdirs.

## References

- [PEP 730 - Adding iOS as a supported platform][PEP 730]
- [PEP 738 - Adding Android as a supported platform][PEP 738]
- Reference implementation: conda/rattler, branch `feat/ios-android-subdirs`

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

[RFC2119]: https://www.ietf.org/rfc/rfc2119.txt
[PEP 730]: https://peps.python.org/pep-0730/
[PEP 738]: https://peps.python.org/pep-0738/
