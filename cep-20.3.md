# A new recipe format – part 3 - file existence test section

<table>
<tr><td> Title </td><td> A new recipe format - file existence test section </td>
<tr><td> Status </td><td> Proposed</td></tr>
<tr><td> Author(s) </td><td> Wolf Vollprecht &lt;wolf@prefix.dev&gt;</td></tr>
<tr><td> Created </td><td> June 15, 2023</td></tr>
<tr><td> Updated </td><td> June 15, 2023</td></tr>
<tr><td> Discussion </td><td>  </td></tr>
<tr><td> Implementation </td><td>https://github.com/prefix-dev/rattler-build (coming soon)</td></tr>
</table>

## Abstract

We propose a new test-section for recipes (building on top of two previous CEPs that are in discussion).
The new test section will make it easier to test for package contents in a cross-platform fashion.

See also:

- [CEP for YAML Format for new recipe](https://github.com/conda-incubator/ceps/pull/54)
- [Content definition for new recipe format, incl. new test section & outputs](https://github.com/conda-incubator/ceps/pull/56)

## Motivation

In many recipes, people use bash- or batch commands to test for file existence. This has several downsides:

- It is not guaranteed that the file is actually part of _this_ package (could come from another dependency)
- The syntax is very fragile. Few people are well-versed in cmd.exe or bash scripting.
- The files appear in different locations on Windows vs. Unix, but these locations are somewhat well-specified (so we should make sure that the files _are_ in the right place)

This is an example of the current `xtensor` recipe:

```yaml
test:
  commands:
    - test -d ${PREFIX}/include/xtensor # [unix]
    - test -f ${PREFIX}/include/xtensor/xarray.hpp # [unix]
    - test -f ${PREFIX}/share/cmake/xtensor/xtensorConfig.cmake # [unix]
    - test -f ${PREFIX}/share/cmake/xtensor/xtensorConfigVersion.cmake # [unix]
    - if not exist %LIBRARY_PREFIX%\include\xtensor\xarray.hpp (exit 1) # [win]
    - if not exist %LIBRARY_PREFIX%\share\cmake\xtensor\xtensorConfig.cmake (exit 1) # [win]
    - if not exist %LIBRARY_PREFIX%\share\cmake\xtensor\xtensorConfigVersion.cmake (exit 1) # [win]
```

## The specification

We propose a new "test" section (following the split of testing sections in this [CEP](https://github.com/conda-incubator/ceps/pull/56)) to test for package file existence.
The test are executed on the raw package contents (without installing them). That should make them very fast to execute, as well as less brittle vs. cmd.exe / bash scripts.

```yaml
package_contents:
  # checks for the existence of files inside $PREFIX or %PREFIX%
  files:
    - etc/libmamba/test.txt
    - etc/libmamba
    - etc/libmamba/*.mamba.txt # can also use globs, then _at least_ one file needs to match

  # checks for the existence of `mamba/api/__init__.py` inside of the Python site-packages directory
  # NOTE: the user can/should also use Python import checks
  site_packages:
    - mamba.api

  # looks in $PREFIX/bin/mamba for unix and %PREFIX%\Library\bin\mamba.exe on Windows
  # NOTE: the user can/should also check the `commands` and execute something like `mamba --help` to make
  #       sure things work fine
  bin:
    - mamba

  # searches for `$PREFIX/lib/libmamba.so` or `$PREFIX/lib/libmamba.dylib` on Linux or macOS,
  # on Windows for %PREFIX%\Library\lib\mamba.dll & %PREFIX%\Library\bin\mamba.lib
  lib:
    - mamba # (look for libmamba)
    - mamba_ext # (look for libmamba_ext)

  # searches for `$PREFIX/include/libmamba/mamba.hpp` on unix, and
  # on Windows for `%PREFIX%\Library\include\mamba.hpp`
  include:
    - libmamba/mamba.hpp
    - if: win
      then:
        - libmamba/windows/include.h
        - libmamba/windows/hello_world.h
```
