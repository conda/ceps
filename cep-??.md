<table>
<tr><td> Title </td><td> The <code>MatchSpec</code> grammar </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Jaime Rodríguez-Guerra &lt;jaime.rogue@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> June 4, 2024 </td></tr>
<tr><td> Updated </td><td> June 4, 2024 </td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/82 </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
</table>

## Abstract

This CEP standardizes the grammar for the `MatchSpec` query language.

## Motivation

The motivation of this CEP is merely informative. It describes the details of an existing grammar.

## Nomenclature

The `MatchSpec` query syntax is a mini-language designed to query package records from one or more conda channels. It is sometimes referred to as simply _spec_.

## Mini language

The `MatchSpec` mini language has gone through several iterations:

- Positional syntax, with two variants: space- and `=`-separated.
- Square brackets syntax.

### Space-separated positional syntax

The simplest form merely consists of up to six positional arguments: `[channel[/subdir]:[namespace]:]name [version [build]]`. Only `name` is required. `version` can be any version specifier. `build` can be any string matcher. See "Match conventions" below.

### `=`-separated positional syntax

The positional syntax also allows the `=` character as a separator, instead of a space, between `name`, `version` and `build`. When this is the case, versions are interpreted differently. `pkg=1.8` will be taken as `1.8.*` (fuzzy), but `pkg 1.8` will give `1.8` (exact). To have fuzzy matches with the space syntax, you need to use `pkg =1.8`. This nuance does not apply if a `build` string is present; both `foo==1.0=*` and `foo=1.0=*` are equivalent (they both understand the version as `1.0`, exact).

### Square brackets syntax

`MatchSpec` queries can be also specified with keyword arguments between square brackets. Key-value pairs can be delimited by comma, space, or comma+space. Value can optionally be wrapped in single or double quotes, but must be wrapped if `value` contains a comma, space, or equal sign. Their values can be quoted with single or double quotes. The accepted keys are:

- `channel` (`str`): Name or URL of a channel
- `subdir` (`str`): Identifier of the subdir (either platform-specific or `noarch`)
- `version` (`str`): A version specifier
- `build` (`str`): Build string or a glob match.
- `build_number` (`int`): Number of the build
- `md5` (`str`): MD5 hash of the artifact
- `sha256` (`str`): SHA256 hash of the artifact

These are also accepted but have reduced utility. Their usage is discouraged:

- `url`
- `track_features`
- `features`
- `license`
- `license_family`
- `fn`

When both positional and keyword arguments are used, the keyword arguments override the positional information, except for `name` (positional value wins).

## Canonical representation

Since there are several ways of specifying the same information, a canonical representation is welcome. The currently accepted notation is:

```
(channel(/subdir):(namespace):)name(version(build))[key1='value 1',key2=value2]
```

where `()` indicate optional fields. `version` and `build` can be separated by a
space or `=` (see above). The rules for constructing a canonical string
representation are:

1. `name` (i.e. "package name") is required, but its value can be `*`. Its position is always
   outside the key-value brackets.
2. If `version` is an exact version, it goes outside the key-value brackets and is prepended
   by `==`. If `version` is a "fuzzy" value (e.g. `1.11.*`), it goes outside the key-value
   brackets with the `.*` left off and is prepended by `=`. Otherwise `version` is included
   inside key-value brackets.
3. If `version` is an exact version, and `build` is an exact value, `build` goes outside
   key-value brackets prepended by a `=`. Otherwise, `build` goes inside key-value brackets.
   `build_string` is an alias for `build`.
4. The `namespace` position is being held for a future conda feature.
5. If `channel` is included and is an exact value, a `::` separator is used between `channel`
   and `name`. `channel` can either be a canonical channel name or a channel url. In the
   canonical string representation, the canonical channel name will always be used.
6. If `channel` is an exact value and `subdir` is an exact value, `subdir` is appended to
   `channel` with a `/` separator. Otherwise, `subdir` is included in the key-value brackets.
7. The canonical format for key-value pairs uses comma delimiters and single quotes.
8. When constructing a `MatchSpec` queries instance from a string, any key-value pair given
   inside the key-value brackets overrides any matching parameter given outside the brackets.

## Match conventions

Since the only required field is `name`, any non-specified field is the equivalent of a full wildcard match (`*`).

### String matching

When `MatchSpec` queries attribute values are simple strings, they are interpreted using the
following conventions:

- If the string begins with `^` and ends with `$`, it is converted to a regex.
- If the string contains an asterisk (`*`), it is transformed from a glob to a regex. For example, `*cuda` becomes `^.*cuda$`.
- Otherwise, an exact match to the string is sought.

### Version specifiers

The version field uses a PEP-440-like ordering defined in [`conda.models.version.VersionOrder`](https://github.com/conda/conda/blob/c9348478751c57d136a25058c79aef1fc91d2863/conda/models/version.py#L52). Excerpts of its contents are submitted here for reference:

> Version strings can contain the usual alphanumeric characters
> (A-Za-z0-9), separated into components by dots and underscores. Empty
> segments (i.e. two consecutive dots, a leading/trailing underscore)
> are not permitted. An optional epoch number - an integer
> followed by `!` - can proceed the actual version string
> (this is useful to indicate a change in the versioning
> scheme itself). Version comparison is case-insensitive.
> 
> Conda supports six types of version strings:
> * Release versions contain only integers, e.g. `1.0`, `2.3.5`.
> * Pre-release versions use additional letters such as `a` or `rc`,
>   for example `1.0a1`, `1.2.beta3`, `2.3.5rc3`.
> * Development versions are indicated by the string `dev`,
>   for example `1.0dev42`, `2.3.5.dev12`.
> * Post-release versions are indicated by the string `post`,
>   for example `1.0post1`, `2.3.5.post2`.
> * Tagged versions have a suffix that specifies a particular
>   property of interest, e.g. `1.1.parallel`. Tags can be added
>   to any of the preceding four types. As far as sorting is concerned,
>   tags are treated like strings in pre-release versions.
> * An optional local version string separated by `+` can be appended
>   to the main (upstream) version string. It is only considered
>   in comparisons when the main versions are equal, but otherwise
>   handled in exactly the same manner.
>
> To obtain a predictable version ordering, it is crucial to keep the
> version number scheme of a given package consistent over time.
> Specifically,
> * version strings should always have the same number of components
>   (except for an optional tag suffix or local version string),
> * letters/strings indicating non-release versions should always
>   occur at the same position.
> Before comparison, version strings are parsed as follows:
> * They are first split into epoch, version number, and local version
>   number at `!` and `+` respectively. If there is no `!`, the epoch is
>   set to 0. If there is no `+`, the local version is empty.
> * The version part is then split into components at `.` and `_`.
> * Each component is split again into runs of numerals and non-numerals
> * Subcomponents containing only numerals are converted to integers.
> * Strings are converted to lower case, with special treatment for `dev`
>   and `post`.
> * When a component starts with a letter, the fillvalue 0 is inserted
>   to keep numbers and strings in phase, resulting in `1.1.a1 == 1.1.0a1`.
> * The same is repeated for the local version part.
>
> Examples:
>
> ```
> 1.2g.beta15.rc  =>  [[0], [1], [2, 'g'], [0, 'beta', 15], [0, 'rc']]
> 1!2.15.1_ALPHA  =>  [[1], [2], [15], [1, '_alpha']]
> ```
>
> The resulting lists are compared lexicographically, where the following
> rules are applied to each pair of corresponding subcomponents:
>
> * integers are compared numerically
> * strings are compared lexicographically, case-insensitive
> * strings are smaller than integers, except
>   * `dev` versions are smaller than all corresponding versions of other types
>   * `post` versions are greater than all corresponding versions of other types
> * if a subcomponent has no correspondent, the missing correspondent is
>   treated as integer 0 to ensure `1.1` == `1.1.0`.
>
> The resulting order is:
>
> ```
>    0.4
>  < 0.4.0
>  < 0.4.1.rc
> == 0.4.1.RC   # case-insensitive comparison
>  < 0.4.1
>  < 0.5a1
>  < 0.5b3
>  < 0.5C1      # case-insensitive comparison
>  < 0.5
>  < 0.9.6
>  < 0.960923
>  < 1.0
>  < 1.1dev1    # special case 'dev'
>  < 1.1_       # appended underscore is special case for openssl-like versions
>  < 1.1a1
>  < 1.1.0dev1  # special case 'dev'
> == 1.1.dev1   # 0 is inserted before string
>  < 1.1.a1
>  < 1.1.0rc1
>  < 1.1.0
> == 1.1
>  < 1.1.0post1 # special case 'post'
> == 1.1.post1  # 0 is inserted before string
>  < 1.1post1   # special case 'post'
>  < 1996.07.12
>  < 1!0.4.1    # epoch increased
>  < 1!3.1.1.6
>  < 2!0.4.1    # epoch increased again
> ```
>
> Some packages (most notably openssl) have incompatible version conventions.
> In particular, openssl interprets letters as version counters rather than
> pre-release identifiers. For openssl, the relation:
>
> ```
> 1.0.1 < 1.0.1a  =>  False  # should be true for openssl
> ```
>
> holds, whereas conda packages use the opposite ordering. You can work-around
> this problem by appending an underscore to plain version numbers:
>
> ```
> 1.0.1_ < 1.0.1a =>  True   # ensure correct ordering for openssl
> ```

With that ordering in mind, the following operators are allowed:

- Range operators: `<`, `>`, `<=`, `>=`. Note that `<1.0` would include `1.0a` given the ordering above!
- Exact equality and negated equality: `==`, `!=`.
- Fuzzy equality: `=`, `*`. `=1.0` and `1.0.*` are equivalent, and both would match `1.0.0` and `1.0.1`, but not `1.1` or `0.9`.
- Logical operators: `|` means OR, `,` means AND. `1.0|1.2` would match both `1.0` and `1.2`. `>=1.0,<2.0a0` would match everything between `1.0` and the last version before `2.0a0`. `,` (AND) has higher precedence than `|` (OR). `>=1,<2|>3` means `(>=1,<2)|(>3)`; i.e. greater than or equal to `1` AND less than `2` or greater than `3`, which matches `1`, `1.3` and `3.0`, but not `2.2`.
- Semver-like operator: `~=`. `~=0.5.3` is equivalent to `>=0.5.3,0.5.*` and this syntax is preferred for backwards compatibility.

No spaces are allowed between operators. `1.8*` and `1.8.*` are equivalent, but the latter is preferred for clarity.

### Exact matches

To fully-specify a package record with a full, exact spec, these fields must be given as exact values: `channel` (preferrably by URL), `subdir`, `name`, `version`, `build`. Alternatively, an exact spec can also be given by `*[md5=12345678901234567890123456789012]` or `*[sha256=f453db4ffe2271ec492a2913af4e61d4a6c118201f07de757df0eff769b65d2e]`.

## Examples

```python
>>> str(MatchSpec('foo 1.0 py27_0'))
'foo==1.0=py27_0'
>>> str(MatchSpec('foo=1.0=py27_0'))
'foo==1.0=py27_0'
>>> str(MatchSpec('conda-forge::foo[version=1.0.*]'))
'conda-forge::foo=1.0'
>>> str(MatchSpec('conda-forge/linux-64::foo>=1.0'))
"conda-forge/linux-64::foo[version='>=1.0']"
>>> str(MatchSpec('*/linux-64::foo>=1.0'))
"foo[subdir=linux-64,version='>=1.0']"
```

## References

- [`conda.models.match_spec.MatchSpec`](https://github.com/conda/conda/blob/24.5.0/conda/models/match_spec.py)
- [`rattler_conda_types::match_spec`](https://github.com/conda/rattler/blob/rattler-v0.37.4/crates/rattler_conda_types/src/match_spec/mod.rs)
- [Package match specifications at conda-build docs](https://docs.conda.io/projects/conda-build/en/latest/resources/package-spec.html#package-match-specifications)

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
