<table>
<tr><td> Title </td><td> Conda Version Support </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Travis Hathaway &lt;thathaway@anaconda.com&gt;</td></tr>
<tr><td> Created </td><td> May 19, 2022</td></tr>
<tr><td> Updated </td><td> March 23, 2023</td></tr>
<tr><td> Discussion </td><td>  NA </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
</table>

## Abstract

This CEP introduces an official version support policy to promote transparency and certainty 
about which versions of conda are supported. The policy itself states that only the latest
released version of conda will be supported. Instead of patching previous releases, maintainers will only focus their efforts on new and current releases. The implications of
this and how this looks will be outlined below.

## Specification

The latest version of conda will be the only officially supported version of conda. This relates
only to the conda project itself (i.e. conda-build is not included). This means that the only
time patch releases will be made are soon after a release goes out. For example, if a
bug is identified soon after releasing conda `23.11.0` and fixed, a subsequent `23.11.1` 
release will be made. Patch releases for conda versions older than the current version
will not be made.

When a user is using a version older than the current version, we make no guarantees that
patches for this release will be made. If bugs are encountered with this particular release,
users will be encouraged to upgrade to the most recent release.

The conda project already commits to maintain backwards compatibility per CEP-9.
Any breaking changes will be announced ahead of time and go through our established
[deprecation schedule][deprecation-schedule].


## Motivation

The primary motivation for this CEP is setting clear expectations about how long
a particular version of conda will be supported. We do not expect our users to
always be running the latest version of conda, but we also do not want to give
users the impression that every version of conda will be supported indefinitely.
Therefore, we felt it necessary to outline with this CEP exactly which versions
will be supported and how. This not only helps set expectations for our users but 
also eases our development efforts knowing we no longer have to support older versions 
of conda.

## Rationale

For many projects (more information here: https://endoflife.date), either
the latest version is supported or the projects have a sliding window of time
for their supported versions. This window is a guarantee saying that the 
version in question will be supported for a specific amount of time. For most who
use a version window, they further specify the types of fixes a version will receive
as it ages.

For conda, we decided to not pursue a sliding window of supported versions. Instead,
we opted to only support the latest version. This was decided for a few reasons:

1. This is effectively what conda has already been doing. Very rarely in conda's history has a bugfix or security patch been released for an older version of conda, the standing policy has been to ask users to upgrade to the latest version.
2. It's relatively easy for users to update conda, so regular updates are highly encouraged.
3. Supporting multiple versions at any one point in time is burdensome, time consuming, and distracts from other valuable work our maintainers can be focused on instead.

## Alternatives

- **Indefinitely support all conda versions ever:** not sustainable or practical for our community stakeholders.
- **Support a sliding window of versions:** also not sustainable or practical for our community stakeholders.

## FAQ

_TBD_ (please add questions to the pull request for me to add)

## Resolution

This section contains the final decision on this issue.

## Reference

Helpful websites and articles:

- https://endoflife.date
- https://pip.pypa.io/en/latest/development/release-process/#supported-versions
- https://devguide.python.org/versions/


## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).


[deprecation-schedule]: https://github.com/conda-incubator/ceps/blob/main/cep-9.md