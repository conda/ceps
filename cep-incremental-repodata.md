<table>
<tr><td> Title </td><td> Incremental updates for repodata.json </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Daniel Holth &lt;dholth@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> Mar 30, 2022</td></tr>
<tr><td> Updated </td><td> Mar 30, 2022</td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
</table>

## Abstract

Conda downloads a per-channel `repodata.json`, a file listing all available packages, when it changes, but a typical `repodata.json` update only adds a handful of packages. If conda could download just the changes it would save bandwidth and time. This document outlines a `repodata-patch.json` containing a list of patches needed to bring recent versions of `repodata.json` up to date with the most current version. If it has not been too long since the last complete `repodata.json` was fetch, conda can download a tiny file to bring the user up to date.

## Specification

When re-indexing a conda repository, also update a file `repodata-patch.json` containing a relative url to the target repodata; a hash of the most recent complete `repodata.json` and zero or more RFC 6902 Json Patch documents listed from newest to oldest. Each patch is accompanied by a hash `from` of the older version of the file, and a hash `to` of the newer version of the file. After inserting a new patch, discard the oldest patches to maintain `repodata-patch.json` at a useful size, perhaps no more than 10% of the size of the full file.

When updating metadata, look for a remote `repodata-patch.json` having a newer `Last-Modified` date compared to `repodata.json`. Download using standard HTTP caching rules.

To apply patches, take the hash of the most recent complete `repodata.json`. Follow the list of patches in `repodata-patch.json` from the first one whose `to` matches `latest`, to the next one whose `to` matches the more recent `from` and so on, pushing these onto a stack until a patch with a `from` hash matching the cached, outdated `repodata.json` is found. If the desired `from` hash is found, pop each patch off the stack applying them in turn to the outdated `repodata.json`. The result is logically equal to the latest `repodata.json`. Since Json Patch does not preserve formatting, the new `repodata.json` cannot be hashed unless it is normalized and re-serialized, but it can be considered to have the `latest` hash for purposes of incremental updates.

If the desired hash is not found, download the complete `repodata.json` as before.

An example of two patches against `repodata.json` adding a few packages to this ~30MB (4MB compressed) file:

```
{
  "url": "./repodata.json",
  "latest": "522b4f2143180599813da19b3083e922aa502a92ec2e2dfc4e16bfbf36750954",
  "patches": [
    {
      "from": "c218ae840b2f2443ff5d7f3ffbd2fea602f4abbfc707f520a868b0b96049645c",
      "to": "522b4f2143180599813da19b3083e922aa502a92ec2e2dfc4e16bfbf36750954",
      "patch": [
        {
          "op": "add",
          "path": "/packages.conda/nginx-1.21.6-hd80bfc7_0.conda",
          "value": {
            "build": "hd80bfc7_0",
            "build_number": 0,
            "depends": [
              "libgcc-ng >=7.5.0",
              "libgd 2.2.*",
              "libgd >=2.2.5,<2.3.0a0",
              "libgfortran-ng",
              "libgfortran4 >=7.5.0",
              "libstdcxx-ng >=7.5.0",
              "libxml2",
              "libxslt 1.1.*",
              "libxslt >=1.1.34,<2.0a0",
              "openssl >=1.1.1m,<1.1.2a",
              "pcre2 >=10.37,<10.38.0a0",
              "zlib >=1.2.11,<1.3.0a0"
            ],
            "license": "BSD-2-Clause",
            "license_family": "BSD",
            "md5": "3ccfff6b1f51112815ffe5425ecdbbc7",
            "name": "nginx",
            "sha256": "e6a0f13119b7074ddcea60c20fc466cf5364ef1d08b8a547c34fd4adf4669bae",
            "size": 524700,
            "subdir": "linux-64",
            "timestamp": 1646390801760,
            "version": "1.21.6"
          }
        }
      ]
    },
    {
      "from": "aac06b4e2c292a5229987d638d257d4feafd7b0b1f08b7a36f45dea425593837",
      "to": "c218ae840b2f2443ff5d7f3ffbd2fea602f4abbfc707f520a868b0b96049645c",
      "patch": [
        {
          "op": "add",
          "path": "/packages.conda/pillow-9.0.1-py39h22f2fdc_0.conda",
          "value": {
            "build": "py39h22f2fdc_0",
            "build_number": 0,
            "depends": [
              "freetype >=2.10.4,<3.0a0",
              "jpeg",
              "lcms2 >=2.12,<3.0a0",
              "libgcc-ng >=7.5.0",
              "libstdcxx-ng >=7.5.0",
              "libtiff >=4.1.0,<5.0a0",
              "libwebp >=0.3.0",
              "libwebp >=1.2.0,<1.3.0a0",
              "python >=3.9,<3.10.0a0",
              "tk",
              "zlib >=1.2.11,<1.3.0a0"
            ],
            "license": "LicenseRef-PIL",
            "license_family": "Other",
            "md5": "af9738244e2dca1bf5d04a81a34f28d5",
            "name": "pillow",
            "sha256": "ea1c3b72759bad5942a00290d52bae62f4630f004be604b5a5dfd958b28c3bb5",
            "size": 685262,
            "subdir": "linux-64",
            "timestamp": 1646325095608,
            "version": "9.0.1"
          }
        },
        {
          "op": "add",
          "path": "/packages.conda/pillow-9.0.1-py310h22f2fdc_0.conda",
          "value": {
            "build": "py310h22f2fdc_0",
            "build_number": 0,
            "depends": [
              "freetype >=2.10.4,<3.0a0",
              "jpeg",
              "lcms2 >=2.12,<3.0a0",
              "libgcc-ng >=7.5.0",
              "libstdcxx-ng >=7.5.0",
              "libtiff >=4.1.0,<5.0a0",
              "libwebp >=0.3.0",
              "libwebp >=1.2.0,<1.3.0a0",
              "python >=3.10,<3.11.0a0",
              "tk",
              "zlib >=1.2.11,<1.3.0a0"
            ],
            "license": "LicenseRef-PIL",
            "license_family": "Other",
            "md5": "bb592fe35035d609c091c8782f852224",
            "name": "pillow",
            "sha256": "9f6b3762141f69c49aed1e2ab2e4782ae1a872b59e9f6c381959ede13c0ceb55",
            "size": 1139325,
            "subdir": "linux-64",
            "timestamp": 1646325112795,
            "version": "9.0.1"
          }
        }
      ]
    }
  ]
}
```

In a realistic test, a ~1.3MB (225kB compressed using standard `Content-Encoding: gzip`) patch set represented three months of changes to Anaconda's `main/linux-64` channel; so users who `conda install` more than once a season would be able to download 225kB instead of 3.7MB.

## Alternatives

JSON Merge Patch is simpler, but does not allow the `null` values occasionally used in `repodata.json`.

Textual diff + patch would work, but `conda` needs the data and not the formatting.

## Reference

* JSON Patch https://datatracker.ietf.org/doc/html/rfc6902

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
