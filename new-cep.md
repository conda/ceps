<table>
<tr><td> Title </td><td> Conda Version Support </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Travis Hathaway &lt;thathaway@anaconda.com&gt;</td></tr>
<tr><td> Created </td><td> May 19, 2022</td></tr>
<tr><td> Updated </td><td> May 19, 2022</td></tr>
<tr><td> Discussion </td><td>  NA </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
</table>

## Abstract

This CEP introduces an official version support policy to promote transparency and certainty 
about how long a specific version of conda will be supported. Going forward each version
will be classified as either "feature", "bugfix", "security" or "end-of-life". Versions classified
as "end-of-life" will not receive any support. In to order to determine this cut-off in an
educated manor, usage statistics were gathered about current conda usage, and we believe the appropriate
version cutoff should be `4.12`, meaning any version older than `4.12` will no longer be supported.
This CEP also includes detailed information about each version category stated above and its
effects on how the version will be supported.

## Specification

Version support will be broken down in to four separate categories as defined below:

- **Feature**, feature additions, bugfixes and security fixes
- **Bugfix**, bugfixes and security fixes
- **Security**, security fixes
- **End-of-life**, frozen and no bugfixes or security fixes will be added

The upcoming version will always fall into the "feature" category, and this is where all
active feature development will occur. The current release and the previous release will
fall in the "bugfix" category and will accept bugfixes and security fixes but will not
receive any feature additions. The third, fourth an fifth oldest releases will fall into
the "security" category and only receive security fixes. When possible conda users will
always be motivated to update to the most recent release.

Below is an example of how this version support schedule looks as of December 2022:

| Version | Category |
|---------|----------|
| 22.11.* | feature  |
| 22.9.*  | bugfix   |
| 4.14.*  | bugfix   |
| 4.13.*  | security | 
| 4.12.*  | security | 
| 4.11.*  | security | 

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

For many projects (more information here: https://endoflife.date), either only 
the latest version is supported or they have a sliding window of time
for their supported versions. This window is a guarantee saying that the 
version in question will be supported for a specific amount of time. For most who
use a version window, they further specify the types of fixes a version will receive
as it ages.

For conda, we decided to a use a version support window. Although using the latest
version of conda is typically recommended, we want to give our users flexibility
in knowing that they will not be expected to continuously upgrade in order to always
be using a supported version. Our release schedule is about every two months, and 
we believe that this is too frequent to be asking our users to update. We hope this
gives our users more time to prepare for upcoming versions and when their version 
will reach end-of-life.

## Backwards Compatibility

Highlight backwards compatibility issues here.

## Alternatives

- **Indefinitely support all conda versions ever:** not sustainable or practical for the development team.
- **Only support the latest version:** not fair to users who may want to run one or 
  two releases behind the current release. Additionally our release schedule is about
  once every two months which would be too frequent for many users.

## FAQ

Please put questions that may come up in this section.

## Resolution

This section contains the final decision on this issue.

## Reference

Helpful websites and articles:

- https://endoflife.date
- https://pip.pypa.io/en/latest/development/release-process/#supported-versions
- https://devguide.python.org/versions/


## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
