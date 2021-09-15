<table>
<tr><td> Title </td><td> Deprecate `pip` interoperability and Default `pip` to have `--no-deps` in all environments </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Matthew R. Becker &lt;becker.mr@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> Sep 15, 2021</td></tr>
<tr><td> Updated </td><td> Sep 15, 2021</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/3 </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
</table>

## Abstract

Installing software from `pip` into `conda` environments creates huge hassels, especially for new users. It 
can lead to inconsistent or even broken environments with undefined behavior. This CEP proposed to have `conda`'s 
version of `pip` have the installation of dependencies turned off by default to ease the pain here. Additionally, 
this CEP proposes to deprecate the current `pip` interoperability feature. A correct implementation of this feature 
is nearly impossible and partial implementations create as many problems as they solve.

## Specification

1. The `pip` interoperability feature currently in `conda` is deprecated and never to be brought back forevermore.

2. The version of `pip` shipped with `conda` will default to have the equivalent of `--no-deps` turned on by default. 

3. An option in `conda` to allow `pip` to install dependencies would be added (e.g., `pip_allow_deps` in the `.condarc` or 
   at the command line).

## Alternatives

1. The biggest single alternative would be to develop a system to reconcile metadata across `pip` and `conda`. Indeed, such functionality 
already exists. However, maintaining and ensureing this system works in all of the various edge cases is next to impossible. 

2. One could limit `pip` interoperability to pure python (i.e., `noarch: python` in `conda` or the equivalent from pypi, e.g., `sdists`, etc.). 
Even this special case is complicated enough that the required work seems to exceed the potential gains. The simpler rules above allow for users 
to install software stacks like this on their own via opting-out.

## Reference

This CEP came out of a very nice discussion in the `conda` community call on 2021/15/09.

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
