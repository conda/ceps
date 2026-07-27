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
> More specifically, violations of a MUST or MUST NOT rule MUST result in an error. Violations of the
  rules specified by any of the other all-capital terms MAY result in a warning, at discretion of the
  implementation.

## Abstract

This CEP defines how [Sigstore] attestations are distributed alongside conda packages and how clients consume them.
Building upon [CEP 27], which standardizes the attestation format, this proposal specifies how channels serve attestations via a `.sigs` sidecar endpoint, how the repodata index advertises and integrity-protects sidecars through a new `attestations` field, and the client-side configuration for discovering, verifying, and enforcing policy on attestations. Together, these enable verification of package integrity and provenance.

## Motivation

[CEP 27] defines a standard attestation format for the conda ecosystem using [in-toto] statements and [Sigstore] bundles. However, it explicitly leaves the distribution mechanism as future work:

> "This CEP does not specify a distribution mechanism for attestations (i.e., Sigstore bundles containing attestations)."

Without a standardized distribution mechanism, clients cannot reliably discover and retrieve attestations. This CEP addresses that gap by defining a simple, read-only HTTP sidecar endpoint that:

1. **Enables client verification**: Clients can fetch attestations alongside packages and verify them before installation.

2. **Supports multiple attestations**: A single package may have multiple attestations. For example, future workflows could attach attestations produced during build, during channel upload, or by third-party review processes.

3. **Works with existing infrastructure**: The sidecar file approach integrates naturally with static file hosting, CDNs, and mirrors.

4. **Follows ecosystem conventions**: Similar approaches are used by PyPI ([Integrity API][PyPI Integrity], standardized in [PEP 740]), npm ([provenance attestations][npm provenance]), and RubyGems ([release-gem][rubygems]).

## Specification

### Endpoint Definition

For any conda package artifact at URL:

```text
<channel_url>/<subdir>/<artifact_filename>
```

if the package has one or more attestations, they MUST be available at:

```text
<channel_url>/<subdir>/<artifact_filename>.sigs
```

Whether a package has attestations is advertised in the repodata index (see [Repodata changes](#repodata-changes)). Clients discover sidecars through repodata rather than by probing `.sigs` URLs; packages without attestations need not have a sidecar file at all.

#### Examples

| Package URL                                                                         | Attestation URL                                                                          |
| ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `https://conda.anaconda.org/conda-forge/linux-64/numpy-2.0.0-py312h1234567_0.conda` | `https://conda.anaconda.org/conda-forge/linux-64/numpy-2.0.0-py312h1234567_0.conda.sigs` |
| `https://prefix.dev/my-channel/noarch/my-package-1.0.0-pyhd8ed1ab_0.conda`          | `https://prefix.dev/my-channel/noarch/my-package-1.0.0-pyhd8ed1ab_0.conda.sigs`          |
| `https://example.com/channel/win-64/pkg-1.0-0.tar.bz2`                              | `https://example.com/channel/win-64/pkg-1.0-0.tar.bz2.sigs`                              |

### Response Format

The `.sigs` file MUST contain a JSON array of one or more [Sigstore bundles][Sigstore Bundle]. Each bundle represents one attestation for the package.

The sidecar is a static artifact: channels MUST serve it byte-for-byte identical to the file whose SHA256 hash is published in the repodata `attestations` field (see [Repodata changes](#repodata-changes)). Channels MUST NOT re-serialize the JSON when serving it. This makes the sidecar safe to host on static infrastructure (e.g. object storage or CDNs) and safe to cache and mirror by content hash.

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

Attestation discovery goes through repodata, so clients MUST NOT infer anything about the existence of the package itself from a `.sigs` response. In particular, channels that do not implement this CEP may return `404 Not Found` for every `.sigs` URL, even when the underlying package exists.

For a package whose repodata record carries an `attestations` field, any failure to retrieve a sidecar matching the advertised hash — including a `404 Not Found` — is a retrieval failure and MUST be handled according to the client's `require` policy (see [Configuration](#configuration)).

### Repodata changes

A package record in the repodata index (in `packages` or `packages.conda`, or the equivalent per-package record in sharded repodata per [CEP 16]) gains a new OPTIONAL `attestations` field:

```json
{
  "name": "foobar",
  "version": "1.2.3",
  "attestations": {
    "sha256": "37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570",
    "size": 4842
  }
}
```

- `sha256` (REQUIRED): the SHA256 hash of the exact bytes of the `.sigs` file as served.
- `size` (REQUIRED): the size of the `.sigs` file in bytes.

The field MUST be present if and only if at least one attestation is available for the package. Its absence means the package has no attestations; clients MUST NOT treat an absent field as an error and SHOULD NOT request the `.sigs` URL in that case.

The field is the single discovery and integrity mechanism for attestation sidecars:

1. **Discovery**: Clients learn from repodata alone whether a `.sigs` file exists, avoiding a network round-trip for packages without attestations.
2. **Integrity**: Clients MUST verify that the fetched `.sigs` bytes hash to `sha256` before using the sidecar (see [Verification Workflow](#verification-workflow)). This prevents a mirror or intermediary from stripping or replacing attestations without detection.
3. **Change detection**: When attestations are added after a package was first published, the channel publishes an updated `.sigs` file and updates the field. Mirrors and clients re-fetch the sidecar when the hash changes.
4. **Resource bounds**: `size` allows clients to enforce a download limit before fetching, protecting against accidentally downloading oversized sidecars. It is a pre-flight hint rather than a security mechanism: clients MUST also enforce their limit on the actual bytes received. Clients MAY refuse to download sidecars larger than a locally configured limit; such a refusal MUST be handled like a retrieval failure (see [Configuration](#configuration)).

Tools that post-process repodata (e.g. hotfixing and patching pipelines) MUST preserve the `attestations` field. Channels using sharded repodata ([CEP 16]) update only the affected shard when attestations change, so clients pick up new attestations incrementally; consumers of monolithic `repodata.json` receive the update on the next regeneration.

### Attestation Requirements

This CEP defines discovery and distribution of attestations. Verification of publish attestations MUST follow [CEP 27].

If a bundle contains a [CEP 27] publish attestation, then:

1. The in-toto statement's `subject[0].name` MUST match the artifact filename.

2. The in-toto statement's `subject[0].digest.sha256` MUST match the SHA256 hash of the artifact.

3. The `predicateType` MUST be `https://schemas.conda.org/attestations-publish-1.schema.json`.

CEP 27 publish attestations intentionally describe a single package artifact. Other predicate types MAY appear in the same `.sigs` response, but this CEP does not define their verification rules. When a client verifies a bundle with a recognized predicate type, it MUST apply the verification rules of that predicate type's specification. Clients MAY ignore or reject unrecognized predicate types according to local policy.

### Multiple Attestations

A package MAY have multiple attestations, provided each attestation intended to apply to the package artifact identifies that artifact according to the verification rules for its predicate type. Clients MAY choose which attestations to verify based on their trust policy.

This CEP does not define upload authorization, channel admission policy, or access control for adding attestations. For example, a third party may produce an attestation, but the channel decides whether and how that attestation is accepted for distribution.

### Mirror Behavior

Mirrors and proxies treat `.sigs` sidecars like any other channel artifact. They SHOULD:

1. Mirror the `.sigs` file for every package whose repodata record carries an `attestations` field
2. Serve the file byte-for-byte, without modification
3. Re-fetch a mirrored sidecar when the `attestations.sha256` value in the mirrored repodata changes

A mirror that modifies sidecar bytes breaks the hash binding to repodata, and clients will treat its responses as retrieval failures. Mirrors MUST NOT infer that a package does not exist solely because the upstream `.sigs` endpoint returns `404 Not Found`.

## Client Behavior

### Verification Workflow

Clients implementing attestation verification SHOULD follow this workflow:

1. **Check repodata**: If the package's repodata record has no `attestations` field, the package has no attestations. Handle this per the `require` policy for missing attestations and skip the remaining attestation steps.
2. **Download the package** from the channel.
3. **Fetch the sidecar** from `<package_url>.sigs` and verify that its bytes hash to the `attestations.sha256` value from repodata. On a mismatch or fetch failure, the client SHOULD retry once with refreshed repodata, since the sidecar may have been updated concurrently. A persistent mismatch is a retrieval failure and MUST be handled per the `require` policy.
4. **Verify each attestation** using the verification process defined by [CEP 27] or by the attestation's predicate type (see [Attestation Requirements](#attestation-requirements)).
5. **Accept or reject** the package based on the verification results and the `require` policy.

### Configuration

Clients SHOULD support the following configuration options:

```yaml
# Abstract example of Sigstore configuration:
attestations:
  conda-forge:
    enabled: true
    require: warn  # "error", "warn", or "ignore"
    trusted_identities:
      - identity: "https://github.com/conda-forge/*"
        issuer: "https://token.actions.githubusercontent.com"
      - identity: "https://github.com/my-org/*"
        issuer: "https://token.actions.githubusercontent.com"
  https://prefix.dev/foobar:
    enabled: true
    require: warn
    trusted_identities:
      - identity: "https://github.com/foobar"
        issuer: "https://token.actions.githubusercontent.com"
```

Each channel entry MUST specify `enabled`, `require`, and `trusted_identities`; clients MUST NOT infer default values for omitted fields.

| Setting              | Values                               | Behavior                                                   |
| -------------------- | ------------------------------------ | ---------------------------------------------------------- |
| `enabled`            | `true`/`false`                       | Enable or disable attestation fetching and verification    |
| `require`            | `error`/`warn`/`ignore`              | How to respond to attestation problems (see below)         |
| `trusted_identities` | List of `(identity, issuer)` entries | Only accept attestations from matching Sigstore identities |

#### `require` semantics

Three classes of attestation problems exist:

- **Missing**: the package's repodata record has no `attestations` field.
- **Retrieval failure**: the sidecar cannot be fetched, exceeds the client's size limit, or its bytes do not match the repodata `sha256`.
- **Verification failure**: a bundle fails verification for its predicate type, or no attestation matches `trusted_identities`.

| `require` | Missing | Retrieval failure | Verification failure |
| --------- | ------- | ----------------- | -------------------- |
| `error`   | fail    | fail              | fail                 |
| `warn`    | warn    | warn              | warn                 |
| `ignore`  | silent  | warn              | warn                 |

"Fail" means the package MUST NOT be installed; "warn" means the client MUST log a warning and MAY continue. `ignore` accepts packages without attestations silently, but retrieval and verification failures are potential tampering signals and MUST NOT be silently swallowed: they are handled as under `warn`.

#### `trusted_identities` matching

A Sigstore signing identity is the *pair* of the certificate identity (the SubjectAlternativeName of the signing certificate) and the OIDC issuer that authenticated it. The same SubjectAlternativeName authenticated by two different issuers constitutes two different identities, so each `trusted_identities` entry MUST specify both fields:

- `identity`: a pattern matched against the SubjectAlternativeName. Matching is case-sensitive and literal, except that `*` matches any sequence of characters, including `/`.
  For example, `https://github.com/conda-forge/*` matches `https://github.com/conda-forge/numpy-feedstock/.github/workflows/build.yml@refs/heads/main` but not `https://github.com/conda-forge-evil/...`, because the literal prefix includes the trailing slash.
- `issuer`: the OIDC issuer URL (e.g. `https://token.actions.githubusercontent.com` for GitHub Actions). Issuers are compared literally; patterns are not supported.

An attestation matches an entry only when the SubjectAlternativeName matches `identity` **and** the certificate's OIDC issuer equals `issuer`. Clients MUST NOT accept attestations based on the identity pattern alone.

Clients MAY offer shorthand notations that expand deterministically to `(identity, issuer)` entries (for example, deriving the GitHub Actions issuer from a `github:owner/repo` form), provided the expansion is documented and the underlying policy always contains both fields.

### Offline and Air-gapped Environments

For offline verification, clients MAY cache `.sigs` files alongside packages in local repositories.
The Sigstore bundle format is self-contained and supports offline verification once the Sigstore trust root is available locally.

Clients SHOULD refresh the Sigstore trust root regularly — for example, on the update cadence of the Sigstore TUF repository — so they do not miss trust-root changes, including key revocations and newly trusted keys. Clients SHOULD warn when verifying against a trust root older than a configurable threshold. In air-gapped environments, deployments SHOULD establish an out-of-band process for updating the trust root alongside the mirrored packages.

## Security Considerations

The `.sigs` sidecar is served by the same infrastructure as the package it describes: an attacker who can modify the package artifact can equally modify or remove the sidecar. The mechanisms in this CEP layer as follows:

- **Sigstore verification** binds each attestation to a signing identity, that is, the pair of certificate identity and OIDC issuer. An attacker cannot forge attestations for identities they do not control, but an attacker who controls the distribution path can substitute attestations signed by an identity they *do* control. The `trusted_identities` policy, because it pins both the identity pattern and the issuer, is what turns bundle verification into a guarantee about who produced the package.
- **The repodata `attestations` hash** binds the sidecar bytes to the repodata. An intermediary (mirror, CDN, proxy) that strips or rewrites a sidecar is detected by the client's hash check, provided the client obtained repodata from a trusted source.
- The strength of the hash binding is bounded by the integrity of repodata itself, which is currently protected by transport security to the channel origin. A compromised channel origin can consistently rewrite the package, the sidecar, and the repodata. This is the same trust model that applies to packages today. A future repodata signing mechanism would automatically extend to sidecar integrity, since the `attestations` field is part of the signed content.
- `require: warn` and `require: ignore` do not block installation on failure. Deployments that rely on attestations as a security control MUST use `require: error` together with a restrictive `trusted_identities` list.

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
