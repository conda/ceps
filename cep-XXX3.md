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

This CEP proposes a simplified mechanism to select package variants without relying on partial build string globbing. Instead, a concrete keyword-matching strategy is devised to allow for more targeted granularity. This mechanism involves adding a new `flags` repodata record field along with the corresponding `MatchSpec` extensions.

## Motivation

Within a channel and subdir, a conda package for a given project release may have different builds or artifacts. These are used to either correct deficiencies in the build process, or to provide different build alternatives (e.g. linking to diverse library backends). These artifacts can be distinguished by their build string, which can be matched with glob strings.

In principle, the solver is responsible for choosing the right variant for a given package version. However, the user may also want to force a particular variant to satisfy their needs. The solution so far has been to plant a special substring in the build string so it can be selected by the corresponding glob string. For example, given a package with a CPU and a GPU variant (`package-1.0-h123abc_cpu_0.conda` and `package-1.0-h453cbd_gpu_0.conda`), the GPU variant can be choosen by asking for `package=*=*gpu*`.

The problem with this approach is that it doesn't scale well for more than one "flag" per build string. What if a package needs to distinguish among more than one feature? That is, not just GPU vs CPU, but also BLAS backend, MPI or licensing? The glob strings are not expressive enough for a single spec, so several ones need to be supplied (e.g. `package=*=*gpu*`, `package=*=*mkl*`, `package=*=*mpich*` and `package=*=*nogpl*`), resulting in complicated lookahead regexes that balloon in computational complexity.

The answer to this problem is to provide a specific field that is designed to provide such selection capabilities without the expressivity and complexity problems observed above: `flags`.

## Rationale

...

## Specification

### Repodata record syntax

The `info/index.json` file of each conda artifact MUST support a new field, `flags`, the value of which MUST be a list of non-empty strings matching the regex `^[a-z0-9\-_:+\.]+$`. Subsequently, the `schema_version` value MUST be bumped to `5`.

In recipes, this value MUST be supported in the `build` section of each output (i.e. sibling to `number` and `track_features`).

Additionally, another field has to be added to the `index.json` file and `repodata_record`: `variant_order`. This field lists flags in descending priority order. During the resolution, artifacts that match on flags are sorted by the order in `variant_order`.

### MatchSpec syntax changes

Values in the `flags` field MUST be matchable by the corresponding keyword in `MatchSpec`, placed in the square brackets section. Its value MUST be a string or list of strings supporting the following syntax:

- A string matching the regex `^[a-z0-9\-_:+\.]+$` is considered a literal match and will evaluate to true if the input string matches the target string fully.
- The asterisk symbol `*` works as a glob operator, with the same rules used for build string matching.
- A string query MAY be followed by one of the operators `=`, `!=`, `>`, `>=`, `<` and `<=`, which implement equality, inequality, greater than, greater than or equals, less than, less than or equals, respectively. They MUST be followed by a numeric value. When used, anything right side in the target strings will be interpreted as numbers and compared accordingly. The left side follows the same string matching rules as above.
- Two special prefix characters MUST be recognized with the following meaning:
  - `~`: negates the match
  - `?`: makes the match optional

### Variant order sorting

The variants are sorted lexicographically by matching flags from the variant order. Flags not mentioned in the variant order will be sorted lower than any flags mentioned in the variant order, and in alphabetical order.

Example:

```
variant order: [release, cuda, blas:mkl, blas:openblas]

sorted variants:

1. [release, cuda, blas:mkl]
2. [release, cuda, blas:openblas]
3. [release, blas:mkl]
4. [release, blas:openblas]
5. [release, blas:blis]
6. [debug]
```

### `index.json` and `repodata_record` changes

The records gain two new fields, `flags` and `variant_order`:

```json
...
{
  "name": "foobar",
  "version": "1.2.3",
  "flags": ["gpu:cuda", "build_type:release", "blas:mkl"],
  "variant_order": ["build_type:release", "blas:mkl", "gpu:*"]  # rest of the flags,
}
```

### Changes to the `recipe.yaml` file

```yaml
build:
  string: ...
  flags: ["gpu:cuda${{ cuda_version }}", "blas:${{ blas}}", "release"]
  variant:
    order: ["release", "blas:mkl", "blas:blis", "blas:openblas", "gpu:*"],

```

## Examples

In practice, this would look like the following from a user perspective:

```shell
conda install 'pytorch[version=">=3.1", flags=["gpu:*", "?release"]]'
```

## Rejected ideas

This proposal may remind the readers of the old `features` properties in the first iterations of conda packaging.

## References

...


## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
