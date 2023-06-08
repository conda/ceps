<table>
    <tr><td> Title </td><td> Optional Dependencies</td>
    <tr><td> Status </td><td> Draft </td></tr>
    <tr><td> Author(s) </td><td> Travis Hathaway &lt;travis.j.hathaway@gmail.com&gt;</td></tr>
    <tr><td> Created </td><td> June 7, 2023</td></tr>
    <tr><td> Updated </td><td> June 7, 2023</td></tr>
    <tr><td> Discussion </td><td> NA </td></tr>
    <tr><td> Implementation </td><td> NA </td></tr>
</table>

[python-extras]: https://peps.python.org/pep-0508/#extras
[cargo-features]: https://doc.rust-lang.org/cargo/reference/features.html
[original-cep]: https://github.com/conda-incubator/ceps/pull/9
[conda-issue-7502]: https://github.com/conda/conda/issues/7502
[conda-issue-11053]: https://github.com/conda/conda/issues/11053
[mamba-issue-245]: https://github.com/mamba-org/boa/issues/245

## Abstract

This CEP proposes a new method for including optional dependencies when installing conda packages.
Optional dependencies are largely inspired by [Python's "extras"][python-extras] and
[Cargo's "features"][cargo-features]. When implemented, package builders will have a  way to specify
dependencies which are not required but if installed would enable different features that are
not included by default.

## Motivation

Optional dependencies as a feature has been requested for conda compatible package managers for quite
some time (e.g. [conda-7502][conda-issue-7502], [conda-11053][conda-issue-11053], and [mamba-245][mamba-issue-245]).
Adding this feature to the conda ecosystem would also give package managers greater flexibility when
instructing users how to install and use their software. For example, a package could support multiple
variants by using this methodology. If a package supported either `seaborn` or `matplotlib`,
users could specify either `seaborn` or `matplotlib` as an optional dependency.


## Specification

This section will first show how this works from the end user point of view and then talks about
how it will work for package builders. Updates to the `repodata.json` format will also be discussed.

### User point of view

When a user goes to install a package, they will specify optional dependencies with the following syntax:

```bash
# For a single optional dependency
conda install package_name[optional_a]

# For multiple optional dependencies
conda install package_name[optional_a,optional_b]
```

Optional dependencies can also be specified by using the keyword argument syntax:

```bash
# For a single optional dependency
conda install package_name[extras=optional_a]

# For multiple optional dependencies
conda install package_name[extras=optional_a,optional_b]
```

Later, when running commands like `conda list` the packages will show up as "virtual metapackages", which
look like the following:

```bash
conda list

# Name                    Version                   Build  Channel
package_name              0.1.0                h0c17e10_0  conda-forge
package_name@optional_a   0.1.0              pyhd8ed1ab_0  conda-forge
package_name@optional_b   0.1.0              pyhd8ed1ab_0  conda-forge
```

When a user wants to later remove an optional dependency, they do so by referencing
these "virtual metapackages":

```bash
conda remove package_name@optional_a
```


### Packager point of view

**TBD**


## Rationale

**TBD**


## Backwards compatibility

**TBD**


## Sample implementation

**TBD**


## FAQ

**TBD**


## Resolution

**TBD**


## References

- [Python extras][python-extras]
- [Cargo features][cargo-features]
- [First CEP for optional dependencies by @wolfv][original-cep]
- [Conda issue: "Optional groups of dependencies"][conda-issue-7502]
- [Conda issue: "ENH: More powerful syntax for build variants & optional package-extras"][conda-issue-11053]
- [Mamba issue: "[recipe-spec] Allow for arbitrary optional dependencies"][mamba-issue-245]


## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
