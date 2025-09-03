# CEP XXXX - Customizable system DLL linkage checks for windows

<table>
<tr><td> Title </td><td> Customizable system DLL linkage checks for windows </td>
<tr><td> Status </td><td> Accepted </td></tr>
<tr><td> Author(s) </td><td> Isuru Fernando &lt;ifernando@openteams.com&gt;</td></tr>
<tr><td> Created </td><td> Aug 04, 2025 </td></tr>
<tr><td> Updated </td><td> Aug 04, 2025</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/128 </td></tr>
<tr><td> Implementation </td><td> N/A </td></tr>
</table>

## Abstract

In conda build tools like `conda-build` or `rattler-build` there are postprocessing
checks to see that any executable/shared library built links to a set of
dynamic shared objects (DSOs) that satisfy some constraints. These constraints
are important to make sure that the built conda package works everywhere.

While conda build tools allow the user on Linux/macOS to customize
the set of system DSOs, it is not so on Windows. This CEP aims to provide
conda build tools users with a way to customize the system DSOs on windows.

## Motivation

Diving into Linux, in order for a package to work in another user's environment,
we require certain constraints on the DSOs. For example, we require a minimum version
of the GLIBC-provided `libc.so.6`, `libm.so.6`, etc libraries on the user system
as these are not provided by conda packages. We do require any non-system DSO to be
in the environment in a place where the dynamic loader will search,
i.e. on the `rpath` of the executable/shared library that requires the DSO.

The constraints for the DSOs currently in conda build tools are:

For Linux,

1. If the DSO was in the specified host environment locations (`$PREFIX/<rpath>`,
   where `<rpath>` entries are listed in `build/rpath`), the DSO has to be installed as
   well; either as part of the same package or one of its dependencies.

2. If the DSO was in a sysroot (`$BUILD_PREFIX/*/sysroot`), then these are system
   libraries and are allowed. These DSOs usually come from `sysroot_<subdir>`
   conda packages.

For macOS,

1. If the DSO was in the specified host environment locations (`$PREFIX/<rpath>`,
   where `<rpath>` entries are listed in `build/rpath`), the DSO has to be installed as
   well; either as part of the same package or one of its dependencies.

2. If the DSO was in `CONDA_BUILD_SYSROOT` (the macOS SDK location), then these are system
   libraries and are allowed.

For Windows,

1. If the DSO was in the specified host environment locations (`$PREFIX/Scripts`,
   `$PREFIX/Library/bin`, etc), the DSO has to be installed as
   well; either as part of the same package or one of its dependencies.

2. If the DSO was in `CONDA_BUILD_SYSROOT` (this is unset in most scenarios), then   these are system libraries and are allowed.

3. If the DSO was in `C:\Windows\System32`, then these are system libraries and are
   allowed.

4. If the DSO was in the `DEFAULT_WIN_WHITELIST` location defined by the build tool,
   then these are system libraries and are allowed. `DEFAULT_WIN_WHITELIST` is a
   hardcoded constant in `conda-build` and `rattler-build`.

Note that for Linux and macOS, the user has a way of controlling which system
DSOs are allowed. On Linux, a user can modify the `sysroot_linux-*` package
and on macOS, the user can specify a custom macOS SDK using `CONDA_BUILD_SYSROOT`.
However, the user has no way of controlling which system DSOs are allowed
on Windows.

### Need for customizability of allowed Windows system libraries

A user of conda build tools might need to customize the set of system DLLs.
An example from Linux is the [removal of `libnsl` from `glibc`](https://github.com/conda-forge/linux-sysroot-feedstock/pull/40).

In this case, newer versions of `glibc` dropped `libnsl` and made it a separate package,
therefore conda-forge dropped it from `sysroot_linux-*` packages to make sure
when new conda packages link to the `libnsl` system library, the build tool will
warn or error out.

An example for Windows can be found in this issue:
[Warn when linking to debug VC runtimes](https://github.com/conda/conda-build/issues/5732).

In this case, the CI machines provide debug VC (Visual Studio) runtime DLLs and are
considered system DLLs by conda build tools, but these debug DLLs
are not always found in user systems. Also, linking to these debug DLLs
are not desirable and therefore should not be shipped it the corresponding
conda package (e.g. `vc14_runtime`). Therefore we need a way to tell the build tool
which DLLs are allowed and which are not.

## Specification

This CEP proposes a mechanism to control the allowed system DLLs on Windows.
When a JSON file provided by a conda package in `host` or `build` exists in
any of the following locations we use those list of files:

- `<BUILD_PREFIX>/etc/conda-build/dsolists.d/<conda-package-name>.json`

- `<PREFIX>/etc/conda-build/dsolists.d/<conda-package-name>.json`

The JSON file format is:

```json
{
  "version": 1,
  "allow": [str],
  "deny": [str],
  "subdir": str
}
```

Here `version` is for the version of the DSO list JSON schema and will always
be present for these files. The build tools should check the version and
validate that the `version` is a known and supported version and error out
if not. This CEP specifies `version=1` only and subsequent CEPs can revise
this format by changing the `version` key.

The elements of the two lists `allow` and `deny` supports standard POSIX
globbing syntax; i.e., the following is allowed:

```json
{
  "version": 1,
  "allow": [
    "C:/Windows/System32/*.dll",
    "**/R.dll",
  ],
  "deny": [
    "**/ucrtbased.dll",
  ],
  "subdir": "win-64",
}
```

Note that forward slashes are used for path separation and only absolute paths
are allowed. This rule should be enforced by the build tool.

When no allow list is available among all the JSON files, but only deny lists are
available, a default `C:/Windows/System32/*.dll` glob is assumed.
When no deny list is available among all the JSON files, but only allow lists are
available, an empty deny list is assumed. When neither are available,
conda build tools should fall back to the current method (as of August 2025).

When both allow lists and deny lists are available, allow lists among all the JSON
files are processed first and then deny lists are processed.

## Conclusion

In this CEP, we propose a method to allow users of conda build tools
to control the allowed system DLLs on Windows, bringing it to feature
parity with Linux and macOS.
