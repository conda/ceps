
<table>
<tr><td> Title </td><td> Add plugin architecture to Conda </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Jannis Leidel <jleidel@anaconda.com></td></tr>
<tr><td> Created </td><td> Jun 29, 2021</td></tr>
<tr><td> Updated </td><td> Jun 30, 2021</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/1 </td></tr>
<tr><td> Implementation </td><td> (listed below) </td></tr>
</table>

## Motivation

Conda consists of many moving parts both in the `conda`/`conda-build`
projects as well as additional and even 3rd party projects. It relies
on loose coupling with various technical and workflow mechanisms.

Conda would profit from a generic plugin architecture because it would

* cover use cases that are underserved at the moment,
* support a better distribution of maintenance in the community,
* add the ability to extend Conda internals via official APIs
* and lower the barrier for contributions from other stakeholders
  in the Conda ecosystem.

## Implementation

* Integrate [pluggy](https://pluggy.readthedocs.io/) or
  [HookMan](https://github.com/ESSS/hookman) to host a set of hooks
  in Conda and allow external packages to provide plugins
  in addition to the default implementations shipped with Conda.

* Especially for performance critical code paths the plugin
  architecture would make it possible to work on innovative
  solutions instead of risking changes to the existing stable
  implementation.

## Rationale

Conda's architecture was not designed to extend it programmatically
with an official plugin API. It would profit from learning from
other tools in the Python ecosystem that have had plugins for years
(e.g. pytest, tox) and have a thriving well-maintained ecosystem.

At the same time Conda's special role as a tool written in Python
but existing in an ecosystem that tends to use the best tool for the
job, means that the plugin architecture should eventually
allow handling programming languages and technologies other than
Python.

It's also in the best interest for the health of the Conda project
to provide the means for the community to create innovative plugins for
Conda to cater to the ever-evolving Scientific community. Third
party contributors should use official APIs instead of having to
divert to workarounds and wrappers.

The CLI for example can already be extended with any command on the
`PATH` that follows the naming scheme `conda-([\w\-]+)$`
(or `conda-([\w\-]+)\.(exe|bat)$` on Windows). Unfortunately that
does not suffice to have an low-level integration with Conda internals.

So for deeper integrated functionality it's imperative to instead
provide code-level plugin hooks in Conda, e.g. where the solver
functionality that is currently implemented as a static mapping
for the libraries pycosat, pycryptosat and pysat.

Other example areas where this could be useful (not part of this CEP):

* shell integration

* dependency solver backend

* network adapter

* virtual package discovery

* build system integration

* language support (R, Julia, etc)

## Backward Compatibility

* Any plugin hook added to Conda should default to the way Conda works in
  the latest major release as of accepting its related CEP.

* Future updates to the defaults of the Conda plugin hooks should be
  reviewed for backward compatibility and follow clear a compatibility
  policy, e.g. only changed in major versions.

## References

* [Amy Williams about adding ability to replace default solver](https://github.com/conda/conda/issues/10271)
* [@jakirkham on adding plugin mechanism for detecting "virtual packages"](https://github.com/conda/conda/issues/10131)

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
