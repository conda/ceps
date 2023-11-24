<table>
<tr><td> Title </td><td> Add package-urls to PackageRecord </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Bas Zalmstra &lt;bas@prefix.dev&gt;</td></tr>
<tr><td> Created </td><td> Nov 23, 2023</td></tr>
<tr><td> Updated </td><td> Nov 23, 2023</td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
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

## Motivation

Conda packages can repackage packages from other ecosystems.
Conda-forge and other channels famously repackages a lot of PyPI packages.
However, without actually downloading the conda package and inspecting its contents there is no reliable way to know whether a certain conda package is a repackaged package.

Pixi and conda-lock are both tools that try to combine the conda and PyPI package ecosystem but this is hard to do because conda package names and PyPI package names do not necessarily match up.

Its hard to use open-source vulnerability databases because they often do not contain conda packages.
Using the PURL standard allows us to link vulnerabilities from other ecosystems to conda package.

## Rationale

Adding the information to the `repodata.json` file has some advantages:

* We can keep this information close to the conda package description.
* We can incrementally add `purls` through repodata patches.

The downside is that the (already large) repodata.json file will grow.

The `purls` field is an array because:

* A package might exist in multiple ecosystems
* A single conda package might repackage multiple other packages.

## Alternatives

Some work has been done to try and map conda package names to PyPI package names through the grayskull mapping:

https://raw.githubusercontent.com/regro/cf-graph-countyfair/master/mappings/pypi/grayskull_pypi_mapping.yaml

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
