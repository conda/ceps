# CEP XXXX - Names in conda packages and channels

<table>
<tr><td> Title </td><td> CEP XXXX - Names in conda packages and channels </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Jaime Rodríguez-Guerra &lt;jaime.rogue@gmail.com&gt; <br /> Matthew R. Becker &lt;becker.mr@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> Mar 11, 2025</td></tr>
<tr><td> Updated </td><td> Mar 11, 2025</td></tr>
<tr><td> Discussion </td><td> N/A </td></tr>
<tr><td> Implementation </td><td> N/A </td></tr>
</table>

## Abstract

This CEP aims to standardize names and other strings used throughout the conda ecosystem.

## Specification

### Artifacts

The conda ecosystem distinguishes between two types of packages:

- Distributable package names: represented by a concrete, downloadable, extractable conda artifact.
- Virtual package names: not backed by any physical artifact. They only exist on the client side.

### Package names

A distributable package name MUST only consist of lowercase ASCII letters, numbers, hyphens, periods and underscores. It MUST start with a letter, a number, or a single underscore. It MUST NOT include two consecutive separators (hyphen, period, underscore).

Virtual package names MUST only consist of lowercase ASCII letters, numbers, hyphens, periods and underscores. They MUST NOT use two consecutive separators, with one exception: they MUST start with two underscores.

This means that distributable package names MUST match the following case-insensitive regex: `^(([a-z0-9])|([a-z0-9_](?!_)))[._-]?([a-z0-9]+(\.|-|_|$))*$`.

Virtual package names MUST follow this other regex: `^__[a-z0-9][._-]?([a-z0-9]+(\.|-|_|$))*$`.

In all cases, the maximum length of a package name MUST NOT exceed 128 characters.

### Version strings

Version strings MUST only consist of digits, periods, lowercase ASCII letters, underscores, plus
symbols, and exclamation marks. Additional rules apply but are out of scope in this CEP and will be
discussed separately.

The maximum length of a version string MUST NOT exceed 128 characters.

### Build strings

Builds strings MUST only consist of ASCII letters, numbers, periods, plus symbols, and underscores. They MUST match this regex `^[a-zA-Z0-9_\.+]+$`.

The maximum length of a build string MUST NOT exceed 128 characters.

### Filenames

Regular conda artifacts MUST be named following this scheme:

```
<package name>-<version string>-<build string>.<extension>
```

Virtual conda packages SHOULD NOT need filename standardization.

### Channels

A conda channel is defined as a location where one can find one or more `repodata.json` files arranged in one subdirectory (_subdir_) each. `noarch/repodata.json` MUST be present to consider the parent location a channel.

#### Channel names

With that definition in mind, a channel name is understood as the path component of the URI leading to the `noarch/repodata.json` location, without leading or trailing slashes. For example, given `https://conda.anaconda.org/conda-forge/noarch/repodata.json`, the full path component is `conda-forge/noarch/repodata.json`. The part leading to `noarch/repodata.json` is thus `conda-forge`, the channel name. For local repodata such as `file:///home/username/channel/noarch/repodata.json`, the channel name is `home/username/channel`.

Channel names MUST only consist of lowercase ASCII letters, numbers, hyphens, periods, slashes and underscores. They MUST start and end with a letter or a digit. They MUST NOT contain two consecutive separators (hyphen, underscore, period, slash). In other words, they MUST match this regex: `^[a-z0-9]+((-|_|.)[a-z0-9]+)*$`.

The maximum length of a channel name SHOULD NOT exceed 128 characters.

#### Subdir names

Channel subdir names MUST either be the literal `noarch` or a string following the syntax `{os}-{arch}`, where `{os}` and `{arch}` MUST only consist of lowercase ASCII letters and numbers. Non-`noarch` subdirs MUST match this regex: `^[a-z0-9]+-[a-z0-9]+$`.

The maximum length of a subdir name MUST NOT exceed 32 characters.

#### Label names

Channel label names MUST only consist of ASCII letters, digits, underscores, hyphens, forward slashes, periods, colons and whitespace. They MUST start with a letter. They MUST match this regex: `^[a-zA-Z][0-9a-zA-Z_\-\.\/:\s]*`. Even if allowed, label names SHOULD NOT contain any whitespace.

The labels `nolabel` is reserved and MUST only be used for conda packages which have no other labels. In other words, in the space of labels, the empty set is represented by the labels `nolabel`.

The maximum length of a label name SHOULD NOT exceed 128 characters.

## Backwards compatibility

The conda channel, subdir, label, and package name regexes are backwards compatible with the current `conda` implementation (25.3) and all existing packages on the `defaults` and `conda-forge` channels, except the `__anaconda_core_depends` package on the `defaults` channel.

The regex for labels above was pulled from an anaconda.org error message describing the set of valid labels. Finally, anaconda.org usernames/channel names are case insensitive and cannot begin with an underscore.

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
