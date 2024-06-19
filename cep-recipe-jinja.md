# A new recipe format: `jinja` functions in recipes

<table>
<tr><td> Title </td><td> A new recipe format: `jinja` functions in recipes </td>
<tr><td> Status </td><td> Open </td></tr>
<tr><td> Author(s) </td><td> Wolf Vollprecht &lt;wolf@prefix.dev&gt;</td></tr>
<tr><td> Created </td><td> Apr 12, 2024</td></tr>
<tr><td> Updated </td><td> Jun 10, 2024</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/71 </td></tr>
<tr><td> Implementation </td><td>https://github.com/prefix-dev/rattler-build</td></tr>
</table>

## Abstract

This CEP is part of the effort to strictly define a new recipe format. The previous CEPs are:

- [CEP 13: A new recipe format](https://github.com/conda/ceps/blob/main/cep-13.md)
- [CEP 14: A new recipe format: allowed keys and values](https://github.com/conda/ceps/blob/main/cep-14.md)

Historically, `conda-build` recipes have relied on templating with `Jinja` for some
"dynamic" functionality. For example, many recipes use the `version` of the
package in multiple places (as package version, in the URL and the tests, for
example). To make it easy to change recipes, Jinja has been used for some
light-weight templating.

The "old" recipe format has allowed arbitrary Jinja syntax (including set,
if/else or for loops). The new recipe format only allows a subset of Jinja with
the goal of always producing valid YAML files. In this CEP we clarify how Jinja
is used in the new recipe format, what Jinja functions are available and how
variables can be set and used.

## Jinja in the new recipe format

The new recipe format uses a subset of Jinja. Specifically, only "variable"
expressions are allowed (no blocks such as `set`, `for` loops, `if`/`else`
blocks, ...).

A Jinja expression in the new recipe format looks like the following:

`${{ version }}`

Or if a function is involved:

`${{ compiler('c') }}`

Jinja expressions are also used in `if` statements and in the `skip` field of a
recipe. In both instances, the `${{ ... }}` syntax is omitted.

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

The variables that are available in the Jinja context in the recipe come from
two sources: the "variant configuration" file or the "context" section of the
recipe.

### The context section

The context is a dictionary at the top-level of a recipe that maps keys to
scalar values. The keys can be used by accessing them as variables in the Jinja
expressions. For example:

```yaml
context:
  version: "1.0.5"

package:
  version: ${{ version }}
```

Context evaluation must happen from top-to-bottom. That means a later value can
reference an earlier one like so:

```yaml
context:
  version: "1.0.5"
  name_and_version: "pkg_${{ version | replace('.', '_') }}"  # evaluates to "pkg_1_0_5"
```

### Variables from variant configuration

Any variable specified in the variant configuration file can be used in a recipe
by using it in a Jinja expression. For example, with a variant config like:

```yaml
cuda:
  - "have_cuda"
  - "no_cuda"
```

This value can be used as follows, for example in an inline `if` expression:

```yaml
requirements:
  host:
    - ${{ "cudatoolkit" if cuda == "have_cuda" }}
```

## Available Jinja functions

### The compiler function

The compiler function is used to create a dependency spec from `{lang}_compiler`
and `{lang}_compiler_version`

The function looks as follows:

```yaml
${{ compiler('c') }}
```

This would pull in the `c_compiler` and `c_compiler_version` from the variant
config. The compiler function suffixes `{lang}_compiler` with the
`target_platform` to render to something such as:

```txt
gcc_linux-64 8.9
clang_osx-arm64 12
msvc_win-64 19.29
```

The function `${{ compiler("foo") }}` thus evaluates to
`{foo_compiler}_{target_platform} {foo_compiler_version}`.

To configure the `foo` compiler, the following variant keys can be used:

```yaml
foo_compiler: "superfoo"
foo_compiler_version: "1.2.3"

# on linux-64 this then results in
# compiler: "superfoo_linux-64 1.2.3"
```

> [!NOTE] Default values for `<lang>_compiler`
>
> The default value for the `<lang>_compiler` variable is the language that was passed in (e.g. `rust -> rust`, or `go -> go`)
> However, for `c`, `cxx`, and `fortran`, `rattler-build` and `conda-build` define the following default values:
>
> ```yaml
> linux:
>  c: gcc
>  cxx: gxx
>  fortran: gfortran
> osx:
>   c: clang
>   cxx: clangxx
>   fortran: gfortran
> win:
>   c: vs2017
>   cxx: vs2017
>   fortran: gfortran
> ```

### The `stdlib` function

The `stdlib` function works exactly as the `compiler` function, but uses the
`stdlib` keys in the variant.

For example:

```yaml
build:
  - ${{ stdlib('c) }}
```

Evaluates to the `c_stdlib` and `c_stdlib_version` from the variant config
(incl. the target platform), using the following `<lang>_stdlib` and
`<lang>_stdlib_version` keys.

The function should evaluate to `{<lang>_stdlib}_{target_platform}
<lang>_stdlib_version`.

### The `cdt` function

CDT stands for "core dependency tree" packages. These are typically repackaged
from a Linux distribution.

The function expands to the following:

- package-name-<cdt_name>-<cdt_arch>

Where `cdt_name` and `cdt_arch` are loaded from the variant config. If they are
undefined in the variant configuration, an error is raised. There are no default
values for `cdt_name` and `cdt_arch`.

### The pin functions

The new recipe format has two `pin` expressions:

- `pin_compatible`
- `pin_subpackage`

Both follow the same "pinning" mechanism as described next and have the same
arguments.

#### Pin definition

A pin has the following arguments:

- `package_name`, positional, required: The name of the package to pin.
- `lower_bound`, defaults to `x.x.x.x.x.x`: the lower bound, either as a version
  or as a "pin expression", or `None`
- `upper_bound`, defaults to `x`: the upper bound, either as a version or as a
  "pin expression" or `None`
- `exact`: a boolean that specifies whether the pin should be exact. It defaults
  to `False`. If `exact` is `True`, the `lower_bound` and `upper_bound` are
  irrelevant and should not be set.
  An exact pin must pin with the full version and build string (to a
  single package), e.g. `==version=build`.

##### Pin expressions

A pin expression is a string that contains only `x` and `.` characters. The
number of `x` characters in the expression determines the number of segments
that are used from the version.

A pin expression of `x.x` applied to a version like `1.2.3` would yield `1.2`.
The epoch and local version parts are left untouched by the pin expression:
`1!1.2.3+local` with a `x.x` pin expression would yield `1!1.2+local`.

The version used in the pin expression computation must _always_ be the version
that was determined during the run of the recipe (irrespective of setting the
lower bound to an explicit version).

##### Upper bound pin computation

When a pin expression is used for the upper bound, the last segment of the
version must be incremented, and the local version part must be removed.

- If the last segment is a letter, the number should be incremented and the
  letter set to `a`, e.g. `9d` with a `x` pin expression results in `<10a`.
- If the last segment is a number, the number should be incremented and `.0a0`
  should be appended to prevent any alpha versions from being selected. For
  example: `1.2.3` with a `x.x` pin expression should result in `<1.3.0a0`.
- The epoch is left untouched by the `max_pin` (or `min_pin`). If the epoch is
  set, it will be included in the final version. E.g. `1!1.2.3` with a
  `max_pin='x.x'` will result in `<1!1.3.0a0`.
- When bumping the version with a `max_pin` the local version part is removed.
  For example, `1.2.3+local` with a `max_pin='x.x'` will result in `<1.3.0a0`.

> [!NOTE]
>
> `conda-build` uses the `lower_bound` for the version that is used in
> the `max_pin` pinning expression. `conda-build` also ignores the `min_pin`
> expression when a `upper_bound` is used.

##### Corner cases

If there are fewer segments in the version than in the `lower_bound` pin
expression, only the existing segments are used (implicit 0 padding). For
example, `1.2` with a `lower_bound` of `x.x.x.x` would result in `>=1.2`.

If there are more segments in the `upper_bound` pin expression than in the
version, `0` segments are inserted before bumping the last segment. For example,
`1.2` with a `upper_bound` of `x.x.x.x` would result in `<1.0.0.3.0a0`.

#### Example

For example, a package like `numpy-1.21.3-h123456_5` as input to the following
pin expressions.

- `lower_bound='x.x', upper_bound='x.x'` would result in `>=1.21,<1.22.0a0`
- `lower_bound='x.x.x', max_pin='x'` would result in `>=1.21.3,<2.0a0`
- `lower_bound=None, upper_bound='x'` would result in `<2.0a0`
- `lower_bound='x.x.x.x', upper_bound=None` would result in `>=1.21.3`
- `exact=True` would result in `==1.21.3=h123456_5`

The function should error if `exact` is `True` and `min_pin` or `max_pin` are
set.

Given the following version `1.2.3`, we get the following results:

- default values: `lower_bound='x.x.x.x.x.x', upper_bound='x'` -> `>=1.2.3,<2.0a0`
- `lower_bound='1.0', upper_bound='x.x'` -> `>1.0,<1.3.0a0`
- `lower_bound='x.x', upper_bound='2.0'` -> `>1.2,<2.0`
- `lower_bound=None, upper_bound='x'` -> `<2.0a0`
- `lower_bound='x.x.x.x', upper_bound=None` -> `>=1.2.3`

For an input of the form: `9e` (jpeg style version)

- `lower_bound='x', upper_bound='x'` -> `>=9e,<10a`

For an input of the form: `1.1.1j` (openssl style version)

- `lower_bound='x.x.x', upper_bound='x'` -> `>=1.1.1j,<2.0a0`
- `lower_bound='x.x.x', upper_bound='x.x'` -> `>=1.1.1j,<1.2.0a0`
- `lower_bound='x.x.x', upper_bound='x.x.x'` -> `>=1.1.1j,<1.1.2a`

### The `pin_compatible` function

Pin compatible will pin the dependency to the same version as "previously"
resolved in the `host` or `build` environment. This is useful to ensure that the
same package is used at run time as was used at build time.

Example:

```yaml
requirements:
  host:
    - numpy
  run:
    - ${{ pin_compatible('numpy', exact=True) }}
    # or alternatives
    # - ${{ pin_compatible('numpy', lower_bound='x.x.x', upper_bound='x') }}
    # - ${{ pin_compatible('numpy', lower_bound=None, upper_bound='x') }}
    # - ${{ pin_compatible('numpy', lower_bound="1.0", upper_bound='x') }}
    # - ${{ pin_compatible('numpy', lower_bound="1.0", upper_bound="2.0") }}
```

### The `pin_subpackage` function

Pin subpackage will pin the dependency to the same version as another
sub-package from the recipe (or the current package itself). This is useful to
ensure that multiple outputs from a recipe are linked together or to export the
correct `run_exports` for a package.

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

### The `match` function

The `match` function is used to match a variant with a version spec. It returns
`true` if the version spec matches the variant and `false` otherwise.

For example, it can be used in the following way:

```yaml
requirements:
  - $ {{ "six" if match(python, "<3.8") }}
  - $ {{ "six" if match(python, "3.8") }}
  - $ {{ "six" if match(python, "==3.8") }}
  - $ {{ "six" if match(python, "3.8.*") }}
  - $ {{ "six" if match(python, ">=3.8,<3.10") }}
```

In this case the value from the `python` _variant_ is used to add or remove
optional dependencies. Note that generalizes and replaces selectors from old
recipes, such as `# [py38]` or `# [py3k]`.

The version comparison rules follow those of the `conda` version comparison
rules.

## The `hash` variable

`${{ hash }}` is the variant hash and is useful in the build string computation.
This used to be `PKG_HASH` in the old recipe format. Since the `hash` variable
depends on the variant computation, it is only available in the `build.string`
field and is computed after the entire variant computation is finished.

## The `env` object

The `env` object is used to retrieve environment variables and inject them into
the recipe. There are two ways to do this:

- `${{ env.get("MY_ENV_VAR") }}` will return the value of the environment
  variable `MY_ENV_VAR` or throw an error if the environment variable is not
  set.
- `${{ env.get("MY_ENV_VAR", default="default_value") }}` will return the value
  of the environment variable `MY_ENV_VAR` or `"default_value"` if it is unset.

You can also check for the existence of an environment variable:

- `${{ env.exists("MY_ENV_VAR") }}` will return a boolean `true` if the
  environment variable `MY_ENV_VAR` is set and `false` otherwise.

## Jinja filters

A feature of `jinja` is called "filters". Filters are functions that can be
applied to variables in a template expression.

The syntax for a filter is `{{ variable | filter_name }}`. A filter can also
take arguments, such as `... | replace('foo', 'bar')`.

The following Jinja filters are available, taken from the upstream `minijinja`
library:

- `replace`: replace a string with another string (e.g. `"{{ 'foo' | replace('oo', 'aa') }}"` will return `"faa"`)
- `lower`: convert a string to lowercase (e.g. `"{{ 'FOO' | lower }}"` will return `"foo"`)
- `upper`: convert a string to uppercase (e.g. `"{{ 'foo' | upper }}"` will
return `"FOO"`) - `int`: convert a string to an integer (e.g. `"{{ '42' | int }}"` will return `42`)
- `abs`: return the absolute value of a number (e.g. `"{{ -42 | abs }}"` will return `42`)
- `bool`: convert a value to a boolean (e.g. `"{{ 'foo' | bool }}"` will return `true`)
- `default`: return a default value if the value is falsy (e.g. `"{{ '' | default('foo') }}"` will return `"foo"`)
- `first`: return the first element of a list (e.g. `"{{ [1, 2, 3] | first }}"`
will return `1`) - `last`: return the last element of a list (e.g. `"{{ [1, 2, 3] | last }}"` will return `3`)
- `length`: return the length of a list (e.g. `"{{ [1, 2, 3] | length }}"` will return `3`)
- `list`: convert a string to a list (e.g. `"{{ 'foo' | list }}"` will return `['f', 'o', 'o']`)
- `join`: join a list with a separator (e.g. `"{{ [1, 2, 3] | join('.') }}"` will return `"1.2.3"`)
- `min`: return the minimum value of a list (e.g. `"{{ [1, 2, 3] | min }}"` will return `1`)
- `max`: return the maximum value of a list (e.g. `"{{ [1, 2, 3] | max }}"` will return `3`)
- `reverse`: reverse a list (e.g. `"{{ [1, 2, 3] | reverse }}"` will return `[3, 2, 1]`)
- `slice`: slice a list (e.g. `"{{ [1, 2, 3] | slice(1, 2) }}"` will return `[2]`)
- `batch`: This filter works pretty much like `slice` just the other way round.
  It returns a list of lists with the given number of items. If you provide a
  second parameter this is used to fill up missing items.
- `sort`: sort a list (e.g. `"{{ [3, 1, 2] | sort }}"` will return `[1, 2, 3]`)
- `trim`: remove leading and trailing whitespace from a string (e.g. `"{{ ' foo ' | trim }}"` will return `"foo"`)
- `unique`: remove duplicates from a list (e.g. `"{{ [1, 2, 1, 3] | unique }}"` will return `[1, 2, 3]`)
- `split`: split a string into a list (e.g. `"{{ '1.2.3' | split('.') }}"` will return `['1', '2', '3']`). By default, splits on whitespace.

<details>
<summary>Removed filters</summary>
The following filters are removed from the builtins:

- `attr`
- `indent` (indent with spaces, could be useful?)
- `select`
- `selectattr`
- `dictsort`
- `reject`
- `rejectattr`
- `round`
- `map`
- `title`
- `capitalize`
- `urlencode`
- `escape`
- `pprint`
- `safe`
- `items`
- `float`
- `tojson`
</details>

### Extra filters for recipes

#### The `version_to_buildstring` filter

- `${{ python | version_to_buildstring }}` converts a version from the variant
  to a build string (it removes the `.` character and takes only the first two
  elements of the version).

For example the following:

```yaml
context:
  cuda: "11.2.0"

build:
  string: ${{ hash }}_cuda${{ cuda_version | version_to_buildstring }}
```

Would evaluate to a `abc123_cuda112` (assuming the hash was `abc123`).

### Various remarks

#### Inline conditionals with Jinja

The new recipe format allows for inline conditionals with Jinja. If they are
falsey, and no `else` branch exists, they will render to an empty string (which
is, for example in a list or dictionary, equivalent to a YAML `null`).

When a recipe is rendered, all values that are `null` must be filtered from the
resulting YAML.

```yaml
requirements:
  host:
    - ${{ "numpy" if cuda == "yes" }}
```

If `cuda` is not equal to yes, the first item of the host requirements will be
empty (null) and thus filtered from the final list.

This must also work for dictionary values. For example:

```yaml
build:
  number: ${{ 100 if cuda == "yes" }}
  # or an `else` branch can be used, of course
  number: ${{ 100 if cuda == "yes" else 0 }}
```

## Error handling

Build tools should be aggressive about Jinja errors:

- Undefined variables should always be an error. To workaround, the user should use the `default` filter (e.g. `${{ foo | default("bla") }}`).
- Unknown functions should always be an error.
- Syntax errors should always be an error.
