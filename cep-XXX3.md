# CEP XXXX - Simplified variant selection

<table>
<tr><td> Title </td><td> Simplified variant selection </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td>
  Wolf Vollprecht &lt;w.vollprecht@gmail.com&gt;,
  Bas Zalmstra &lt;bas@prefix.dev&gt;,
  Jaime Rodríguez-Guerra &lt;jaime.rogue@gmail.com&gt;
</td></tr>
<tr><td> Created </td><td> Feb 5, 2025</td></tr>
<tr><td> Updated </td><td> Mar 9, 2026</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/111 </td></tr>
<tr><td> Implementation </td><td> TBD </td></tr>
<tr><td> Requires </td><td> https://github.com/conda/ceps/pull/146 </td></tr>
</table>

## Abstract

This CEP proposes a simplified mechanism to select package variants without relying on partial build string globbing. A package carries a list of plain string flags; a solver constraint that names a flag excludes any package that does not carry it. This mechanism involves adding a new `flags` repodata record field along with the corresponding `MatchSpec` extensions.

## Motivation

Within a channel and subdir, a conda package for a given project release may have different builds or artifacts. These are used to either correct deficiencies in the build process, or to provide different build alternatives (e.g. linking to diverse library backends). These artifacts can be distinguished by their build string, which can be matched with glob strings.

In principle, the solver is responsible for choosing the right variant for a given package version. However, the user may also want to force a particular variant to satisfy their needs. The solution so far has been to plant a special substring in the build string so it can be selected by the corresponding glob string. For example, given a package with a CPU and a GPU variant (`package-1.0-h123abc_cpu_0.conda` and `package-1.0-h453cbd_gpu_0.conda`), the GPU variant can be chosen by asking for `package=*=*gpu*`.

The problem with this approach is that it doesn't scale well for more than one "flag" per build string. What if a package needs to distinguish among more than one feature? That is, not just GPU vs CPU, but also BLAS backend, MPI or licensing?
The glob strings are not expressive enough for a single spec, so several ones need to be supplied (e.g. `package=*=*gpu*`, `package=*=*mkl*`, `package=*=*mpich*` and `package=*=*nogpl*`), resulting in complicated lookahead regexes that balloon in computational complexity.

The answer to this problem is to provide a specific field that is designed to provide such selection capabilities without the expressivity and complexity problems observed above: `flags`.

## Rationale

The chosen keyword is `flags` which makes sense as a "compile time flag". This feature is mainly relevant for compiled packages with different compile time feature selection, making `flags` a matching name.

## Specification

### Repodata record syntax

The `info/index.json` file of each conda artifact MUST support two new fields, `flags`.

The value of the `flags` field MUST be a list of non-empty strings matching the regex `^[a-z0-9_]+(:[a-z0-9_]+)?$`. We allow a _single_ `:` for `key:value` semantics.

Subsequently, the `schema_version` value MUST be bumped to `3`.

In recipes, these values MUST be supported in the `build` section of each output (i.e. sibling to `number` and `track_features`).

In recipes, it MUST be represented as a list of strings under the `build.flags = [str]` key for each package output.

### MatchSpec syntax changes

Values in the `flags` field MUST be matchable by the corresponding keyword in ``, placed in the square brackets section. Its value MUST be a string or list of strings. Each entry MUST match the regex `^[a-z0-9_]+(:[a-z0-9_]+)?$`.

Flag matching is intentionally simple: a package is excluded from consideration if it does not contain every flag listed in the `flags` constraint. A flag either matches the string exactly or the package is filtered out.

### `index.json` and `repodata_record` changes

The records gain a new `flags`:

```json
{
  "name": "foobar",
  "version": "1.2.3",
  ...,
  "flags": ["cuda", "release", "blas:mkl"],
}
```

### Changes to the `recipe.yaml` file

```yaml
build:
  string: ...
  flags: ["cuda", "blas:mkl", "release"]
```

## Examples

In practice, this would look like the following from a user perspective:

```shell
conda install 'pytorch[version=">=3.1", flags=["cuda", "blas:*"]]'
```

Any package that does not carry both the `cuda` and a flag starting with `blas:` is excluded from the candidate set. Among the remaining candidates the solver applies its normal version and build-number and variant order preference sorting.

## Rejected ideas

This proposal may remind the readers of the old `features` properties in the first iterations of conda packaging.

## Future plans

In the future we might extend the matching ergonomics of flags to include numeric values and key-value items.

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
