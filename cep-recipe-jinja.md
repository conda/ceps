# Jinja functions in recipes

The new recipe format has some Jinja functionalities. We want to specify what functions exist and their expected behavior.

## The compiler function

The compiler function is used to stick together a compiler from {lang}_compiler and {lang}_compiler_version

The function looks as follows:

```yaml
${{ compiler('c') }}
```

This would pull in the c_compiler and c_compiler_version from the variant config. The compiler function also adds the target_platform to render to something such as:

```
gcc_linux-64 8.9
clang_osx-arm64 12
msvc_win-64 19.29
```

The function thus evaluates to `{compiler}_{target_platform} {compiler_version}`.

The variant config could look something like:

```
c_compiler:
  - gcc
c_compiler_version:
  - "8.9"
cxx_compiler:
  - clang
cxx_compiler_version:
  - "12"
```

## The `cdt` function

CDT stands for "core dependency tree" packages. These are repackaged from Centos.

The function expands to the following: 

- package-name-<cdt_name>-<cdt_arch>

Where `cdt_name` and `cdt_arch` are loaded from the variant config. If they are undefined, they default to:

- `cos6` for `cdt_name` on `x86_64` and `x86`, otherwise `cos7`
- To the `platform::arch` for `cdt_arch`, except for `x86` where it defaults to `i686`.

## The `pin_subpackage` function

### Pin definition

A pin has the following arguments:

- `min_pin`: The lower bound of the dependency spec. This is expressed as a `x.x....` version where the `x` are filled in from the corresponding version of the package. For example, `x.x` would be `1.2` for a package version `1.2.3`. The resulting pin spec would look like `>=1.2` for the `min_pin` argument of `x.x` and a version of `1.2.3` for the package.
- `max_pin`: This defines the upper bound and follows the same `x.x` semantics but adds `+1` to the last segment. For example, `x.x` would be `1.(2 + 1)` for a package version `1.2.3`. The resulting pin spec would look like `<1.3` for the `max_pin` argument of `x.x` and a version of `1.2.3` for the package.
- `exact`: This is a boolean that specifies whether the pin should be exact. It defaults to `False`. If `exact` is `True`, the `min_pin` and `max_pin` are irrelevant. We pin to an `==` version and also include the build string exactly (e.g. `==1.2.3=h1234`).

#### Example

If we consider a package like `numpy-1.21.3-h123456_5` we could apply some pin expressions. 

- `min_pin=x.x, max_pin=x.x` would result in `>=1.21,<1.22`
- `min_pin=x.x.x,max_pin=x` would result in `>=1.21.3,<2`
- `exact=True` would result in `==1.21.3=h123456_5`


## The `pin_compatible` function

Pin compatible will pin the dependency to the same version as "previously" resolved in the `host` or `build` environment. This is useful to ensure that the same package is used at run time as was used at build time.

Example:

```yaml
requirements:
  host:
    - numpy
  run:
    - ${{ pin_compatible('numpy', exact=True) }}
```

## The `pin_subpackage` function

Pin subpackage will pin the dependency to the same version as another sub-package from the recipe (or the current package itself).
This is useful to ensure that multiple outputs from a recipe are linked together or to export the correct `run_exports` for a package.

Example:

```yaml
outputs:
  - package:
      name: libfoo
      version: "1.2.3"
  - package:
      name: foo
      version: "1.2.3"
    requirements:
      run:
        - ${{ pin_subpackage('libfoo', exact=True) }}
```

## The `cmp` function

The `cmp` function is used to compare two versions. It returns `True` if the comparison is true and `False` otherwise.

## The `hash` variable

`${{ hash }}` is the variant hash and is useful in the build string computation. This used to be `PKG_HASH` in the old recipe format. Since the `hash` variable depends on the variant computation, it is only available in the `build.string` field and is computed after the entire variant computation is finished.

## The `version_to_buildstring` function

- `${{ python | version_to_buildstring }}` converts a version from the variant to a build string (it removes the `.` character and takes only the first two elements of the version).

## The `env` object

You can use the `env` object to retrieve environment variables and forward them to your build script. There are two ways to do this:

- `${{ env.get("MY_ENV_VAR") }}` will return the value of the environment variable `MY_ENV_VAR` or throw an error if it is not set.
- `${{ env.get_default("MY_ENV_VAR", "default_value") }}` will return the value of the environment variable `MY_ENV_VAR` or `"default_value"` if it is not set.

You can also check for the existence of an environment variable:

- `${{ env.exists("MY_ENV_VAR") }}` will return `true` if the environment variable `MY_ENV_VAR` is set and `false` otherwise.
