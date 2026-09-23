# CEP XXXX - Include support to R packages from CRAN and R-universe

<table>
<tr><td> Title </td><td> Improve support to R packages </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Raniere Gaia Costa da Silva &lt;Raniere.CostadaSilva@gesis.org&gt; </td></tr>
<tr><td> Created </td><td> Jan 29, 2026 </td></tr>
<tr><td> Updated </td><td> Jan 29, 2026 </td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/issues/148 </td></tr>
<tr><td> Implementation </td><td> N/A </td></tr>
</table>

## Abstract

Although conda is a language agnostic package, dependency, and environment management, it is primarily used by scientific Python users.
R is another popular programming language used in scientific computing with a large ecosystem of packages and strong community.
This CEP aims to improve conda bring features available to R users with parity to the features available to Python users, specially the installation of non-conda packages.

## Motivation

When a Python package is available at Python Package Index ([PyPI]) but not at a conda respository, Python users have the option to provide a `pip` section. For example, [CEP 24] illustrates this with

```yaml
name: test
channels:
  - conda-forge
dependencies:
  - numpy
  - pip:
      - scipy
```

Unfortunately, when a R package is available at the Comprehensive R Archive Network ([CRAN]) or [R-universe] but not at a conda repository, R users can only recourse to (1) install the R package as a extra step after the creation of the conda environment or (2) re-package the R package to a conda repository.
The option (1) desincorage the use of conda given that it is not fulfilling it's goal.
The option (2) it time consuming and, probably, out of reach to many R users without experience creating packagings.

[CEP 24] already allows the use of subsections in `dependencies` but the lack of a recommendation limits the implementation and adoption.

## Specification

The top-level key `dependencies` in the `environment.yml` file is aware of the new `cran` subsection that should be used to define the name of **bundled** R packages installable using R's native function `install.packages()`.

The simplest form for the new `cran` subsection is a list of `str` encoding match compatible requirements.

This new `cran` subsection can also contain dictionaries when selecting the server where the R package is available. Currently known keys include

- `pkg`, the `str` encoding match compatible requirement;
- `repos`, the list of base URL of the server to use when downloading the requirement.

## Examples

Simplest possible `environment.yml` with `cran` subsection:

```yaml
dependencies:
  - r-base
  - cran:
    - tidyverse
```

With `repos` key:

```yaml
dependencies:
  - r-base
  - cran:
    - pkg: tidyverse
      repos:
        - https://tidyverse.r-universe.dev
        - https://cloud.r-project.org
```

## Backwards Compatibility

This CEP is compatible with [CEP 24].

Users with `environment.yml` that includes the features defined in this CEP are expected to see a error message from conda clients without support to this CEP as already described in [CEP 24].

## Conclusion

In this CEP, we propose a method to allow users of conda to define dependencies from [CRAN], [R-universe] and other repositories of R packages.

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

[CEP 24]: https://github.com/conda/ceps/blob/main/cep-0024.md
[PyPI]: https://pypi.org/
[CRAN]: https://cran.r-project.org/
[R-universe]: https://r-universe.dev/