<table>
<tr><td> Title </td><td> Add package-urls to PackageRecord </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Bas Zalmstra &lt;bas@prefix.dev&gt;, Pavel Zwerschke &lt;pavelzw@gmail.com&gt; </td></tr>
<tr><td> Created </td><td> Nov 23, 2023</td></tr>
<tr><td> Updated </td><td> Nov 23, 2023</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/63 </td></tr>
<tr><td> Implementation </td><td> https://github.com/prefix-dev/rattler-build/pull/1664, https://github.com/conda/rattler/pull/1303, https://github.com/conda/rattler/pull/1312 </td></tr>
</table>

## Abstract

This CEP describes a change to the `PackageRecord` format and the corresponding `repodata.json` file to include `purls` (Package Urls) of repackaged packages to identify packages across multiple ecosystems.

## Specification

We propose to add the optional `purls: [string]` field to `PackageRecord`.
To identify the repackaged package we use [PURL](https://github.com/package-url/purl-spec/) (Package URL), which implements a scheme for identifying packages that is meant to be portable across packaging ecosystems.

```json
{
  ...
  "pinject-0.14.1-pyhd8ed1ab_0.tar.bz2": {
    "name": "pinject",
    "version": "0.14.1",
    "purls": ["pkg:pypi/pinject@0.14.1"],
    ...
  }
  ...
}
```

PURL is already supported by dependency-related tooling like SPDX (see [External Repository Identifiers in the SPDX 2.3 spec](https://spdx.github.io/spdx-spec/v2.3/external-repository-identifiers/#f35-purl)), the [Open Source Vulnerability format](https://ossf.github.io/osv-schema/#affectedpackage-field), and the [Sonatype OSS Index](https://ossindex.sonatype.org/doc/coordinates); not having to wait years before support in such tooling arrives is valuable.
[PEP 725 (WIP)](https://peps.python.org/pep-0725) also proposes how to specify non-PyPi dependencies using PURLs.

### PURLs in recipes

PURLs can be specified in the recipe under `.about.purls` (implementation for [v1-recipes](cep-00014.md): [prefix-dev/rattler-build #1664](https://github.com/prefix-dev/rattler-build/pull/1664)):

```yaml
about:
  # ...
  # PURLs that this package belongs to
  purls: [string (PURL enforced)]
```

Tools that build conda packages should add these packages to `index.json`:

```json
{
  ...,
  "purls": ["pkg:pypi/pinject@0.14.1"]
}
```

### PURLs in repodata

In `repodata.json`, PURLs should be an optional field.
Tools that generate `repodata.json` (like `rattler-index` or `conda-index`) can decide whether to include it or not in `repodata.json`.

Instead of writing the PURLs in `repodata.json`, these tools can decide to add PURLs to a separate `purls.json` like in [CEP 12](cep-0012.md):

```json
{
  "info": {
    "platform": "string",
    "arch": "string",
    "subdir": "string",
    "version": 0
  },
  "packages": {
    "package-version-build.tar.bz2": {
      ...,
      "purls": ["pkg:pypi/pinject@0.14.1"]
    }
  },
  "packages.conda": {
    "package-version-build.conda": {
      ...,
      "purls": ["pkg:pypi/pinject@0.14.1"]
    }
  }
}
```

If the `purls` field is not present in the `repodata.json` record, it means no `purls` information is stored with the record. Then, a fallback mechanism (i.e., read `purls.json`) should be used to acquire the PURL information.

In sharded repodata ([CEP 16](cep-0016.md)), PURLs can be specified similar to [CEP 21](cep-0021.md).

### Patching

With the purls part of the repodata we propose to also allow repodata patching this field. The original purls can still be extracted from the packages in `index.json`. We do not see a reason how the PURL information is different from other patchable information stored in the repodata (like the dependencies).

To facilitate these patches, the `patch_instructions_version` in `patch_instructions.json` files is incremented to `3`. A `patch_instructions_version: 3` file MAY contain a `purls: ...` field in the patch instructions that MUST be used to patch generated the `purls` entry in the (sharded) repodata (or the `purls.json`).

```json
{
  "patch_instructions_version": 3,
  "packages": {
    "package-version-build.tar.bz2": {
      ...,
      "purls": ["pkg:pypi/pinject@0.14.1"]
    },
    ...
  }
}
```

### PURL of a conda packages

Conda packages itself should have a PURL as well.
This makes it possible for CVE Numbering Autorities (CNA) to publish vulnerabilities for conda packages.
A package `pinject-0.14.1-pyh29332c3_1.conda` published on `conda-forge` should have the PURL `pkg:conda/conda-forge/pinject@0.14.1?build=pyh29332c3_1&platform=noarch`.
Packages can also specify a custom `repository_url`, for example `pkg:conda/custom-channel/my-package@0.1.0?build=pyh29332c3_1&platform=noarch&repository_url=prefix.dev`.

Tools that generate packages like rattler-build and conda-build should also be able to inject a PURL at build time via CLI flags.
For this, v1-recipes can use the jinja syntax from the recipes.

```bash
rattler-build build -r recipe/ \
    --append-purl-pattern \
    'pkg:conda/conda-forge/${{ PACKAGE_NAME }}@${{ PACKAGE_VERSION }}?build=${{ BUILD_NUMBER }}'
```

Variables that are available in the build process (like `PACKAGE_NAME`, `PACKAGE_VERSION` and `BUILD_NUMBER`) can be specified here.

## Motivation

Conda packages can mostly repackage packages from other ecosystems.
Conda-forge and other channels famously repackages a lot of PyPI packages.
However, without actually downloading the conda package and inspecting its contents there is no reliable way to know whether a certain conda package is a repackaged package and which package it repackages.

Tools like pixi or conda-lock try to combine conda and PyPI packages through heuristics. This doesn't work deterministically as package names between the two indices may differ.

Its hard to use open-source vulnerability databases because they often do not contain conda packages.
Using the PURL standard allows us to link vulnerabilities from other ecosystems to conda package.

## Rationale

Adding the information to the `repodata.json` file has some advantages:

* We can keep this information close to the conda package description.
* We can incrementally add `purls` through repodata patches.

The downside is that the (already large) `repodata.json` file will grow. That's why this field is optional in `repodata.json` and can be instead added to a `purls.json`.

The `purls` field is an array because:

* A package might exist in multiple ecosystems
* A single conda package might repackage multiple other packages.

## Alternatives

Some work has been done to try and map conda package names to PyPI package names through the grayskull mapping:

<https://raw.githubusercontent.com/regro/cf-graph-countyfair/master/mappings/pypi/grayskull_pypi_mapping.yaml> and <https://github.com/conda/grayskull/blob/0cba811da58d003a98cb844ff760b9a4f490350f/grayskull/strategy/config.yaml>

This file is generated automatically from the recipes in conda-forge feedstocks.

However, this approach has some serious drawbacks:

* It only works for packages from conda-forge.
* Its a heuristic based on source urls.
* The implementation is based on the recipes instead of the actual package files.
* The implementation does not work with multi-output recipes.
* Its maintained as a separate file that is hard to discover

## Backwards Compatibility

Since the `purls` field is an addition (and optional) there should be no breaking changes.

<!--
## Other sections

Other relevant sections of the proposal.  Common sections include:

    * Specification -- The technical details of the proposed change.
    * Motivation -- Why the proposed change is needed.
    * Rationale -- Why particular decisions were made in the proposal.
    * Backwards Compatibility -- Will the proposed change break existing
      packages or workflows.
    * Alternatives -- Any alternatives considered during the design.
    * Sample Implementation -- Links to prototype or a sample implementation of
      the proposed change.
    * FAQ -- Frequently asked questions (and answers to them).
    * Resolution -- A short summary of the decision made by the community.
    * Reference -- Any references used in the design of the CEP.
-->

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
