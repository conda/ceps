<table>
<tr><td> Title </td><td> CPython Version Support </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Travis Hathaway &lt;thathawa@anaconda.com&gt;</td></tr>
<tr><td> Created </td><td> May 18th, 2022</td></tr>
<tr><td> Updated </td><td> May 18th, 2022</td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
</table>

## Abstract

Decisions for which Python versions we support are currently made adhoc and in a manner
which is not easily predicted by the conda community. In order for this to be a more organized
process and to provide greater transparency, this document outlines the procedures we take to
add support for newer Python versions and how we drop support for older versions. Additionally,
this document outlines our official schedule for when we add support and begin testing for new
versions as well as when we drop support and stop testing for older version.

## Specification

Questions this section should answer:

- What is our exact schedule for new/old version support?
- Where will this schedule live? (presumably here but perhaps in the docs too)

## Motivation

The primary motivation behind this CEP is better transparency and planning around exactly
when new Python versions will be supported and when support for older versions will be dropped.

## Rationale 

Our rationale for this management closely follows the Python release cycles themselves:

[https://endoflife.date/python](https://endoflife.date/python)

## Backwards Compatibility

This CEP outlines a new strategy towards managing expectations about which Python versions
we support. As this is purely a process/procedure we follow, there is little chance for
backwards compatibility issues (i.e. there was previously no version management process
we followed that may be a source of conflict).

## Alternatives

This will provide a place to discuss potential alternatives to the proposed version
support schedule.

## Sample

Links to how other projects manage this can go here.

## FAQ

Please put FAQs here

## Resolution

TBD

## Reference

Please put references here.


## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
