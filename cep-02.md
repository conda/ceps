
<table>
<tr><td> Title </td><td> Add plugin architecture to Conda </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Jannis Leidel <jleidel@anaconda.com></td></tr>
<tr><td> Created </td><td> Jun 29, 2021</td></tr>
<tr><td> Updated </td><td> Jun 29, 2021</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda-forge/conda-forge-enhancement-proposals/pull/6 </td></tr>
<tr><td> Implementation </td><td> (listed below) </td></tr>
</table>

## Motivation

Conda consists of many moving parts both in the `conda`/`conda-build`
projects as well as external and 3rd party projects that rely
on loose coupling with various technical and workflow mechanisms.

Conda would profit from an additional, generic plugin architecture
that

* can cover use cases underserved at the moment,
* would support a better distribution of code maintenance in the community,
* would add the ability to extend specific pieces of Conda internals,
* and reduce the effort needed by community members to contribute to
  the ecosystem.

## Implementation

* Integrate [pluggy](https://pluggy.readthedocs.io/) or
  [HookMan](https://github.com/ESSS/hookman) to host a set of hooks
  in Conda and allow external packages to provide plugins
  in addition to the default implementations.

* Especially for performance critical code paths the plugin
  architecture makes it possible to work on innovative
  alternatives instead of risking changes to the existing
  algorithm.

## Rationale

Conda's architecture was not designed to extend it programmatically
with an official plugin API and it would profit from learning from
other tools in the Python ecosystem that have had plugins for years
(e.g. pytest, tox).

At the same time Conda's special role as a tool written in Python
but existing in an ecosystem that tends to use the best tool for the
job, means that the plugin architecture should eventually
encompass other languages other than Python, too.

It's also in the best interest for the Conda project to provide
the means to the community to innovate parts of the project
to cater to the ever-evolving Scientific community and allow 3rd
party contributors to use official APIs instead of work arounds
and wrappers.

The CLI for example can already be extended with any command on the
`PATH` that follows the naming scheme `conda-([\w\-]+)$`
(or `conda-([\w\-]+)\.(exe|bat)$` on Windows). Unfortunately that
does not suffice to have an low-level integration with Conda internals.

So for deeper integrated functionality it's imperative to instead
provide code-level plugins to hook into Conda, e.g. the solver
functionality that is currently implemented as a static mapping
for the libraries pycosat, pycryptosat and pysat.

Other areas where this could be useful:

* shell integration

* dependency solver backend

* network adapter

* virtual package discovery

* build system integration

* language support (R, Julia, etc)

## Backward Compatibility

* Any plugin hook added to Conda should default to the way Conda works in
  the latest major release as of accepting this CEP.

* Future updates to the defaults of the Conda plugin hooks should be
  reviewed for backward compatibility and follow clear a compatibility
  policy, e.g. only changed in major versions.

## References

* [Amy Williams about adding ability to replace default solver](https://github.com/conda/conda/issues/10271)
* [@jakirkham on adding plugin mechanism for detecting "virtual packages"](https://github.com/conda/conda/issues/10131)

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
