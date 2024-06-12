# A new recipe format – part 5 - tests defined in the recipe

<table>
<tr><td> Title </td><td> A new recipe format – part 5 - tests defined in the recipe </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Wolf Vollprecht &lt;wolf@prefix.dev&gt;</td></tr>
<tr><td> Created </td><td> Jun 12, 2024</td></tr>
<tr><td> Updated </td><td> Jun 12, 2024</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda-incubator/ceps/pull/?? </td></tr>
<tr><td> Implementation </td><td>https://github.com/prefix-dev/rattler-build</td></tr>
</table>

## Abstract

Testing is an important part of the packaging workflow - the goal is to make sure that packages
work correctly and package the files they are supposed to contain.

In the CEP we want to clearly define how tests can be declared in the `recipe.yaml` file and how they
are stored in the final package.

## Tests definition

With the exception of the package content tests, this is a recap of the previous CEPs (CEP 14).

The recipes can contain a `tests` section that is a list of individual tests that should be executed by the package build program after the package is built.

```yaml
tests:
  - script: # following the script definition in the CEP-14
      - echo "Hello World"
    requirements:
      build: # [MatchSpec]
        - ${{ "qemu" if target_platform != build_platform }}
      run: # [MatchSpec]
        - python
        - pytest # match spec
    files:
      # files to be copied to the package for test execution
      source:    # GlobVec
        - tests/**
    # Additional files from the recipe directory
    #   recipe:
    #     - ...
  - python:
      imports: # [string]
        - foo # python imports to test
      pip_check: true # bool
  - package_contents:
      include: # [list of globs]
        - foo.h
        - foo.hpp
        - foo/*.hpp
  - downstream: bar # string
```

For `script`, `python` and `downstream` tests, please refer to CEP-14.
The `package_contents` test is a new test type that runs before package creation and checks if the files listed are present (or not present) in the package.

## Test rendering to the final package

Tests should be shipped as part of the package in order to facilitate running tests outside of the package build execution, and as part of e.g. downstream tests.

For this reason, tests should be rendered as part of the package. However, the rendered tests should still contain the original test definition including the un-evaluated Jinja selectors and if/else sections - in order to facilitate running tests in cross-compilation settings.

A build tool SHOULD render the list of tests into a JSON file in the `info/` folder of the package. The file should be named `tests.json`. It should contain a list of dictionaries, where each dictionary is a test definition.

- Any Jinja or conditionals should be kept in-tact and evaluated at runtime. (Question: should the list of tests be filtered? Should we introduce a `skip` key instead?)
- The package content tests are filtered
- The source files for the command tests are copied into the `/etc/conda/test-files/<package-identifier>/<index>/` folder and referenced from the `tests.json` file. This is done in order to keep the `info`-folder small for cases when only metadata is requested.

```js
[
  {
    script: ['echo "Hello World"'],
    requirements: {
      build: ["${{ 'qemu' if target_platform != build_platform }}"],
      run: ["python", "pytest", { if: "win", then: "pytest-windows" }],
    },
  },
  {
    python: {
      imports: ["foo"],
      pip_check: true,
    },
  },
  {
    downstream: "bar",
  },
];
```

### Test execution

#### Script test

A script test SHOULD create the `run` and `build` environment. The `build` environment SHOULD be in the architecture of the current platform. The `run` environment SHOULD be in the architecture of the target platform (ie. the platform the package is intended to run on).

The `build` environment SHOULD be stacked on top of the `run` environment (ie. the PATH entries of the `build` environment take precedence).
The script MUST be executed with the current work dir set to a copy of of the folder of files copied for the test (ie. the `$PREFIX/etc/conda/test-files/<package-identifier>/<id>/` folder).

## Package contents test

A list of `globs` is used to check for the presence (or absence) of files in the package.

The full definition of a package content test is given below:

```yaml
package_contents:
  strict: bool
  include: TestGlobVec
  lib: TestGlobVec
  bin: TestGlobVec
  files: TestGlobVec
  site_packages: TestGlobVec
```

Where the `TestGlobVec` is defined as follows: either a single glob, a list of globs or a dictionary with `exists` and `not_exists` keys, where the values are list of globs.

For example:

```yaml
package_contents:
  include:
    - foo.h
    - foo.hpp
    - foo/*.hpp
  lib:
    exists:
      - libfoo.so
    not_exists:
      - libbar.so
```

This test would check if the files `foo.h`, `foo.hpp` and any files matching `*.hpp` files are present in the package.
It would also check if `libfoo.so` is present and `libbar.so` is not present in the package.

### The `strict` flag

If the strict flag is set, all files included in the package MUST be matched by at least one glob.

### The `lib` section

The `lib` section will look in the `$PREFIX/lib` or `$PREFIX/Library/lib` (on Windows) folder.
A simple library name MUST be checked in multiple ways (e.g. `foo`) - inspired by CMake `find_library` command.

#### Windows

Libraries are expected to be found in both .dll and .lib formats.
Special handling is required for .dll files, which must be accompanied by a corresponding .bin file.

If the path extension of the glob is `.dll` or `lib`, we search for

- glob ends with `.dll`: `Library/bin/{glob}`
- glob ends with `.lib`: `Library/lib/{glob}`

If no extension is given, the dll/lib must be search in:

- `Library/bin/{glob}.dll`
- `Library/lib/{glob}.lib`

#### MacOS

On macOS the base directory that must be searched for libraries is `lib/`.
If the glob does not include `.a` or `.dylib`, the following variations are tried:

- `lib/{,lib}{glob}.dylib` (matches `foo.dylib`, `libfoo.dylib`)
- `lib/{,lib}{glob}.*.dylib` (matches `foo.1.dylib`, `libfoo.1.dylib`)

If the glob ends with `.a` or `.dylib`, the following variations are tried:

- `lib/{glob}`

#### Linux and WebAssembly

On Linux and WebAssembly the base directory that must be searched for libraries is `lib/`.
If the glob does not end with `.a` or `.so` and does not contain `.so.`, the following variations are tried:

- `lib/{,lib}{glob}.so` (matches `foo.so`, `libfoo.so`)
- `lib/{,lib}{glob}.so.*` (matches `foo.so.1`, `libfoo.so.1`)

Otherwise, the following variations are tried:

- `lib/{glob}`

### The `bin` section

The `bin` section will look in the `$PREFIX/bin` folder on macOS, Linux and WebAssembly.

On Windows, the build tool must search under the following folders, with the following extensions.
If a file extension is explictly given, only that extension is searched for.

- extensions: `.exe`, `.bat`, `.com`, `.cmd`, `.ps1`
- folders:
  - `bin`
  - `Scripts`
  - `Library/bin`
  - `Library/usr/bin`
  - `Library/mingw-w64/bin`

For example, `foo` would match `Library/bin/foo.exe`.

### The `include` section

Globs in the include section should match files in the `$PREFIX/include` or `$PREFIX/Library/include` (on Windows) folder.
If no file extension is supplied, `.h` and `.hpp` files must be matched.
