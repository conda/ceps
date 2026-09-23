# CEP XXXX - Subdirs and virtual packages for iOS and Android

<table>
<tr><td> Title </td><td> Subdirs and virtual packages for iOS and Android </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Wolf Vollprecht &lt;wolf@prefix.dev&gt;</td></tr>
<tr><td> Created </td><td> Jul 24, 2026</td></tr>
<tr><td> Updated </td><td> Sep 4, 2026</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/183 </td></tr>
<tr><td> Implementation </td><td> https://github.com/conda/rattler/pull/2613 </td></tr>
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
| `android-armv7l`  | `armv7l`     | `armeabi-v7a` |
| `android-64`      | `x86_64`     | `x86_64`      |
| `android-32`      | `x86`        | `x86`         |

### Virtual packages

This section extends [CEP 30](./cep-0030.md) with two new virtual packages and amends the rules
for `__unix`. The build string of `__ios` and `__android` MUST be `0`.

#### `__ios`

`__ios` MUST be present when the target subdir is `ios-*` or `iossimulator-*`, and MUST NOT be
present otherwise. Its version MUST be set to the first two numeric components of the iOS version
available in the target environment, formatted as `{major}.{minor}`, for example `13.0`. A package
requiring iOS 13.0 or newer depends on `__ios >=13.0`.

The version MUST be overridable with `CONDA_OVERRIDE_IOS` when set to a non-empty valid version
string. Without an override, an implementation MAY use a detected native version or a target version
supplied by a build tool or configuration; if neither is available, the version MUST be `0`. The
override MUST be ignored for other target subdirs.

> The iOS version can be obtained via Python's `platform.ios_ver().release` ([PEP 730]).

#### `__android`

`__android` MUST be present when the target subdir is `android-*`, and MUST NOT be present
otherwise. Its version MUST be set to the Android API level available in the target environment,
formatted as a single integer, for example `21`. A package requiring API level 21 or newer depends
on `__android >=21`.

The version MUST be overridable with `CONDA_OVERRIDE_ANDROID` when set to a non-empty valid version
string. Without an override, an implementation MAY use a detected native API level or a target API
level supplied by a build tool or configuration; if neither is available, the version MUST be `0`.
The override MUST be ignored for other target subdirs.

> The Android API level can be obtained via:
>
> - Python's `sys.getandroidapilevel()` or `platform.android_ver().api_level` ([PEP 738])
> - `getprop ro.build.version.sdk`

#### Fallback version

With the fallback version `0`, no constraint of the form `__ios >=X` or `__android >=X` can be
satisfied until the user provides an override. Packages for these platforms are commonly resolved
from a different native platform, so the fallback is expected to be hit frequently. Tools SHOULD
inform the user when the fallback is in use and how to override it, as suggested in CEP 30.

#### `__unix`

CEP 30 lists the target platforms for which `__unix` MUST be present. This CEP adds `ios-*`,
`iossimulator-*` and `android-*` to that list.

#### Other virtual packages

`__linux`, `__glibc` and `__osx` MUST NOT be present for any subdir defined by this CEP. CEP 30
already excludes `__glibc` outside `linux-*`; this CEP makes the same requirement explicit for
`__linux` and `__osx`, since iOS is not macOS and Android is not a glibc Linux platform even though
it runs a Linux kernel.

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
- **Architecture tokens follow existing subdirs, not vendor ABI names.** The `<arch>` token reuses
  the tokens conda already uses for the same architecture on other platforms: `arm64` as in
  `osx-arm64`, `aarch64` and `armv7l` as in `linux-aarch64` and `linux-armv7l`, and `64` and `32` as
  in `linux-64` and `linux-32`. Android's own ABI names (`arm64-v8a`, `armeabi-v7a`) are not used
  because they would introduce tokens that are unknown to existing tooling and would violate CEP 26.
  A future 64-bit ARM ABI variant on Android is expected to be tied to a minimum Android version,
  which `__android` can express without a new subdir.
- **32-bit Android subdirs are included.** CPython does not officially support the 32-bit Android
  ABIs ([PEP 738]), but conda channels also ship C, C++ and Rust libraries, and `armeabi-v7a` and
  `x86` remain in use on Android TV, Wear OS and low-end devices. Channels are free to not publish
  packages for these subdirs.
- **Version in a virtual package.** Encoding the minimum OS version in the subdir, as PyPI does in a
  wheel tag, would multiply the number of subdirs and move compatibility resolution out of the
  solver. `__ios` and `__android` reuse conda's existing version-compatibility mechanism.

## Rejected ideas

- **`ios-simulator-*` subdirs.** A second dash does not conform to CEP 26. The simulator variant is
  therefore folded into the OS token.
- **An `ios-64` subdir.** Apple does not provide an x86_64 iOS device ABI.
- **An `armv7a` token for 32-bit ARM Android.** Android's `armeabi-v7a` differs from the ABI of
  `linux-armv7l` in calling convention and C library, but the architecture is still ARMv7
  little-endian, and the OS token already keeps the two apart. The existing `armv7l` token is reused.
- **Target-triple subdirs.** Naming subdirs after target triples, such as `x86_64-linux-android`
  with `linux-64` as an alias for `x86_64-linux-gnu`, would distinguish Android from glibc Linux
  without a new OS token. CEP 26 already fixes the `<os>-<arch>` syntax, and build scripts that
  match `linux-*` need to be updated for Android either way, just as Python code checking
  `sys.platform == "linux"` does.
- **Using `linux-*` for Android.** Modeling Bionic as a C standard-library variant in `linux-*` would
  put incompatible binaries in the same subdir and rely on every package declaring an exact standard
  library constraint. Android also has its own userspace ABI, dynamic linker, and platform APIs, so
  it receives separate subdirs.

## Future work

The same pattern extends to other Apple platforms, for example `tvos-*`, `tvossimulator-*`,
`visionos-*` and `visionossimulator-*`, together with matching virtual packages. They are out of
scope for this CEP.

## References

- [PEP 730 - Adding iOS as a supported platform][PEP 730]
- [PEP 738 - Adding Android as a supported platform][PEP 738]
- Reference implementation: [conda/rattler#2613](https://github.com/conda/rattler/pull/2613)

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

[RFC2119]: https://www.ietf.org/rfc/rfc2119.txt
[PEP 730]: https://peps.python.org/pep-0730/
[PEP 738]: https://peps.python.org/pep-0738/
