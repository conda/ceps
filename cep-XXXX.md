# CEP XXXX - PURLs for conda packages

<table>
<tr><td> Title </td><td> Package-URLs (PURLs) for conda packages </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Cheng H. Lee &lt;clee@anaconda.com&gt; </td></tr>
<tr><td> Created </td><td> 2026-04-02 </td></tr>
<tr><td> Updated </td><td> 2026-04-02 </td></tr>
<tr><td> Discussion </td><td> ... </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
</table>


## Abstract

This CEP describes the Package-URL type definition for conda packages in a way that conforms to
other relevant standards, including other CEPs and ECMA-427.


## Motivation

Package URLs (PURLs) provide "a standardized, URL-based syntax that uniquely identifies software
packages, independent of their ecosystem or distribution channel".  Users may want or need to use
PURLs to identify conda packages in various contexts, including but not limited to, software bills
of materials (SBOMs), vulnerability reporting, and cross-ecosystem compatibility.

However, the [existing conda PURL definition][purl-conda-def] fails to properly capture the
multi-stakeholder nature of the conda ecosystem, various commonly-understood concepts within the
ecosystem, and critically, the standards specified in other accepted CEPs.  This CEP seeks to
address such shortcomings with an ecosystem-approved specification for the conda PURL definition.


## Specification

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT",
"RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as
described in BCP 14 ([RFC2119][RFC2119], [RFC8174][RFC8174]) when, and only when, they appear in
all capitals, as shown here.

For the purposes of this CEP, the phrase "existing conda PURL definition" refers to the [commit
a6c97bc version of `types/conda-definition.json`][purl-conda-def], which is canonically available
in the https://github.com/package-url/purl-spec repository.

For the purposes of this CEP, references to sections of [ECMA-427][ECMA427] are relative to the 1st
Edition (December 2025) of that standard.

### ECMA-427 PURL components

ECMA-427 Section 5 ("Package-URL specification") states:

> A PURL is a URL composed of seven components:  
>   scheme:type/namespace/name@version?qualifiers#subpath

For conda PURLs, these seven components are defined as follows:

#### `scheme` component

In accordance with ECMA-427 Section 5.6.1 ("Scheme"), the `scheme` component for a conda PURL is
the ASCII string literal "pkg".  Systems handling conda PURLs SHOULD also follow the other rules
for the `scheme` component specified in ECMA-427 Section 5.6.1.

#### `type` component

In accordance with ECMA-427 Section 5.6.2 ("Type"), the canonical form for a conda PURL's `type`
component is the ASCII string literal "conda".  The `type` component MUST be treated as
case-insensitive, and system handling conda PURLs are encouraged to normalize the `type` component
to its canonical lowercase form, following the behaviors specified in ECMA-427 Section 5.5.

#### `namespace` component

Roughly speaking, the `namespace` component of a conda PURL corresponds to the path and label name
components of the [channel base URL defined in CEP 26](./cep-0026.md#channel-base-urls) and/or the
concept most users have when using the `channel` configuration option supported by [most]
conda-compatible tools.

For conda PURLs, the ECMA-427 Section 6.5.1 requirement property for the `namespace` component is
optional.  However, the use or non-use of the `namespace` component within a conda PURL MUST
conform to the following rules:

- If the `namespace` component is omitted from a conda PURL, then the `repository_url` qualifier
  MUST be explicitly provided in the PURL, and its value MUST be a valid channel base URL, as
  defined in CEP 26.
- If the `namespace` component is provided, each ECMA-427 Section 5.6.3 `namespace` segment MUST be
  a valid channel base URL path component, as defined in CEP 26.  All other rules for the
  `namespace` component specified in ECMA-417 Section 5.6.3 apply to conda PURLs, including the
  requirement that segments within a PURL `namespace` MUST be separated by a single unencoded
  ASCII "/" (slash) character.
- If the `namespace` component is provided, then the concatenation of the `repository_url`
  qualifier, a single unencoded ASCII "/" (slash) character, and the `namespace` component MUST be
  a valid channel base URL, as defined in CEP 26.
- The string literals "defaults" and "local" MUST NOT be used as the entire value of the
  `namespace` component.  This prohibition exists to minimize potential confusion with the
  reserved, user-configurable [multi-]channel names supported by many conda-compatible clients.
- The final path component of `namespace` SHOULD NOT match any channel subdir name, as this can
  lead to ambiguous PURLs and channel base URLs, as noted in CEP 26.  If platform information is
  needed to properly identify the package(s), then the `subdir` qualifier (defined below) should be
  used instead.

An important implication of these rules is that a valid conda PURL must provide at least one of the
`namespace` component or the `repository_url` qualifier, as a conda PURL that both omits the
`namespace` component _and_ assumes the default value for the `repository_url` qualifier (defined
below) specifies a channel base URL that is insufficient to properly locate the package.

Further, the prohibition on using "defaults" as the `namespace` component value means that PURLs
for Anaconda-built packages should use "main", "r", or "msys2" for their `namespace` component.

#### `name` component

The `name` component MUST be the [distributable package name](./cep-0026.md#package-names) of the
identified artifact(s), as defined in CEP 26.

Conda PURLs SHOULD NOT be used to identify conda virtual packages since they do not correspond to
any concrete [package] artifact and only exist on the client side.

#### `version` component

The `version` component MUST be the [package version string](./cep-0026.md#version-strings), as
defined in CEP 26.

#### `qualifiers` component

The following `qualifiers` are defined for conda PURLs:

- `repository_url`: Optional qualifier, with a default value defined in the "`repository` property"
  section of this CEP.  Its value, when combined with any `namespace` component as described in the
  "`namespace` component" section, MUST specify the channel base URL of the identified package(s),
  as defined in CEP 26.
- `build`: Optional qualifier, with no default value.  If provided, its value MUST be the
  [build string](./cep-0026.md#build-strings), as defined in CEP 26, of the identified package(s).
- `build_number`: Optional qualifier, with no default value.  If provided, its value MUST the
  [build number](./cep-0034.md#infoindexjson), as defined in CEP 34, of the identified package(s).
- `subdir`: Optional qualifier, with no default value.  If provided, its value MUST be the
  [channel subdir name](./cep-0026.md#subdir-names), as defined in CEP 26, of the identified
  package(s).
- `type`: Optional qualifier, with no default value.  If provided, its value MUST be exactly one of
  [currently-recognized artifact extensions](./cep-0026.md#artifact-extensions) or its versioned
  synonym, as defined in CEP 26.  At the time of this CEP's adoption, the accepted values are
  `tar.bz2` (versioned synonym: `v1`), or `conda` (versioned synonym: `v2`).
- `checksum`:  Optional qualifier, with no default value.  If provided, its value MUST consist of
  one or more checksum specifications, with consecutive checksum specifications separated by a
  single, unencoded ASCII "," (comma) character.  Each checksum specification is defined as the
  concatenating of the lowercase checksum algorithm name (e.g., "md5", "sha256"); a single,
  unencoded ":" (colon) character; and the lowercase, hex-encoded checksum value.

  The lowercase checksum algorithm name MUST only contain the ASCII lowercase characters `a-z` and
  digits `0-9`.  The recommended way to specify checksum algorithms whose names are commonly
  written with upper case and/or non-alphanumeric characters such as dashes (e.g., "SHA-1",
  "SHA-256") is to simply remove any non-alphanumeric characters in the commonly-written name and
  lowercase the remaining string.

  The lowercase hex-encoded checksum value MUST only contain the ASCII lowercase characters `a-f`
  and digits `0-9`.  The checksum value is explicitly understood to be a hexadecimal value, so
  commonly-used prefixes and postfixes (e.g., "0x" and "_16", respectively) MUST NOT be included as
  part of the checksum value.

  Historically, the conda ecosystem has used the MD5 and SHA-256 algorithms for checksumming
  packages; see, e.g., [CEP 16][CEP16], [CEP 32][CEP32], and [CEP 36][CEP36].  Given this and the
  sub-optimal security properties of MD5, the RECOMMENDED algorithm for the `checksum` qualifier is
  SHA-256.

Qualifiers in conda PURLs SHALL conform with all the rules specified ECMA-427 Section 5.6.6
("Qualifiers"), with the key words "shall", "shall not", and "may" in ECMA-427 Section 5.6.6 being
interpreted as their BCP 14 equivalents "SHALL", "SHALL NOT", and "MAY", respectively.
Importantly, this means that the entirety of any `repository_url` value, including colons (`:`) and
slashes (`/`), must be percent-encoded in accordance with ECMA-427 Section 5.4.

Since existing CEPs do not define a strict relationship between a package artifact's build string
and build number, this CEP does not require that the `build` and `build_number` qualifiers in a
conda PURL be mutually exclusive.  Further, it does specify which of these two qualifiers takes
precedence in cases where their simultaneous use in a conda PURL creates a conflict.  Producers of
conda PURLs should take care that their use of these qualifiers does not create a conflict, and
consumers of conda PURLs are RECOMMENDED to treat conflicting use of these qualifiers as an invalid
or erroneous PURL.

This CEP explicitly _undefines_ the `channel` qualifier found in the [existing conda PURL
definition][purl-conda-def].  The `channel` qualifier corresponds to a weakly-defined concept not
properly captured in any existing CEP, and its presumed purpose in the existing definition is
better handled by the combination of the `namspace` component and `repository_url` qualifier, as
described in this CEP.  Upon acceptance of this CEP, systems handling conda PURLs SHOULD treat
PURLs containing a `channel` qualifier as invalid.

To avoid the need for potentially complex precedence rules in this CEP, the [commonly-used
qualifiers][purl-quals-guide] `filename` and `download_url` used by other PURL types are explicitly
_not_ defined for conda PURLs.  In other words, the `filename` and `download_url` qualifiers MUST
NOT be accepted when processing conda PURLs.  Should such values be needed to handle a conda PURL,
they should be constructed from the other components and qualifiers defined in this CEP and the
rules defined in CEP 26.

#### `subpath` component

The optional `subpath` component of a conda PURL is used to specify a path within the identified
package(s), subject to the following:

- The `subpath` component SHALL confirm to all rules specified in ECMA-427 Section 5.6.7
  ("Subpath"), with the key words "shall", "shall not", and "may" in ECMA-427 Section 5.6.7 being
  interpreted as their BCP 14 equivalents "SHALL", "SHALL NOT", and "MAY", respectively.
- The `subpath` component MUST be treated as case-sensitive.
- If the `subpath` component identifies a symbolic link with the package(s), the `subpath`
  component MUST be interpreted as a reference to the symbolic link file itself and _not_ as a
  reference to the target path after the symbolic link has been partially or fully dereferenced.
- When applied to [`tar.bz2`-/`v1`-format packages][CEP35.v1], "relative to the root of the
  package" in ECMA-427 Section 5.6.7 MUST be interpreted as the path to an archive member within
  the package tarball, or equivalently, as a relative path from a root directory into which the
  package tarball was extracted.
- When applied to [`conda`-/`v2`-format packages][CEP35.v2], "relative to the root of the package"
  in ECMA-427 Section 5.6.7 MUST be interpreted as a relative path from a common root directory
  into which both inner archives (i.e., `info-{name}-{version}-{build}.tar.zst` and
  `pkg-{name}-{version}-{build}.tar.zst`) have been extracted.
- The `subpath` component MUST be interpreted as a reference to a path as it exist in the package
  artifact(s), and _not_ as a reference to a path after any modifications that may have occurred
  when the package artifact(s) are processed by conda-compatible clients (e.g., prefix replacement,
  pre- or post-link scripts, etc.).

The last three rules are intended to ensure consistent interpretation of the `subpath` component,
regardless of the actual package format and processing system.  Note that these rules imply that
conda PURLs cannot be used to directly identify the `metadata.json` nor the inner `.tar.zst`
archives within `conda`-/`v2`-format packages.

### Other ECMA-427 root object properties

ECMA-427 Section 6 ("Package-URL Type Definition Schema") specifies other required and optional
properties for a PURL type definition.  For conda PURLs, these properties are defined as follows:

#### `type name` property

The ECMA-427 Section 6.2 `type name` property of the conda PURL type definition SHALL be "Conda".

#### `description` property

The ECMA-427 Section 6.3 `description` property of the conda PURL type definition SHALL be
"Conda packages".

#### `repository` property

The ECMA-427 Section 6.4 `repository` property is REQUIRED for conda PURLs.  Its use and
interpretation is defined in the "`namespace` component" and "`qualifier` component" sections.

To maintain compatibility with the default behavior of existing conda-compatible clients, the
default public repository (i.e., `default_repository_url`) for conda packages is SHALL be
"https://conda.anaconda.org".

#### `examples` property

The ECMA-427 Section 6.10 `PURL examples` property of the conda PURL type definition SHALL consist
of the PURLs listed in the "Examples" section of this CEP.

#### `reference_urls` property

The ECMA-427 Section 6.12 `reference_urls` property for the conda PURL type definition SHALL be a
list consisting of:

- The canonical URL of this CEP

Note that ECMA-427 Section 6.12 specifies that the URLs listed in the `reference_urls` PURL type
definition are informative.  However, to ensure standardized implementations, this CEP SHOULD be
treated as normative and not just informative.


## Examples

- `pkg:conda/main/python`: basic usage, identifying [all] `python` packages from Anaconda
- `pkg:conda/conda-forge/python@3.13.12?build=hc97d973_100_cp313&subdir=linux-64`: basic usage,
  identifying a specific `python` build from conda-forge.
- `pkg:conda/python?repository_url=https%3A%2F%2Frepo.anaconda.com%2Fpkgs%2Fmain`: using the
  `repository_url` qualifier to fully identify the channel base URL
- `pkg:conda/conda-forge/python?repository_url=https%3A%2F%2Fprefix.dev`: using the
  `repository_url` qualifier to identify packages hosted by a conda-forge mirror.


## Backwards Compatibility

This CEP intentionally breaks backwards-compatibility for PURLs based on the [existing conda PURL
definition][purl-conda-def] in the following ways:

- The `default_repository_url` has been changed from `https://repo.anaconda.com` to
  `https://conda.anaconda.org`.
- The requirement property of the `namespace` component has changed from "prohibited" to
  "optional", with additional rules as described above.
- `channel` is no longer an accepted qualifier for conda PURLs.

These breaking changes are considered acceptable by the author(s) of this CEP, as the existing
conda PURL definition fails to properly capture existing standards (i.e., CEPs) and commonly-used
patterns in the conda ecosystem.  Among the motivations for these breaking changes:

- Simple PURLs like `pkg:conda/python` and `pkg:conda/python?channel=conda-forge` are accepted
  under the existing conda PURL definition but cannot be used to identify actual package artifacts,
  as that definition's default values produces non-existent URLs.  The existing conda PURL
  definition effectively requires that _every_ conda PURL explicitly provide a `repository_url`
  qualifier, possibly combined with a `channel` qualifier in an unspecified way, to produce a URL
  that would correspond to an actual package artifact.
- The prohibition of a `namespace` component in the existing conda PURL definition means
  commonly-used patterns in the conda ecosystem (e.g., `channel::package=version`) cannot be
  translated to "intuitive"-/similar-looking PURLs (e.g., `pkg:conda/channel/package@version`).
  Coupled with the previously-noted choice of [existing] default values, this creates an unwanted
  UX burden when using conda PURLs.


## Implementation Notes

Upon approval of this CEP by conda steering council, the CEP author(s) will submit the necessary
changes to the [Github `package-url/purl-spec`](https://github.com/package-url/purl-spec)
repository needed to make its conda PURL type definition and any other related files conformant
with this standard.


## Future Work

- ECMA-427 allows for the specification of case-sensitivity and normalization rules as properties
  of various PURL components (e.g., namespaces, names, versions).  This CEP intentionally leaves
  such properties ambiguous or undefined, as no accepted standards within the conda ecosystem
  unambiguously state what the values of such [ECMA-427] properties should be.  The conda PURL type
  definition should be updated appropriately if/when the conda ecosystem standardizes on such
  case-sensitivity and normalization rules.
- CEP 27 allows `file://` URLs to be channel base URLs, and the diversity of file systems and their
  behaviors may lead to conflicts with the requirements in this CEP and/or ECMA-427.  To avoid
  making this CEP overly complicated, the author(s) have intentionally chosen to defer any work
  needed to properly handle [certain types of] `file://`-based channels, especially since it is
  unclear if PURLs are meaningfully useful for such channels.
- The specifications for the `subpath` component may not be fully complete with respect to every
  type of path (i.e., file or directory) that could possibly be included in conda packages.
  Updates to this CEP or additional CEPs may be needed if any gaps are identified in the `subpath`
  component specifications.
- This CEP provides the `repository_url` qualifier that can be used identify a package on a
  _specific_ mirror of a channel.  However, this CEP does _not_ define a way to identify a specific
  package artifact that appears across multiple mirrors; e.g., a single PURL that would
  [simultaneously] identify a conda-forge package hosted on both `conda.anaconda.org/conda-forge`
  and `prefix.dev/conda-forge`.  Supporting such PURLs would require additional work, including
  formalizing the concept of "mirrors" for conda channels and specifying which PURL components or
  qualifiers should be used to identify the set of mirrors for a given packages.  (Due to the
  fairly portable nature of conda packages, the combination is [shortened] channel name, package
  name, version string, and build string may not be sufficient to uniquely identify across all
  possible repositories.)


## References

### Normative References

- [RFC2119][RFC2119]: Key words for use in RFCs to Indicate Requirement Levels
- [RFC8174][RFC8174]: Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words
- [ECMA-427][ECMA427]: Package-URL (PURL) specification, 1st edition, December 2025
- [CEP 26][CEP26]: Identifying Packages and Channels in the conda Ecosystem
- [CEP 34][CEP34]: Contents of conda packages
- [CEP 35][CEP35]: Distributable package artifacts file formats


### Informative References

- [PURL Qualifiers Guidance][purl-quals-guide]
- [CEP 16][CEP16]: Sharded Repodata
- [CEP 32][CEP32]: Management and structure of conda environments
- [CEP 33][CEP33]: Version literals and their ordering
- [CEP 36][CEP36]: Package metadata files served by conda channels

<!-- Links -->
[RFC2119]: https://www.ietf.org/rfc/rfc2119.txt
[RFC8174]: https://www.ietf.org/rfc/rfc8174.txt
[ECMA427]: https://ecma-international.org/publications-and-standards/standards/ecma-427/
[CEP16]: ./cep-0016.md
[CEP26]: ./cep-0026.md
[CEP32]: ./cep-0032.md
[CEP33]: ./cep-0033.md
[CEP34]: ./cep-0034.md
[CEP35]: ./cep-0035.md
[CEP35.v1]: ./cep-0035.md#tarbz2
[CEP35.v2]: ./cep-0035.md#conda
[CEP36]: ./cep-0036.md
[purl-conda-def]: https://github.com/package-url/purl-spec/blob/a6c97bcfe5c83985a1da348f73a65c9842c7e354/types/conda-definition.json
[purl-quals-guide]: https://github.com/package-url/purl-spec/blob/a6c97bcfe5c83985a1da348f73a65c9842c7e354/docs/common-qualifiers.md


## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
