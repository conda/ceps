<table>
<tr><td> Title </td><td> Remove <code>&ast</code>; from valid version characters </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Antoine Prouvost &lt;antoine.prouvost@quantstack.net&gt; </td></tr>
<tr><td> Created </td><td> July 18, 2023 </td></tr>
<tr><td> Updated </td><td> July 18, 2023 </td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
</table>


## Abstract
We recommend to remove ``*`` from valid ``Version`` characters, due to confusing intersection with
``VersionSpec`` glob expressions.
We suggest different possibilities on how the character could be reinterpreted in ``VersionSpec``
with an analysis on backward compatibility.


## Motivation
### Suprising examples
In Conda, ``*`` is a valid version character that is smaller that any string.
For instance ``1.1* < 1.1alpha < 1.1``.
Strings following a separator (typically a ``.``) are implicitly assumed to start with a ``0``, so
we further have ``1.1.* == 1.1.0* < 1.1.0``.

When we further consider ``VerionSpec`` (sets of versions), both ``.*`` and ``*`` suffixes can
alternatively be interpreted as a glob expression.

We have the following in ``conda``.

| VersionSpec | Version operand | ``1.7.0`` matches |
|-------------|-----------------|-------------------|
| ``1.7.*``   | ``1.7``         | True              |
| ``1.7*``    | ``1.7``         | True              |
| ``=1.7.*``  | ``1.7``         | True              |
| ``=1.7*``   | ``1.7*``        | False             |
| ``==1.7.*`` | ``1.7``         | True              |
| ``==1.7*``  | ``1.7*``        | False             |
| ``!=1.7.*`` | ``1.7``         | False             |
| ``!=1.7*``  | ``1.7*``        | True              |

Using ``==``, ``<``, ``<=``, ``>``, ``>=`` comparison operator, ``*`` suffix is always parsed
with the version, and ``.*`` always dropped (with a warning but users may not see it, for instance
if the spec is used in a recipe).

| VersionSpec | Version operand | ``1.7.0alpha`` matches |
|-------------|-----------------|------------------------|
| ``>=1.7.*`` | ``1.7``         | False                  |
| ``>=1.7*``  | ``1.7*``        | True                   |

Core maintainers from [Mamba](github.com/mamba-org/mamba),
[Rattler](github.com/mamba-org/rattler), and [Conda-Forge](https://conda-forge.org/) failed to
properly predict which version would match the aforementionned version specs.
regular users would be all the more surprised of the difference, especially when ``*`` is not a
usual version character (_e.g._ not in Python [PEP440](https://peps.python.org/pep-0440/)).

### Why was the ``*`` character introduced
_Note this is a best effort explanation done by the author of this CEP._

Conda versions can have arbitrarily many ``.`` separated segements, each containing arbitrarily
many alternation of strings and numbers.
For instance ``1.1 == 1.1.0 == 1.1.0.0 == ...``, and ``1.1 < 1.1p < 1.1p1 < 1.1p1p < ...1``.
In a finite semantic verisioning scheme, such as Python PEP440, when asking for a spec
"_matching all the versions starting with 1.1" (_i.e._ ``=1.1*`` in Conda), one could use
``>=1.1.0a0`` and ``<1.2.0a0`` to represent the spec as an interval.
This is a convenient representation that ease working with specs, especially to compute set
intersections.

However, since in Conda we have ``1.1.0a0 > 1.1.0a0a0 > 1.1.0a0a0a0 > ...``, there are no smallest
version that can be used as a lower bound for such interval.
As a comparison, this would be like searching for a decimal to represent the lower bound of the
interval ``>π`` (the mathematical constant).
Hence, the ``*`` character, conveniently not used in practice in versions, was used to represent
this "version" that does not exist but that is useful for representing intervals
(``>1.1*,<1.2*`` in the above example).
We refer to this "imaginary" version as the _``1.1`` infimum_ in the rest of this proposal.

But that special version should always have stayed an implementation detail and never leak into
the set of valid versions, as allowing so breaks it purpose when considering the spec ``1.1*.0*``.
The special character ``*`` should also have been limited to a single appearance per version,
otherwise we can repeat the infinitly decreasing sequence ``1.1* > 1.1*.0* > 1.1*.0*.0* > ...``
of versions in that start with ``1.1``.


## Rationale
We searched through the ``repodata.json`` of all subdirs of the ``anaconda``, ``conda-forge``,
and ``bioconda`` channels and found that:
 - No ``"version"`` field of any package contains a ``*``
 - Occurences of ``>1.1*``, ``>1.1.*``, ``>=1.1*``, ``>=1.1.*``
 - Few occurences of ``<1.1*`` (on bioconda), ``<1.1.*``, no occurence of ``<=1.1*`` and ``<=1.1.*``
 - Single occurence of ``==2.6*`` (dep on Python bioconda neve matching) and no occurence of ``=1.1*``


## Specification
### [V1] Version
Given that no version currently contains the ``*`` character, we reommend to simply forbid ``*``
inside a version.
 - The public API of ``Version`` must fail to create/parse a version from string contaning ``*``.
 - ``Version`` must not serialize to any string containing a ``*``.
 - ``repodata.json`` and the like must not contain a ``*`` in any of the ``"version"`` fields.

Note that ``*`` can still be used internally to represent these special infimum "versions".

### VersionSpec
#### [VS1] Equality and startswith
For equality (``==`` and no prefix operators) and starts with (``=`` operator) we advocate to always
interpret ``*`` as a glob expression.
From the motivation section, this would change the behaviour of ``=1.7*`` and ``==1.7*``.
Since no version where found containing a ``*``, the only occurence of such version spec are
most likely a mistake.

We further argue to make a difference between ``.*`` and ``*`` suffixes to make their meaning
closer to glob expresions.
- ``1.7*`` should match version starting with ``1.7``, that is for instance _including_ ``1.7alpha``;
- ``1.7.*`` should match anything starting with ``1.7.``, that is _excluding_ ``1.7alpha``.

Currently, in ``conda``, only ``=1.7`` is matching ``1.7alpha``.

#### [VS2] Relational comparison operators ``>``, ``>=``, ``<``, ``<=``
This is the most delicate part to handle since ``>1.7*`` is frequently use to mean greater than the
``1.7`` infimum (could also be writen as ``=1.7|>=1.7``, that is, mathching some versions smaller
than ``1.7.0``, such as ``1.7alpha``).

##### [VS2A] Replace the ``*``
``conda`` is already ignoring ``.*`` suffixes on these operators.
We could extend that to the ``*`` suffix, making the breaking change that ``>1.7*`` and the like
would no longer match pre and alpha releases.
In Conda-Forge, pre and alpha releases are kept in separate channels, so the impacts are not as
important.

However, this solution has the downside of not long being able to represent version infima.
This could be reintroduced with a new operator, such as ``>inf(1.7)`` or ``>-1.7``.
Conda-Forge also has a
[repodata patching tool](https://github.com/conda-forge/conda-forge-repodata-patches-feedstock)
for globally migrating package metadata.


##### [VS2B] Reinterpret the ``*``
Alternatively, we could reinterpret ``>1.7*`` as a comparison on the set of versions starting with
``1.7``.

``>=1.7*`` could be understood as _greater than at least one version in the ``1.7`` set_.
This has no breakage with the current use of ``>=1.7*``.
With a symetric meaning, ``<=1.7*`` would be a breaking change, but this is seldom used (not used
in the ``repodata.json`` surveyed).

As for ``>1.7*``, it could become equivalent to ``>=1.7*`` in order to minimize breakage, or
be reinterpreted to _greater than all versions in the ``1.7`` set_ (hence equivalent to ``>=1.8*``).
The latter is (subjectively) more intuitive.
For ``<1.7*`` the breakage is reversed, but this is again not used as often.

As for the equality operator in [VS1], we suggest ``>1.7*`` and ``1.7.*`` to have different meaning.

## Copyright
All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
