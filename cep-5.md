<table>
<tr><td> Title </td><td> Migration to Grayskull from conda-skeleton </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Mahe Iram Khan &lt;miramk163@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> March 29, 2022</td></tr>
<tr><td> Updated </td><td> _ _, 2022</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda-incubator/grayskull/issues/306 </td></tr>
</table>

## Abstract

conda-skeleton, the conda recipe generator, unfortunately is not well maintained. It is also deeply integrated with conda build itself. Grayskull, a community innovation, on the other hand is a stand alone conda recipe generator. Migrating away from conda-skeleton and adopting Grayskull as the de facto conda recipe generator would allow easy maintainence and faster generation of recipes.

## Other sections

**Specification**
Grayskull presently supports the generation of recipes from PyPI and Python packages on GitHub. To make the migration from conda-skeleton to Grayskull, it is required to add more package origins to Grayskull. Adding R support to Grayskull is already a work in progress.
Below is a table comparing the various package repositories supported by conda-skeleton and Grayskull for recipe generation.

<table>
<tr><td> **Package Repository** </td><td> **Supported by conda-skeleton** </td><td> **Supported by Grayskull** </td>
<tr><td> **PyPI** </td><td> Yes </td><td> Yes </td></tr>
<tr><td> **CRAN** </td><td> Yes</td><td> WIP </td></tr>
<tr><td> **CPAN** </td><td> Yes </td></td> No </td></tr>
<tr><td> **Luarocks** </td><td> Yes </td><td> No </td></tr>
<tr><td> **rpm** </td><td> Yes </td><td> No </td></tr>
</table>

**Motivation**
Why the proposed change is needed.

conda-skeleton is poorly maintained and is deep integrated with conda-build. This makes it harder to make changes and improvements to conda-skeleton without breaking something in conda-build itself. Grayskull is a community-developed conda recipe generator. It is a standalone tool and is a major improvement upon conda-skeleton.

  * Generates recipes faster than conda-skeleton (conda-skeleton generates Pytest recipe in 31 sec, whereas Grayskull generates it in 4 sec)
  * Detects noarch:python, conda-skeleton does not.
  * Detects compilers, conda-skeleton does not.

The Grayskull codebase is highly modular and hence easy to understand, follow and maintain.

**Backwards Compatibility**
Will the proposed change break existing packages or workflows

Backwards compatibility is maintained.


* FAQ -- Frequently asked questions (and answers to them).
* Resolution -- A short summary of the decision made by the community.
* Reference -- Any references used in the design of the CEP.

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
