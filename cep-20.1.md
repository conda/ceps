# A new recipe format – part 1

<table>
<tr><td> Title </td><td> A new recipe format </td>
<tr><td> Status </td><td> Proposed </td></tr>
<tr><td> Author(s) </td><td> Wolf Vollprecht &lt;wolf@prefix.dev&gt;</td></tr>
<tr><td> Created </td><td> May 23, 2023</td></tr>
<tr><td> Updated </td><td> October 20, 2023</td></tr>
<tr><td> Discussion </td><td>https://github.com/conda-incubator/ceps/pull/54</td></tr>
<tr><td> Implementation </td><td>https://github.com/prefix-dev/rattler-build</td></tr>
</table>

## Abstract

We propose a new recipe format that is heavily inspired by conda-build. The main
change is a pure YAML format without arbitrary Jinja or comments with semantic
meaning.

## Motivation

The conda-build format has grown over the years to become quite complex.
Unfortunately it has never been formally "specified" and it has grown some
features over time that make it hard to parse as straightforward YAML.

The CEP attempts to introduce a subset of the conda build format that allows for
fast parsing and building of recipes.

### History

A discussion was started on what a new recipe spec could or should look like.
The fragments of this discussion can be found here:
https://github.com/mamba-org/conda-specs/blob/master/proposed_specs/recipe.md
The reason for a new spec are:

- Make it easier to parse ("pure yaml"). conda-build uses a mix of comments and
  jinja to achieve a great deal of flexibility, but it's hard to parse the
  recipe with a computer
- iron out some inconsistencies around multiple outputs (build vs. build/script
  and more)
- remove any need for recursive parsing & solving
- cater to needs for automation and dependency tree analysis via a determinstic
  format

## Major differences with conda-build

- no full Jinja2 support: no block support `{% set ...` support, only string
  interpolation. Variables can be set in the toplevel "context" which is valid
  YAML (all new features should be native to YAML specs)
- Jinja variable syntax is changed to begin with `${{` so that it becomes valid
  YAML, e.g. `- ${{ version }}`
- Selectors use a YAML dictionary with `if / then / else` (vs. comments in
  conda-build) and are only allowed in lists (dependencies, scripts, ...). The
  syntax looks like:
  ```yaml
  - if: win
    then: this
    else: that  # optional
  ```
- for inline values, the Jinja ternary operator can be used, e.g. `number: ${{ 0
  if linux else 100 }}`

## Selectors

Selectors in the new spec are only allowed in lists and take an explicit `if /
then / else` syntax.

For example the following `script` section:

```yaml
script:
  - if: unix
    then: |
      # this is the unix script
  - if: win
    then: |
      @rem a script for batch
```

The same could have been expressed with an `else`:

```yaml
script:
  - if: unix
    then: |
      # this is the unix script
    else: |
      @rem a script for batch
```

This is a valid YAML dictionary. Selector if statements are simple boolean
expressions and follow Python syntax. The following selectors are all valid:

```
win and arm64
(osx or linux) and aarch64
something == "test"
```

If the value of a selector statement is a list, it extends the "outer" list. For
example:

```yaml
build:
  - ${{ compiler('cxx') }}
  - if: unix
    then:
      - make
      - cmake
      - pkg-config
```

evaluates for `unix == true` to a list with elements `[${{ compiler('cxx') }},
make, cmake, pkg-config]`.

### Preprocessing selectors

You can add selectors to any item, and the selector is evaluated in a
preprocessing stage. If a selector evaluates to `true`, the item is flattened
into the parent element. If a selector evaluates to `false`, the item is
removed.

```yaml
source:
  - if: not win
    then:
      # note that we omit the `-`, both is valid
      url: http://path/to/unix/source
      sha256: 01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b
    else:
      - url: http://path/to/windows/source
        sha256: 06f961b802bc46ee168555f066d28f4f0e9afdf3f88174c1ee6f9de004fc30a0
```

Because the selector is a valid Jinja expression, complicated logic is possible:

```yaml
source:
  - if: win
    then:
      url: http://path/to/windows/source
  - if: (unix and cmp(python, "2"))
    then: 
      url: http://path/to/python2/unix/source
  - if: unix and cmp(python, "3")
    then:
      url: http://path/to/python3/unix/source
```

Lists are automatically "merged" upwards, so it is possible to group multiple
items under a single selector:

```yaml
test:
  commands:
    - if: unix
      then:
        - test -d ${PREFIX}/include/xtensor
        - test -f ${PREFIX}/include/xtensor/xarray.hpp
        - test -f ${PREFIX}/lib/cmake/xtensor/xtensorConfig.cmake
        - test -f ${PREFIX}/lib/cmake/xtensor/xtensorConfigVersion.cmake
    - if: win
      then:
        - if not exist %LIBRARY_PREFIX%\include\xtensor\xarray.hpp (exit 1)
        - if not exist %LIBRARY_PREFIX%\lib\cmake\xtensor\xtensorConfig.cmake (exit 1)
        - if not exist %LIBRARY_PREFIX%\lib\cmake\xtensor\xtensorConfigVersion.cmake (exit 1)

# On unix this is rendered to:
test:
  commands:
    - test -d ${PREFIX}/include/xtensor
    - test -f ${PREFIX}/include/xtensor/xarray.hpp
    - test -f ${PREFIX}/lib/cmake/xtensor/xtensorConfig.cmake
    - test -f ${PREFIX}/lib/cmake/xtensor/xtensorConfigVersion.cmake
```

## Templating with Jinja

The spec supports simple Jinja templating in the `recipe.yaml` file.

You can set up Jinja variables in the context YAML section:

```yaml
context:
  name: "test"
  version: "5.1.2"
  major_version: ${{ version.split('.')[0] }}
```

Later in your `recipe.yaml` you can use these values in string interpolation
with Jinja. For example:

```yaml
source:
  url: https://github.com/mamba-org/${{ name }}/v${{ version }}.tar.gz
```

Jinja has built-in support for some common string manipulations.

In the new spec, complex Jinja is completely disallowed as we try to produce
YAML that is valid at all times. So you should not use any `{% if ... %}` or
similar Jinja constructs that produce invalid YAML. We also do not use the
standard Jinja delimiters (`{{ .. }}`) because that is confused by the YAML
parser as a dictionary. We follow Github Actions and others and use `${{ ... }}`
instead:

```yaml
package:
  name: {{ name }}   # WRONG: invalid yaml
  name: ${{ name }} # correct
```

Jinja functions work as usual. As an example, the `compiler` Jinja function will
look like this:

```yaml
requirements:
  build:
    - ${{ compiler('cxx') }}
```

## Shortcomings

Since we deliberately limit the amount of "Jinja" that is allowed in recipes
there will be several shortcomings.

For example, using a `{% for ... %}` loop is prohibited. After searching through
the conda-forge recipes with the Github search, we found for loops mostly used
in tests. 

In our view, for loops are a nice helper, but not necessary for many tasks: the
same functionality could be achieved in a testing script, for example. At the
same time we also plan to formalize a more powerful testing harness ([prototyped
in
boa](https://github.com/mamba-org/boa/blob/main/docs/source/recipe_spec.md#check-for-file-existence-in-the-final-package)).

This could be used instead of a for loop to check the existence of shared
libraries or header files cross-platform (instead of relying on Jinja templates
as done
[here](https://github.com/conda-forge/opencv-feedstock/blob/2fc7848655ca65419050336fe38fcfd87bec0649/recipe/meta.yaml#L131)
or
[here](https://github.com/conda-forge/boost-cpp-feedstock/blob/699cfb6ec3488da8586833b1500b69133f052b6f/recipe/meta.yaml#L53)).

Other uses of `for` loops should be relatively easy to refactor, such as
[here](https://github.com/conda-forge/libiio-feedstock/blob/1351e5846b753e4ee85624acf3a14aee4bcf321d/recipe/meta.yaml#L45-L51).

However, since the new recipe format is "pure YAML" it is very easy to create
and pre-process these files using a script, or even generating them with Python
or any other scripting language. That means, many of the features that are
currently done with Jinja could be done with a simple pre-processing step in the
future.

Another option would be to allow "full" Jinja inside the test script text blocks
(as long as it doesn't change the structure of the YAML).

## Examples

### xtensor

Original recipe [found
here](https://github.com/conda-forge/xtensor-feedstock/blob/feaa4fd8015f96038168a9d67d69eaf06a36d63f/recipe/meta.yaml).

```yaml
context:
  name: xtensor
  version: 0.24.6
  sha256: f87259b51aabafdd1183947747edfff4cff75d55375334f2e81cee6dc68ef655

package:
  name: ${{ name|lower }}
  version: ${{ version }}

source:
  fn: ${{ name }}-${{ version }}.tar.gz
  url: https://github.com/xtensor-stack/xtensor/archive/${{ version }}.tar.gz
  sha256: ${{ sha256 }}

build:
  number: 0
  # note: in the new recipe format, `skip` is a list of conditional expressions
  #       but for the "YAML format" discussion we pretend that we still use the 
  #       `skip: bool` syntax
  skip: ${{ true if (win and vc14) }}

requirements:
  build:
    - ${{ compiler('cxx') }}
    - cmake
    - if: unix
      then: make
  host:
    - xtl >=0.7,<0.8
  run:
    - xtl >=0.7,<0.8
  run_constrained:
    - xsimd >=8.0.3,<10

test:
  commands:
  - if: unix
    then:
      - test -d ${PREFIX}/include/xtensor
      - test -f ${PREFIX}/include/xtensor/xarray.hpp
      - test -f ${PREFIX}/share/cmake/xtensor/xtensorConfig.cmake
      - test -f ${PREFIX}/share/cmake/xtensor/xtensorConfigVersion.cmake
  - if: win
    then:
      - if not exist %LIBRARY_PREFIX%\include\xtensor\xarray.hpp (exit 1)
      - if not exist %LIBRARY_PREFIX%\share\cmake\xtensor\xtensorConfig.cmake (exit 1)
      - if not exist %LIBRARY_PREFIX%\share\cmake\xtensor\xtensorConfigVersion.cmake (exit 1)

about:
  home: https://github.com/xtensor-stack/xtensor
  license: BSD-3-Clause
  license_family: BSD
  license_file: LICENSE
  summary: The C++ tensor algebra library
  description: Multi dimensional arrays with broadcasting and lazy computing
  doc_url: https://xtensor.readthedocs.io
  dev_url: https://github.com/xtensor-stack/xtensor

extra:
  recipe-maintainers:
    - some-maintainer
```

