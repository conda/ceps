# CEP XXXX - Names in conda packages and channels

<table>
<tr><td> Title </td><td> CEP XXXX - Names in conda packages and channels </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Jaime Rodríguez-Guerra &lt;jaime.rogue@gmail.com&gt; <br /> Matthew R. Becker &lt;becker.mr@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> Mar 11, 2025</td></tr>
<tr><td> Updated </td><td> Mar 19, 2025</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/116 </td></tr>
<tr><td> Implementation </td><td> N/A </td></tr>
</table>

## Abstract

This CEP aims to standardize names and other strings used to identify packages, artifacts and channels in the conda ecosystem.

## Specification

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT",
"RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as
described in [RFC2119][RFC2119] when, and only when, they appear in all capitals, as shown here.

More specifically, violations of a MUST or MUST NOT rule MUST result in an error. Violations of the
rules specified by any of the other all-capital terms MAY result in a warning, at discretion of the
implementation.

### Identifying package artifacts

The conda ecosystem distinguishes between two types of packages:

- Distributable package names: represented by a concrete, downloadable, extractable conda artifact.
- Virtual package names: not backed by any physical artifact. They only exist on the client side.

#### Package names

A distributable package name MUST only consist of lowercase ASCII letters, numbers, hyphens, periods and underscores. It MUST start with a letter, a number, or a single underscore. It MUST NOT include two consecutive separators (hyphen, period, underscore).

Virtual package names MUST only consist of lowercase ASCII letters, numbers, hyphens, periods and underscores. They MUST NOT use two consecutive separators, with one exception: they MUST start with two underscores.

This means that distributable package names MUST match the following case-insensitive regex: `^(([a-z0-9])|([a-z0-9_](?!_)))[._-]?([a-z0-9]+(\.|-|_|$))*$`.

Virtual package names MUST follow this other regex: `^__[a-z0-9][._-]?([a-z0-9]+(\.|-|_|$))*$`.

In all cases, the maximum length of a package name MUST NOT exceed 128 characters.

#### Version strings

Version strings MUST only consist of digits, periods, lowercase ASCII letters, underscores, plus
symbols, and exclamation marks. Additional rules apply but are out of scope in this CEP and will be
discussed separately.

The maximum length of a version string MUST NOT exceed 128 characters.

#### Build strings

Builds strings MUST only consist of ASCII letters, numbers, periods, plus symbols, and underscores. They MUST match this regex `^[a-zA-Z0-9_\.+]+$`.

The maximum length of a build string MUST NOT exceed 128 characters.

#### Filenames

Distributable conda artifacts MUST have a filename following this scheme:

```text
<package name>-<version string>-<build string>.<extension>
```

Virtual conda packages do not exist on disk and SHOULD NOT need filename standardization.

#### Distribution strings

A "distribution string" MAY be used to identify a package artifact without specifying the extension or the channel. It MUST match the following syntax:

```text
<package name>-<version string>-<build string>
```

Distribution strings apply to both distributable and virtual packages. They are used as the name of the directories where artifacts are extracted in the package cache, for example.

> Note: Despite the similarity, distribution strings are not `MatchSpec`-like specifiers and
> MUST NOT be used as such.

### Identifying channels

A conda channel is defined as a URL where one can find one or more `repodata.json` files arranged in one subdirectory (_subdir_) each. `noarch/repodata.json` MUST be present to consider the parent location a channel.

#### Channel base URLs and names

The base URL for the arbitrary location of a repodata file is defined as:

```text
<scheme>://[<authority>][/<path>/][/label/<label name>]/<subdir>/repodata.json
```

with `<scheme>`, `<authority>` and `<path>` defined by [RFC
3986](https://datatracker.ietf.org/doc/html/rfc3986#section-3.2).

Taken the channel definition above, the base URL without trailing slashes is thus:

```text
<scheme>://[<authority>][/<path>/][/label/<label name>]
```

For example, given `https://conda.anaconda.org/conda-forge/noarch/repodata.json`, the part leading
to `noarch/repodata.json` and thus base URL is `https://conda.anaconda.org/conda-forge/conda-forge`. For local repodata such as `file:///home/username/channel/noarch/repodata.json`, the
channel base URL is `file:///home/username/channel`.

For convenience, the channel _name_ is defined as the concatenation of `scheme`, `authority` and
`path` components. The `<scheme>://` part MAY be omitted if `scheme` is one of `http`, `https` or
`file`. At least one of `authority` or `path` SHOULD be present. In their absence, the channel name
MUST be considered empty, regardless the scheme. Empty channel names SHOULD NOT be used.

When present, each path component MUST only contain lowercase ASCII letters, numbers, underscores, periods,
and dashes. They MUST not start with a period or a dash. They SHOULD start and end with a letter or a number. If present, all path components combined SHOULD match this regex:

```re
^[a-z0-9]+((\.|_|__|-+)[a-z0-9]+)*(\/[a-z0-9]+((\.|_|__|-+)[a-z0-9]+)*)*$
```

The maximum length of a channel base URL SHOULD NOT exceed 256 characters.

#### Subdir names

Channel subdir names MUST either be the literal `noarch` or a string following the syntax `{os}-{arch}`, where `{os}` and `{arch}` MUST only consist of lowercase ASCII letters and numbers. Non-`noarch` subdirs MUST match this regex: `^[a-z0-9]+-[a-z0-9]+$`.

The maximum length of a subdir name MUST NOT exceed 32 characters.

#### Label names

Channel label names MUST only consist of ASCII letters, digits, underscores, hyphens, forward slashes, periods, colons and whitespace. They MUST start with a letter. They MUST match this regex: `^[a-zA-Z][0-9a-zA-Z_\-\.\/:\s]*`. Even if allowed, label names SHOULD NOT contain any whitespace.

The label `nolabel` is reserved and MUST only be used for conda packages which have no other labels. In other words, in the space of labels, the empty set is represented by the labels `nolabel`.

The maximum length of a label name SHOULD NOT exceed 128 characters.

## Backwards compatibility

The conda subdir and package name regexes are backwards compatible with the current `conda` implementation (25.3) and all existing packages on the `defaults` and `conda-forge` channels, except for the `__anaconda_core_depends` package on the `defaults` channel.

The regex for labels was pulled from an anaconda.org error message describing the set of valid labels.

As of 2025-03-12T19:00Z, of the ~1.9M channel names on anaconda.org:

- 7,219 violate the regex `^[a-z0-9]+((-|_|.)[a-z0-9]+)*$`;
- 98 violate the regex `^[a-z0-9][a-z0-9_.-]*$` (allowing channel names to end with `_`, `.`, or `-`); and
- 6 violate `^[a-z0-9_][a-z0-9_.-]*$` (allowing channel names to start with `_`). Of those six, five start with `.`, and the other starts with `~`.

Given the low percentage (~0.4%) of mismatches, authors have decided to ignore those entries and err on the side of strictness to maximize compatibility with other storage solutions that have more restrictive naming requirements.

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

<!-- links -->

[RFC2119]: https://www.ietf.org/rfc/rfc2119.txt
