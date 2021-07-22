<table>
<tr><td> Title </td><td> Using the Mamba solver in Conda </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Jannis Leidel &lt;jleidel@anaconda.com&gt;</td></tr>
<tr><td> Created </td><td> Jul 20, 2021</td></tr>
<tr><td> Updated </td><td> Jul 22, 2021</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pulls/XX </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
</table>

## Abstract

[Conda]'s current default dependency solver based on [pycosat] has a number
of downsides that led to community efforts to write a faster and more
modern solver based on [libsolv]. The result was the basis for the
alternative Conda implementation called [Mamba].

The intention of this CEP is to propose an experimental feature for
Conda to add support for solver used in [Mamba], based on the plugin
architecture proposed in [CEP 2].

## Motivation

Conda's functionality and usability is predicated on the runtime
characteristics of its low-level dependency resolver since it's a
major part of its architecture -- next to the general CLI code
infrastructure, environment management and the handling of repo
and channel data.

Speed, accuracy, debuggability and other impacts on the user
experience are all heavily reliant on the underlying functionality of the
solver and Conda's ability to interpret and communicate it to the user.
For example long running calls of the Conda install command to resolve
complex environments and dependency trees directly impacts users'
real world experience of the package manager.

In addition, there is a wide-ranging proliferation of community efforts
to improve the usability issues with Conda outside the regular Conda
code project which makes it harder to retain a consistent technical
and community roadmap. As such the experimental integration of the Mamba
solver is to be considered but the first step to affect lasting change
in the Conda community and recognize the innovative solutions that have
been worked on by community members.

## Specificaton

Conda contains a solver registry in the `conda.resolve` module that
must be extended to using the plugin architecture mentioned in CEP 2.

Conda currently (4.10.x) supports three solvers:

- [pycosat] (default), a wrapper around the [PicoSAT] solver
- [pycryptosat], a wrapper around the CryptoMiniSat solver
- [pysat], a generic wrapper for a number of SAT solvers, Glucose4 is used

Depending on the outcome of [CEP 2], the existing solver registry should
be replaced by a mechanism to extend the registry using Conda "plugins",
which are defined as separately installed and maintained packages.

The default choice for the solver registry must stay the same as long
as the Mamba solver plugin is marked as experimental. Only after
considerable functional and integration testing to verify the performance
and solving improvements, it would be considered to be enabled as the
default -- in a new major version of Conda.

The metrics to consider the experiment to be successful are to be
determined as part of the work on this CEP.

## Backwards Compatibility

Given the differences in implementations and algorithms between the
already supported solvers, it's to be expected that Mamba's solver will
also produce slightly different solutions, depending to the requested
set of dependencies.

One prerequisite to implementing this CEP is it therefor to provide a
list of essential dependency solutions in the form of an automatic test
suite of expected solutions and a prose documentation of the minimal
viable solving behavior. Both will be the basis to determine the success
integration success of the Mamba solver to secure backward compatible
at a high degree.

Any potential backward incompatibilities discovered as part of this
work require formal documentation to be shared with the Conda users
and also inform the decision making around the status as an experimental
solver.

## Reference

- [Conda]: the Conda package manager
- [CEP 2]: Add plugin architecture to Conda
- [Libsolv]: the SAT solver that Mamba uses behind the scenes
- [PicoSAT]: the SAT solver wrapped by [pycosat]
- [Mamba]: the Conda community reimplementation

[CEP 2]: https://github.com/conda/ceps/pull/1
[libsolv]: https://github.com/openSUSE/libsolv
[pycosat]: https://pypi.org/project/pycosat/
[pycryptosat]: https://pypi.org/project/pycryptosat/
[pysat]: https://github.com/pysathq/pysat
[Mamba]: https://github.com/mamba-org/mamba
[PicoSAT]: http://fmv.jku.at/picosat/

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
