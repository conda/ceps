# CEP XX: New repodata and matchspec features

| Title          | A short title of the proposal                                                                                                                                        |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Status         | Draft                                                                                                                                                                |
| Author(s)      | Wolf Vollprecht <w.vollprecht@gmail.com>                                                                                                                             |
| Created        | 2025-02-05T12:10:51Z                                                                                                                                                 |
| Updated        | 2025-02-05T12:10:58Z                                                                                                                                                 |
| Discussion     | link to the PR where the CEP is being discussed, NA is circulated initially                                                                                          |
| Implementation | Flags: https://github.com/conda/rattler/pull/1040, Optional: https://github.com/conda/rattler/pull/1019, Conditional: https://github.com/prefix-dev/resolvo/pull/101  |


The conda ecosystem finds and resolves packages based on "repodata" - the main index metadata for all artifacts in the condaverse.

Repodata has been a stable format for a long time now. It generally consists of at least the following fields:

```yaml
name: name of the package
version: version of the package
build_string: build string of the package
build_number: build number of the package
depends: [MatchSpec] dependencies of the package, expressed as "triplet" matchspec
constrains: [MatchSpec] constraints that the package adds to the resolution aka optional dependencies
```

All other fields are mostly for metadata purposes and not listed.

With this CEP we would like to add 3 new fields to a proposed "repodata.v2" format.

The fields serve three different purposes:

- `extras`: optional dependency sets as known from the PyPI world. For examples, `sqlalchemy` might be a small base package that defines a number of extras such as `mysql`, `postgres`, `sqlite` that would pull in dependency sets as needed
- `conditional` dependencies, also widely known from the Python world. These are activated only when the condition is true. For example, certain dependencies such as `pywin32` are only relevant on Windows and not on macOS or Linux.
- `flags` are used to make it easier to select variants. Compiled packages can often be compiled with different options which results in different variants (for example, Debug vs. Release builds). With `flags` it will be trivial to select the preferred build with a syntax such as `foobar[flags=['release']]`. Flags are free-form and can be used by distributions such as conda-forge to differentiate between gpu and non-gpu builds as well.

## Extra dependency sets

We want to define a new `extras` key in `RepoData`. The key will be a dictionary mapping from String to list of MatchSpecs:

```yaml
name: sqlalchemy
version: 1.0.0
depends:
 - python >=3.8
extras:
  sqlite:
    - sqlite >=1.5
    - py-sqlite-adapter 1.0
  postgres:
    - postgres >=3.5
    - pyxpgres >=8
```

When a user, or a dependency, selects an extra through a MatchSpec, the extra and it's dependencies are "activated". This is conceptually the same as having three packages with "exact" dependencies from the "extra" to the base package: `sqlalchemy`, `sqlalchemy-sqlite` and `sqlalchemy-postgres` – which is the workaround currently employed by a number of packages on conda-forge.

## Conditional dependencies

Conditional dependencies are activated when the condition is true. The most straight-forward conditions are `__unix`, `__win` and other platform specifiers. However, we would also like to support matchspecs in conditions such as `python >=3`.

The proposed syntax is:

```yaml
name: sqlalchemy
version: 1.0.0
depends:
 - python >=3.8
 - pywin32; if __win
 - six; if python <3.8
```

The proposed syntax is to extend the `MatchSpec` syntax by appending `; if <CONDITION>` after the current MatchSpec.

We would like to also allow for AND and OR with the following syntax:

```
...; if python <3.8 and numpy >=2.0
...; if python >=3.8 or pypy
```

Note: the proposed functionality is already done in less elegant ways by creating multiple noarch packages with `__unix` or `__win` dependencies in the conda-forge distribution. Similarly this behavior will be conceptually similar as building multiple variants for a given package.

## Flags for the repodata

It's very natural to build different variants for a given package in the conda ecosystem with different properties: blas implementation, gpu / cuda version, and other variables make up the variant matrix for certain recipes.

However, it is not easy to specify which variant a user really wants in conda today. Most of the time, some string-matching on the build string is used to select one of the options, such as `pytorch 2.5.* *cuda`.

There are other workarounds by using `mutex` packages and constraining them such as `blas_impl * mkl` which could be used to select only packages that also depend on the MKL build.

However, it would be nice if we could have a flexible, powerful and simple syntax to enable or disable "flags" on packages in order to select a variant.

A RepodataRecord should get a new field "flags" that is a list of strings, such as:

```yaml
name: pytorch
version: "2.5.0"
# note these flags are free-form, and distributions are free to come up
# with their own set of flags
flags: ["gpu:cuda", "blas:mkl", "archspec:4", "release"]
```

Flags can then be matched using the following little syntax:

- `release`: only packages with `release` flag are used
- `~release`: disallow packages with `release` flag
- `?release`: if release flag available, filter on it, otherwise use any other
- `gpu:*`: any flag starting with `gpu:` will be matched
- `archspec:>2`: any flag starting with `archspec:` will be matched with everything trailing interpreted as a number and matched against the comparison operator
- `?archspec:>2`: if a flag starting with `archspec:` is found, match against this, otherwise ignore

In practice, this would look like the following from a user perspective:

```shell
conda install 'pytorch[version=">=3.1", flags=["gpu:*", "?release"]]'
```

## Backwards Compatibility

The new `repodata.v2` will be served alongside the current format under `repodata.v2.json`. Older conda clients will continue using the v1 format. Packages using any of the new features will not be added to v1 of `repodata.json`.