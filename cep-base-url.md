<table>
<tr><td> Title </td><td> Hosting repodata.json and packages separately by adding a base_url property. </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Daniel Holth &lt;dholth@anaconda.com&gt;</td></tr>
<tr><td> Created </td><td> Aug 24, 2023</td></tr>
<tr><td> Updated </td><td> Aug 24, 2023</td></tr>
<tr><td> Discussion </td><td>  </td></tr>
<tr><td> Implementation </td><td>  </td></tr>
</table>

## Abstract

Conda packages need to be stored in the same directory as `repodata.json`.

This can be inconvenient especially when using alternative `repodata.json` for
the same set of packages. For example, a user might be interested in installing
packages based on an older snapshot of the index data that points to packages
from the original index. Or a user might want to subset `repodata.json` based on
policy.

## Specification

A minimal `repodata.json` looks like this.

```
{"info": {"subdir": "linux-64"},
 "packages": {},
 "packages.conda": {"package-name.conda":{...}},
 "removed": [],
 "repodata_version": 1}
```

Add `base_url` to the `info` object. Increment `repodata_version`.

```
{"info": {"subdir": "...", "base_url":"https://repo.anaconda.com/repo/main/linux-64/"},
 "packages": {},
 "packages.conda": {"package-name.conda":{...}},
 "removed": [],
 "repodata_version": 2}
 ```

Append `base_url` and `package-name.conda` when downloading a package.

`base_url` can be an absolute or a relative URL.

In the absence of `base_url`, packages are loaded relative to the
`repodata.json`. Index data without the new `base_url` will continue to have
`"repodata_version": 1`, but index data including `base_url` will have
`"repodata_version": 2`.

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
