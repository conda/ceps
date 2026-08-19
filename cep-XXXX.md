# CEP XXXX - Distribution of Sigstore Attestations for Conda Packages

<table>
<tr><td> Title </td><td> Distribution of Sigstore Attestations for Conda Packages </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Wolf Vollprecht &lt;wolf@prefix.dev&gt;</td></tr>
<tr><td> Created </td><td> Dec 02, 2025</td></tr>
<tr><td> Updated </td><td> Jul 23, 2026</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/142 </td></tr>
<tr><td> Implementation </td><td> https://prefix.dev (preview implementation) </td></tr>
<tr><td> Requires </td><td> CEP 27 (Publish Attestation) </td></tr>
</table>

> The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT",
  "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as
  described in [RFC2119][RFC2119] when, and only when, they appear in all capitals, as shown here.
>

## Abstract

This CEP defines how [Sigstore] attestations are distributed alongside conda packages.
Building upon [CEP 27], which standardizes the attestation format, it specifies how channels serve attestations via content-addressed `.sigs` sidecars and how repodata advertises them through a new `attestations_sha256` field.

This CEP intentionally covers only distribution and the minimal client requirements needed to discover sidecars, verify their hash, and bind attestations to package artifacts. Configuration, trust policy, lock files, and enforcement behavior are out of scope.

## Motivation

[CEP 27] defines a standard attestation format for the conda ecosystem using [in-toto] statements and [Sigstore] bundles. However, it explicitly leaves the distribution mechanism as future work:

> "This CEP does not specify a distribution mechanism for attestations (i.e., Sigstore bundles containing attestations)."

Without a standardized distribution mechanism, clients cannot reliably discover and retrieve attestations. This CEP addresses that gap by defining a simple, read-only HTTP sidecar endpoint that:

1. **Enables client verification**: Clients can fetch attestations alongside packages and verify them before installation.

2. **Supports multiple attestations**: A single package may have multiple attestations. For example, future workflows could attach attestations produced during build, during channel upload, or by third-party review processes.

3. **Works with existing infrastructure**: The sidecar file approach integrates naturally with static file hosting, CDNs, and mirrors.

4. **Follows ecosystem conventions**: Similar approaches are used by PyPI ([Integrity API][PyPI Integrity], standardized in [PEP 740]), npm ([provenance attestations][npm provenance]), and RubyGems ([release-gem][rubygems]).

## Scope

This CEP specifies the server side of attestation distribution and the minimal client behavior required for the mechanism to be sound. It does not specify:

- Client configuration or user interfaces
- Which signing identities a client should trust
- TOFU or lock-file formats and behavior
- Whether missing or invalid attestations warn, block installation, or are ignored

These policy decisions may be standardized separately.

## Specification

### Endpoint Definition

For any conda package artifact at URL:

```text
<channel_url>/<subdir>/<artifact_filename>
```

if the package has one or more attestations, the current sidecar MUST be available at both:

```text
<channel_url>/<subdir>/<artifact_filename>.sigs
<channel_url>/<subdir>/<artifact_filename>.sigs.<sha256>
```

The first URL is mutable and supports tools that discover attestations by appending `.sigs` to the artifact URL. It MUST serve the same bytes as the current sidecar advertised in repodata and SHOULD use `Cache-Control: no-cache`.

The second URL is content-addressed. Here, `<sha256>` is the 64-character lowercase hexadecimal hash advertised in repodata (see [Repodata changes](#repodata-changes)). Its bytes MUST NOT change, and the channel MUST retain the URL for as long as the package remains available.

To append attestations, a channel first publishes the new content-addressed sidecar, then updates the mutable `.sigs` URL, and finally updates repodata. Thus conda clients with either old or new repodata can fetch the corresponding immutable sidecar without a cache race.

Whether a package has attestations is advertised in the repodata index. Conda clients discover sidecars through repodata and use the content-addressed URL; generic Sigstore tooling may use the mutable `.sigs` URL. Packages without attestations need not have either sidecar URL.

#### Example

| Kind | Attestation URL |
| --- | --- |
| Mutable discovery | `https://example.com/channel/win-64/pkg-1.0-0.conda.sigs` |
| Content-addressed | `https://example.com/channel/win-64/pkg-1.0-0.conda.sigs.<sha256>` |

### Response Format

The sidecar MUST contain a JSON array of one or more [Sigstore bundles][Sigstore Bundle]. Each bundle represents one attestation for the package.

Channels MUST serve both URLs byte-for-byte identical to the current sidecar whose SHA256 hash is published in repodata (see [Repodata changes](#repodata-changes)). Channels MUST NOT re-serialize the JSON when serving it. The content-addressed URL is safe to host on static infrastructure (e.g. object storage or CDNs) and safe to cache and mirror by content hash.

#### Content-Type

The response SHOULD have `Content-Type: application/json`. Clients MUST NOT reject a sidecar based on the `Content-Type` header, since static file hosts do not always allow configuring it.

#### Schema

```json
[
  <Sigstore Bundle>,
  <Sigstore Bundle>,
  ...
]
```

Each element in the array MUST be a valid [Sigstore Bundle] as defined by the Sigstore specification.

### HTTP Status Codes

| Status Code     | Meaning                                  |
| --------------- | ---------------------------------------- |
| `200 OK`        | The sidecar file exists and was returned |
| `404 Not Found` | No sidecar file exists at this URL       |

Conda-client discovery goes through repodata, so clients MUST NOT infer anything about the existence of the package itself from a sidecar response. In particular, channels that do not implement this CEP may return `404 Not Found` for every sidecar URL, even when the underlying package exists.

For a package whose repodata record carries an `attestations_sha256` field, any failure to retrieve a sidecar matching the advertised hash — including a `404 Not Found` — is a retrieval failure (see [Client Requirements](#client-requirements)).

### Repodata changes

A package record in the repodata index (in `packages` or `packages.conda`, or the equivalent per-package record in sharded repodata per [CEP 16]) gains a new OPTIONAL `attestations_sha256` field:

```json
{
  "name": "foobar",
  "version": "1.2.3",
  "attestations_sha256": "37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570"
}
```

`attestations_sha256` MUST contain exactly 64 lowercase hexadecimal characters: the SHA256 hash of the sidecar bytes and the suffix of its content-addressed URL. Clients MUST reject any other value before constructing the URL.

The field MUST be present if and only if the package has a current sidecar containing at least one attestation. Its absence means no sidecar is advertised; clients MUST NOT treat this as an error and SHOULD NOT request a sidecar URL.

The field is the conda-client discovery and hash-binding mechanism for attestation sidecars:

1. **Discovery**: Conda clients learn from repodata alone whether a sidecar exists, avoiding a network round-trip for packages without attestations.
2. **Consistency**: Clients MUST verify that the fetched sidecar bytes hash to `attestations_sha256` before using them (see [Client Requirements](#client-requirements)). This detects modified responses relative to repodata; it does not protect against a source that can also rewrite repodata.
3. **Change detection**: When attestations are appended after a package was first published, the channel publishes a new content-addressed sidecar, updates the mutable URL, and updates the field. Mirrors and clients fetch the new immutable URL when the hash changes.

Tools that post-process repodata (e.g. hotfixing and patching pipelines) MUST preserve the `attestations_sha256` field. Channels using sharded repodata ([CEP 16]) update only the affected shard when attestations change, so clients pick up new attestations incrementally; consumers of monolithic `repodata.json` receive the update on the next regeneration.

### Attestation Requirements

Verification of [CEP 27] publish attestations, including binding the subject filename and SHA256 hash to the package artifact, MUST follow [CEP 27]. This CEP adds no publish-attestation verification rules.

Other predicate types MAY appear in the same sidecar, but this CEP does not define their verification rules. When a client verifies a recognized predicate type, it MUST apply that predicate type's specification. Clients MAY ignore or reject unrecognized predicate types according to local policy.

### Multiple Attestations

A package MAY have multiple attestations, provided each attestation intended to apply to the package artifact identifies that artifact according to the verification rules for its predicate type. This CEP does not define which attestations a client trusts or requires.

This CEP does not define upload authorization, channel admission policy, or access control for adding attestations. For example, a third party may produce an attestation, but the channel decides whether and how that attestation is accepted for distribution.

### Mirror Behavior

For every mirrored package record carrying an `attestations_sha256` field, mirrors and proxies MUST:

1. Fetch the content-addressed sidecar and verify its hash
2. Make the immutable sidecar available
3. Update the mutable `.sigs` URL to the same bytes
4. Publish the repodata that references it
5. Serve both URLs byte-for-byte, without modification
6. Retain old immutable sidecars for as long as the corresponding package remains available

A mirror that modifies sidecar bytes breaks the hash binding to repodata, and clients will treat its responses as retrieval failures. Mirrors MUST NOT infer that a package does not exist solely because an upstream sidecar endpoint returns `404 Not Found`.

## Client Requirements

A conda client that consumes attestation sidecars:

1. MUST discover sidecars through the repodata `attestations_sha256` field and use the content-addressed URL.
2. MUST reject an invalid `attestations_sha256` value before constructing the content-addressed URL.
3. MUST enforce an implementation-defined maximum size while streaming the sidecar and verify its hash before parsing it.
4. MUST treat an unavailable, oversized, malformed, or hash-mismatched advertised sidecar as a retrieval failure. The client MUST NOT use the sidecar or silently treat the package as having no attestations; the user-facing response is tool policy.
5. MUST follow [CEP 27] and the subject-binding rules in [Attestation Requirements](#attestation-requirements) when verifying a publish attestation.

## Security Considerations

The sidecar is served by the same infrastructure as the package it describes. Sigstore verification binds an attestation to a signing identity, but deciding which identities to trust is outside this CEP.

The repodata `attestations_sha256` value binds sidecar bytes to repodata and the content-addressed URL prevents cache races between sidecar revisions. The mutable `.sigs` URL provides discovery compatibility, not freshness or integrity, so conda clients use the content-addressed URL.

This does not protect against a source that can also rewrite repodata. A compromised channel origin can consistently rewrite the package, sidecar, and repodata; this is the same trust model that applies to packages today. A future repodata signing mechanism would extend to sidecar integrity because the `attestations_sha256` field is part of the signed content.

## References

- [CEP 16 - Sharded Repodata][CEP 16]
- [CEP 27 - Standardizing a publish attestation for the conda ecosystem][CEP 27]
- [Sigstore Bundle Specification][Sigstore Bundle]
- [in-toto Attestation Framework][in-toto]
- [PyPI Integrity API][PyPI Integrity]
- [npm Provenance Statements][npm provenance]
- [RubyGems release-gem][rubygems]
- [PEP 740 - Index support for digital attestations][PEP 740]

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

[RFC2119]: https://www.ietf.org/rfc/rfc2119.txt
[Sigstore]: https://sigstore.dev
[Sigstore Bundle]: https://github.com/sigstore/protobuf-specs/blob/main/protos/sigstore_bundle.proto
[in-toto]: https://in-toto.io
[CEP 16]: ./cep-0016.md
[CEP 27]: ./cep-0027.md
[PyPI Integrity]: https://docs.pypi.org/api/integrity/
[npm provenance]: https://docs.npmjs.com/generating-provenance-statements
[PEP 740]: https://peps.python.org/pep-0740/
[rubygems]: https://github.com/rubygems/release-gem
