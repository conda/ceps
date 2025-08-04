# CEP XXXX - Customizable system DLL linkage checks for windows

<table>
<tr><td> Title </td><td> Customizable system DLL linkage checks for windows </td>
<tr><td> Status </td><td> Accepted </td></tr>
<tr><td> Author(s) </td><td> Isuru Fernando &lt;ifernando@openteams.com&gt;</td></tr>
<tr><td> Created </td><td> Aug 04, 2025 </td></tr>
<tr><td> Updated </td><td> Aug 04, 2025</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/xxx </td></tr>
<tr><td> Implementation </td><td> N/A </td></tr>
</table>

## Abstract

In conda build tools like conda-build/rattler-build there are postprocessing
checks to see that any executable/shared library built links to a set of
dynamic shared objects (DSOs) that satisfy some constraints. These constraints
are important to make sure that the built conda package works everywhere.

While conda-build/rattler-build allows the user on Linux/macOS to customize
the set of system DSOs, it is not so on windows. This CEP aims to provide
conda-build/rattler-build users to customize the system DSOs on windows.

## Motivation

Diving into Linux, in order for a package to work in another user's environment,
we require certain constraints on the DSOs. For eg: we require minimum version
of GLIBC provided `libc.so.6`, `libm.so.6` etc on the user system for Linux users
as these are not provided by conda. We require any non-system DSO to be
in the environment in a place where the dynamic loader will know how to load,
i.e. on the rpath of the executable/shared library that requires the DSO.

The constraints for the DSOs currently in conda-build/rattler-build are,

For Linux

1. If the DSO was in the specified host environment locations ($PREFIX/<rpath>
   where <rpath>s are listed in `build/rpath`), the DSO has to be in `run` as
   well; either in the same package or a dependent conda package.

2. If the DSO was in a sysroot ($BUILD_PREFIX/*/sysroot), then these are system
   DLLs and are allowed. These DSOs usually come from `sysroot_<subdir>`
   conda packages.

For macOS,

1. If the DSO was in the specified host environment locations ($PREFIX/<rpath>
   where <rpath>s are listed in `build/rpath`), the DSO has to be in `run` as
   well; either in the same package or a dependent conda package.

2. If the DSO was in CONDA_BUILD_SYSROOT (the macOS SDK), then these are system
   DSOs and are allowed.

For windows

1. If the DSO was in the specified host environment locations ($PREFIX/Scripts,
   $PREFIX/Library/bin, $PREFIX/bin, etc), the DSO has to be in `run` as
   well; either in the same package or a dependent conda package.

2. If the DSO was in CONDA_BUILD_SYSROOT (this is unset in most scenarios), then   these are system DSOs and are allowed

3. If the DSO was in C:\Windows\System32, then these are system DSOs and are
   allowed.

4. If the DSO was in DEFAULT_WIN_WHITELIST defined by conda-build/rattler-build,
   then these are system DSOs and are allowed.

Note that for Linux and macOS, the user has a way of controlling which system
DSOs are allowed. On Linux, a user can modify the `sysroot_linux-*` package
and on macOS, the user can specify a custom macOS SDK using `CONDA_BUILD_SYSROOT`.
However, the user has no way of controlling which system DSO are allowed
on windows.

### Need for customizability of system DLLs

A user of conda-build/rattler-build might need to customize the set of system DLLs.
An example from Linux is

  [Removal of libnsl from glibc](https://github.com/conda-forge/linux-sysroot-feedstock/pull/40)

In this case newer versions of glibc dropped libnsl and made it a separate package,
therefore conda-forge dropped it from `sysroot_linux-*` packages to make sure
when new conda packages links to libnsl system DLL, conda-build/rattler-build will
warn/error out.

An example for Windows is,

  [Warn when linking to debug VC runtimes](https://github.com/conda/conda-build/issues/5732)

In this case, on the CI machines we have the debug VC runtime DLLs and are
considered system DLLs by conda-build/rattler-build, but these debug DLLs
are not always found in user systems. Also, linking to these debug DLLs
are not desirable and therefore we do not ship it in our `vc14_runtime`
conda package. Therefore we need a way to tell conda-build/rattler-build
on which DLLs are desirable and which are not.

## Specification

In this CEP, it is proposed that we allow a user to control the allowed
system DLLs on windows. When a file exists in the following locations
we use those list of files:

   <BUILD_PREFIX>/etc/conda-build/(allow|deny)list.d/<subdir>/<conda-package-name>.txt

   <PREFIX>/etc/conda-build/(allow|deny)list.d/<subdir>/<conda-package-name>.txt

When no allow list is available, but only a deny list is available, a default

   C:\Windows\System32\*.dll

is assumed. When no deny list is available and an allow list is available,
an empty deny list is assumed. When neither are available,
conda-build/rattler-build should fall back to the current method.

Each list supports globbing syntax, i.e., following is allowed.

   C:\Windows\System32\*.dll
   C:\foo.dll
   **\R.dll

## Conclusion

In this CEP, we propose a method to allow users of conda-build/rattler-build
to control the allowed system DLLs on windows, making windows have feature
parity with Linux and macOS.
