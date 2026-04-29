# CEP XXXX - URL field for package records

<table>
<tr><td> Title </td><td> URL field for package records</td></tr>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td>
  Dan Yeaw &lt;dyeaw@anaconda.com&gt;
</td></tr>
<tr><td> Created </td><td> Feb 2, 2026</td></tr>
<tr><td> Updated </td><td> Feb 2, 2026</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/111 </td></tr>
<tr><td> Implementation </td><td> TBD </td></tr>
<tr><td> Requires </td><td> <a href="https://github.com/conda/ceps/pull/146">conda/ceps#146</a> (backwards-compatible repodata update strategy)</td></tr>
</table>

> The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT",
"RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as
described in [RFC2119][RFC2119] when, and only when, they appear in all capitals, as shown here.

## Abstract

This CEP introduces a new optional `url` field in package records to specify download locations for individual packages.

## Motivation

Currently, the download location for a package is constructed by combining the `base_url` field (defined in [CEP 16](https://conda.org/learn/ceps/cep-0016)) with the package filename (which serves as the dictionary key in repodata). This has a couple of limitations:

1. Packages must be stored in the same directory as `repodata.json`
2. It is not possible to serve the files from different servers or Content Delivery Networks (CDNs)

## Rationale

Adding a `url` field enables several use cases that are not possible with the current approach:

- **Per-package directories**: Common in [PyPI simple repositories](https://packaging.python.org/en/latest/guides/hosting-your-own-index/#manual-repository) where each package has its own subdirectory
- **CDN distribution**: Packages can be served from different CDNs with hash-based URLs
- **Mixed sources**: Different packages in the same repodata can be hosted on different servers
- **Backward compatibility**: Traditional flat directory structures continue to work by setting `url` to the filename

Although wheels were the primary motivation, this change provides general flexibility for package hosting in the conda ecosystem.

## Specification

Package repodata records MAY contain a `url` field. When present, the value MUST be set to either a full URL or a relative POSIX path.

Conda clients SHALL construct the download URL as follows:

1. Determine the base URL:
   - If the repodata's `info` object contains a `base_url` field, use that value
   - Otherwise, use an empty string (`""`)

2. Determine the package path:
   - If the package record contains a `url` field, use that value
   - Otherwise, use the package filename (the dictionary key)

3. Resolve the download URL by combining the base URL with the package path following [RFC 3986 URL resolution semantics](https://datatracker.ietf.org/doc/html/rfc3986#section-5) (equivalent to Python's `urllib.parse.urljoin(base_url, package_path)`).

This resolution means:

- **Full URLs**: If the package path is a full URL (e.g., `https://cdn.example.com/package.conda`), it is used as-is, ignoring the base URL
- **Relative path with `base_url`**: If the package path is relative (e.g., `subdir/package.conda`) and `base_url` is set (e.g., `https://repo.example.com/`), the result is `https://repo.example.com/subdir/package.conda`
- **Relative path without `base_url`**: If the package path is relative and no `base_url` is specified, the package path remains relative and will be resolved by the HTTP client relative to the repodata's location

## Examples

### Absolute URL

In this example, the package is served from a CDN with a full URL:

```json
{
  "packages.conda": {
    "numpy-2.4.2-py314hd4f4903_0.conda": {
      "build": "py314hd4f4903_0",
      "build_number": 0,
      "constrains": [],
      "depends": [
        "libblas >=3.9.0,<4.0a0",
        "libcblas >=3.9.0,<4.0a0",
        "liblapack >=3.9.0,<4.0a0",
        "python >=3.14,<3.15.0a0"
      ],
      "license": "BSD-3-Clause",
      "md5": "c15ea513263c9a15d504ab6b087c6d81",
      "name": "numpy",
      "sha256": "1f39bde67c7d252f079260f871c1d6e67b9757e94953369081f5764423fb5e01",
      "size": 8970626,
      "subdir": "linux-64",
      "timestamp": 1770020169383,
      "url": "https://cdn.example.com/packages/numpy/numpy-2.4.2-py314hd4f4903_0.conda",
      "version": "2.4.2"
    }
  }
}
```

### Relative URL with base_url

In this example, packages are organized in subdirectories by package name, using a relative URL combined with `base_url`. The repodata file is located at `https://repo.example.com/conda/linux-64/repodata.json`, where `linux-64` is the platform-specific subdirectory:

```json
{
  "info": {
    "base_url": "https://repo.example.com/conda/linux-64/"
  },
  "packages.conda": {
    "packaging-25.0-pyh29332c3_1.conda": {
      "build": "pyh29332c3_1",
      "build_number": 1,
      "depends": [
        "python >=3.8"
      ],
      "license": "Apache-2.0 OR BSD-2-Clause",
      "md5": "8da6e3f6a14a8f7b8e43f0e4b3e6b5c9",
      "name": "packaging",
      "noarch": "python",
      "sha256": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
      "size": 51234,
      "subdir": "noarch",
      "timestamp": 1735689600000,
      "url": "packaging/packaging-25.0-pyh29332c3_1.conda",
      "version": "25.0"
    }
  }
}
```

The client would resolve the relative `url` against the `base_url` to get: `https://repo.example.com/conda/linux-64/packaging/packaging-25.0-pyh29332c3_1.conda`

## Backward Compatibility

This CEP introduces a new optional `url` field to package records. Since the field is optional, this change is backwards-compatible:

- Older clients that don't recognize the `url` field will continue to construct download URLs using the existing method (combining `base_url` with the package filename)
- Newer clients will use the `url` field when present, falling back to the traditional method when absent
- Existing repodata without `url` fields will continue to work without modification

This approach allows for gradual adoption, where channels can add `url` fields only for packages that need non-standard locations (such as wheels in subdirectories), while keeping traditional flat-structure packages unchanged.

Adoption of `url` in channels SHOULD follow the backwards-compatible repodata update strategy specified in [conda/ceps#146](https://github.com/conda/ceps/pull/146): that strategy defines how to publish repodata changes so clients that ignore unknown record fields continue to resolve artifacts correctly, which matches how the optional `url` is used here.

## Rejected ideas

### Using the dictionary key for paths

The directory path could be embedded in the package's dictionary key (e.g., `packaging/packaging-25.0-pyh29332c3_1.conda`). While some clients may already support this, an explicit `url` field is clearer and maintains the convention that dictionary keys are filenames, not paths.

### Adding an `fn` field alongside `url`

A separate `fn` field could specify a different filename for saving locally. However, packages should not be renamed after downloading, and the filename can be obtained from either the `url` basename or the dictionary key. This would add no value while increasing repodata size.

## References

- [conda/ceps#146 - A backwards-compatible repodata update strategy](https://github.com/conda/ceps/pull/146): Repodata rollout pattern this CEP relies on when introducing optional package-record fields such as `url`
- [CEP 15 - Hosting repodata.json and packages separately by adding a `base_url` property](https://conda.org/learn/ceps/cep-0015): Introduced the `base_url` field for repodata
- [PyPI Simple Repository API](https://peps.python.org/pep-0503/): Specification for simple package repositories
- [Hosting your own simple repository](https://packaging.python.org/en/latest/guides/hosting-your-own-index/#manual-repository): Example of package repositories with per-package subdirectories

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

<!-- links -->
[RFC2119]: https://datatracker.ietf.org/doc/html/rfc2119
