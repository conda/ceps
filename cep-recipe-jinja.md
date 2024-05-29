# Jinja functions in recipes

Historically, conda-recipes have relied on templating with `Jinja` for some "dynamic" functionality. For example, many recipes use the `version` of the package in multiple places (as package version, in the URL and the tests, for example). To make it easy to change recipes, Jinja has been used for some light-weight templating.

The "old" recipe format has allowed arbitrary Jinja syntax (including set, if/else or for loops). The new recipe format only allows a subset of Jinja with the goal of always producing valid YAML files. In this CEP we clarify how Jinja is used in the new recipe format, what Jinja functions are available and how variables can be set and used.

## Jinja in the new recipe format

The new recipe format uses a subset of Jinja. Specifically, only "variable" expressions are allowed (no blocks such as `set`, `for` loops, `if`/`else` blocks, ...).

A Jinja expression in the new recipe format looks like the following:

`${{ version }}`

Or if a function is involved:

`${{ compiler('c') }}`

Jinja expressions are also used in `if` statements and in the `skip` field of a recipe. In both instances, the `${{ ... }}` syntax is omitted.

E.g.:

```yaml
build:
  skip:
    - osx  # This is a Jinja expression!

requirements:
  build:
    - if: win and cuda  # This is a Jinja expression!
      then:
        - cudatoolkit
```

## Variables in the recipe

The variables that are available in the Jinja context in the recipe come from two sources: the "variant configuration" file or the "context" section of the recipe.

### The context section

The context is a dictionary at the top-level of a recipe that maps keys to scalar values. The keys can be used by accessing them as variables in the Jinja expressions. For example:

```yaml
context:
  version: "1.0.5"

package:
  version: ${{ version }}
```

Context evaluation happens from top-to-bottom. That means a later value can reference an earlier one like so:

```yaml
context:
  version: "1.0.5"
  name_and_version: "pkg_${{ version }}"
```

### Variables from variant configuration

Any variable specified in the variant configuration file can be used in a recipe by using it in a Jinja expression. For example, with a variant config like:

```yaml
cuda:
  - yes
  - no
```

This value can be used as follows, for example in an inline `if` expression:

```yaml
requirements:
  host:
    - ${{ "cudatoolkit" if cuda == "yes" }}
```

## Available Jinja functions

## The compiler function

The compiler function is used to stick together a compiler from `{lang}_compiler` and `{lang}_compiler_version`

The function looks as follows:

```yaml
${{ compiler('c') }}
```

This would pull in the c_compiler and c_compiler_version from the variant config. The compiler function suffixes `{lang}_compiler` with the `target_platform` to render to something such as:

```
gcc_linux-64 8.9
clang_osx-arm64 12
msvc_win-64 19.29
```

The function `${{ compiler("foo") }}` thus evaluates to `{foo_compiler}_{target_platform} {foo_compiler_version}`.

The variant config could look something like:

```yaml
c_compiler:
  - gcc
c_compiler_version:
  - "8.9"
cxx_compiler:
  - clang
cxx_compiler_version:
  - "12"
```

> [!NOTE]
> Default values for the `compiler` function
>
> If not further specified, the following values are used as default values:
>
> ```yaml
> linux:
>  c: gcc
>  cxx: gxx
>  fortran: gfortran
>  rust: rust
> osx:
>   c: clang
>   cxx: clangxx
>   fortran: gfortran
>   rust: rust
> win:
>   c: vs2017
>   cxx: vs2017
>   fortran: gfortran
>   rust: rust
> ```

## The `stdlib` function

The `stdlib` function works exactly as the `compiler` function.

## The `cdt` function

CDT stands for "core dependency tree" packages. These are repackaged from Centos.

The function expands to the following: 

- package-name-<cdt_name>-<cdt_arch>

Where `cdt_name` and `cdt_arch` are loaded from the variant config. If they are undefined, they default to:

- `cos6` for `cdt_name` on `x86_64` and `x86`, otherwise `cos7`
- To the `platform::arch` for `cdt_arch`, except for `x86` where it defaults to `i686`.

## The pin functions

The new recipe format has two `pin` expressions:

- `pin_compatible`
- `pin_subpackage`

Both follow the same "pinning" mechanism as described next and have the same arguments.

### Pin definition

A pin has the following arguments:

- `min_pin`: The lower bound of the dependency spec. This is expressed as a `x.x....` version where the `x` are filled in from the corresponding version of the package. For example, `x.x` would be `1.2` for a package version `1.2.3`. The resulting pin spec would look like `>=1.2` for the `min_pin` argument of `x.x` and a version of `1.2.3` for the package. If `min_pin=None` is explicitly set, no lower bound will be set. The default value for `min_pin` if it's left unspecified is `x.x.x.x.x.x`.
- `max_pin`: This defines the upper bound and follows the same `x.x` semantics but adds `+1` to the last segment. For example, `x.x` would be `1.(2 + 1)` for a package version `1.2.3`. The resulting pin spec would look like `<1.3.0a0` for the `max_pin` argument of `x.x` and a version of `1.2.3` for the package. If `max_pin=None` then no upper bound is set. The default value for `max_pin` if it's left unspecified is `x`. If a version ends with a regular numeric segment, then a `.0a0` segment is appended to the final version. If a version contains a letter in the last segment, no `.0a0` segment is appended but the letter (or string) is set to `a`.
- `exact`: This is a boolean that specifies whether the pin should be exact. It defaults to `False`. If `exact` is `True`, the `min_pin` and `max_pin` are irrelevant. We pin to a `==` version and also include the build string exactly (e.g. `==1.2.3=h1234`).
- `lower_bound`: instead of using `min_pin`, the user can pass an explicit lower bound as a version string to the Jinja function. This will be preferred over the `min_pin` argument.
- `upper_bound`: instead of using `max_pin`, the user can pass an explicit upper bound as a version string to the Jinja function. This will be preferred over the `max_pin` argument.

#### Corner cases:

If there are fewer segments in the version than in the `min_pin`, only the existing segments are used (implicit 0 padding). For example, `1.2` with a `min_pin` of `x.x.x.x` would result in `>=1.2`.

If there are more segments in the `max_pin` than in the version, `0` segments are inserted before bumping the last segment. For example, `1.2` with a `max_pin` of `x.x.x.x` would result in `<1.0.0.3.0a0`.

`max_pin` behavior:

- If the last segment is a letter, we increment the number and set the letter to `a`, e.g. `9d` with a `max_pin='x'` results in `<10a`.
- If the last segment is a number, we increment the number and append `.0a0` to prevent any alpha versions from being selected. For example: `1.2.3` with a `max_pin='x.x'` will result in `<1.3.0a0`.
- The epoch is left untouched by the `max_pin` (or `min_pin`). If the epoch is set, it will be included in the final version.
- When bumping the version with a `max_pin` the local version part is removed. For example, `1.2.3+local` with a `max_pin='x.x'` will result in `<1.3.0a0`.

#### Example

If we consider a package like `numpy-1.21.3-h123456_5` we could apply some pin expressions.

- `min_pin='x.x', max_pin='x.x'` would result in `>=1.21,<1.22.0a0`
- `min_pin='x.x.x', max_pin='x'` would result in `>=1.21.3,<2.0a0`
- `exact=True` would result in `==1.21.3=h123456_5`

The function should error if `exact` is `True` and `min_pin` or `max_pin` are set.

Given the following version `1.2.3`, we get the following results:

- default values: `min_pin='x.x.x.x.x.x', max_pin='x'` -> `>=1.2.3,<2.0a0`
- `max_pin='x.x', lower_bound='1.0'` -> `>1.0,<1.3.0a0`
- `min_pin='x.x', upper_bound='2.0'` -> `>1.2,<2.0`
- `min_pin=None, max_pin='x'` -> `<2.0a0`
- `min_pin='x.x.x.x', max_pin=None` -> `>=1.2.3`

For an input of the form: `9e` (jpeg style version)

- `min_pin='x', max_pin='x'` -> `>=9e,<10a`

For an input of the form: `1.1.1j` (openssl style version)

- `min_pin='x.x.x', max_pin='x'` -> `>=1.1.1j,<2.0a0`
- `min_pin='x.x.x', max_pin='x.x'` -> `>=1.1.1j,<1.2.0a0`
- `min_pin='x.x.x', max_pin='x.x.x'` -> `>=1.1.1j,<1.1.2a`

### The `pin_compatible` function

Pin compatible will pin the dependency to the same version as "previously" resolved in the `host` or `build` environment. This is useful to ensure that the same package is used at run time as was used at build time.

Example:

```yaml
requirements:
  host:
    - numpy
  run:
    - ${{ pin_compatible('numpy', exact=True) }}
    # or alternatives
    # - ${{ pin_compatible('numpy', min_pin='x.x.x', max_pin='x') }}
    # - ${{ pin_compatible('numpy', min_pin=None, max_pin='x') }}
    # - ${{ pin_compatible('numpy', lower_bound="1.0", max_pin='x') }}
    # - ${{ pin_compatible('numpy', lower_bound="1.0", upper_bound="2.0") }}
```

### The `pin_subpackage` function

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

For example, it can be used in the following way:

```yaml
requirements:
  - $ {{ "six" if cmp(python, "<3.8") }}
  - $ {{ "six" if cmp(python, "3.8") }}
  - $ {{ "six" if cmp(python, "==3.8") }}
  - $ {{ "six" if cmp(python, "3.8.*") }}
  - $ {{ "six" if cmp(python, ">=3.8,<3.10") }}
```

In this case the value from the `python` _variant_ is used to add or remove optional dependencies. Note that generalizes and replaces selectors from old recipes, such as `# [py38]` or `# [py3k]`.

The version comparison rules follow those of the `conda` version comparison rules.

## The `hash` variable

`${{ hash }}` is the variant hash and is useful in the build string computation. This used to be `PKG_HASH` in the old recipe format. Since the `hash` variable depends on the variant computation, it is only available in the `build.string` field and is computed after the entire variant computation is finished.

## The `env` object

The `env` object is used to retrieve environment variables and inject them into the recipe. There are two ways to do this:

- `${{ env.get("MY_ENV_VAR") }}` will return the value of the environment variable `MY_ENV_VAR` or throw an error if the environment variable is not set.
- `${{ env.get_default("MY_ENV_VAR", "default_value") }}` will return the value of the environment variable `MY_ENV_VAR` or `"default_value"` if it is not set.

You can also check for the existence of an environment variable:

- `${{ env.exists("MY_ENV_VAR") }}` will return a boolean `true` if the environment variable `MY_ENV_VAR` is set and `false` otherwise.

## Jinja filters

A feature of `jinja` is called "filters". Filters are functions that can be applied to variables in a template expression.

The syntax for a filter is `{{ variable | filter_name }}`. A filter can also take arguments, such as `... | replace('foo', 'bar')`.

The following Jinja filters are available:

- `replace`: replace a string with another string (e.g. `"{{ 'foo' | replace('oo', 'aa') }}"` will return `"faa"`)
- `lower`: convert a string to lowercase (e.g. `"{{ 'FOO' | lower }}"` will return `"foo"`)
- `upper`: convert a string to uppercase (e.g. `"{{ 'foo' | upper }}"` will return `"FOO"`)
- `int`: convert a string to an integer (e.g. `"{{ '42' | int }}"` will return `42`)

There are more filters available as [documented by MiniJinja](https://docs.rs/minijinja/latest/minijinja/filters/index.html).

> [!NOTE]
> Should we add all filters from `minijinja` to this spec? Probably ...

### Extra filters for recipes

#### The `version_to_buildstring` filter

- `${{ python | version_to_buildstring }}` converts a version from the variant to a build string (it removes the `.` character and takes only the first two elements of the version).
For example the following 

```yaml
context:
  cuda: "11.2.0"

build:
  string: ${{ hash }}_cuda${{ cuda_version | version_to_buildstring }}
```

Would evaluate to a `abc123_cuda112` (assuming the hash was `abc123`).

### Various remarks

#### Inline conditionals with Jinja

The new recipe format allows for inline conditionals with Jinja. If they are falsey, and no `else` branch exists, they will render to an empty string (which is, for example in a list or dictionary, equivalent to a YAML `null`).

When we render the recipe, we filter all values that are `null` from the YAML output. This allows us to write and parse the following easily:

```yaml
requirements:
  host:
    - ${{ "numpy" if cuda == "yes" }}
```

If `cuda` is not equal to yes, the first item of the host requirements will be empty (null) and thus filtered from the final list.

This also works for dictionary keys:

```yaml
build:
  number: ${{ 100 if cuda == "yes" }}
  # or an `else` branch can be used, of course
  number: ${{ 100 if cuda == "yes" else 0 }}
```

---

### Things to decide

- Limit the filters from Jinja to a default subset?
- Should `env` work more like Python `env`
  - `env["FOO"]` instead of `env.get("FOO")`
  - `env.get("FOO", "default")` instead of `env.get_default("FOO", "default")`
- Or should it be more like Github Actions
  - `env.FOO` instead of `env.get("FOO")`
  - `env.FOO or "default"` for default values
- Should `${{ compiler('c') }}` evaluate directly to `gcc_linux-64` or should there be an intermediate representation (as is now)
- For `pin_subpackage` it will be impossible to evaluate it directly (due to self-referential nature of the function).
