# CEP XXXX - Distribution of Sigstore Attestations for Conda Packages

<table>
<tr><td> Title </td><td> Distribution of Sigstore Attestations for Conda Packages </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Wolf Vollprecht &lt;wolf@prefix.dev&gt;</td></tr>
<tr><td> Created </td><td> Dec 02, 2025</td></tr>
<tr><td> Updated </td><td> Dec 02, 2025</td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> https://prefix.dev (preview implementation) </td></tr>
<tr><td> Requires </td><td> CEP 27 (Publish Attestation) </td></tr>
</table>

> The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT",
  "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as
  described in [RFC2119][RFC2119] when, and only when, they appear in all capitals, as shown here.

## Abstract

This CEP defines a standard endpoint for distributing [Sigstore] attestations alongside conda packages. Building upon [CEP 27], which standardizes the attestation format, this proposal specifies how channels serve attestations to clients via a `.sigs` sidecar endpoint, enabling verification of package integrity and provenance.

## Motivation

[CEP 27] defines a standard attestation format for the conda ecosystem using [in-toto] statements and [Sigstore] bundles. However, it explicitly leaves the distribution mechanism as future work:

> "This CEP does not specify a distribution mechanism for attestations (i.e., Sigstore bundles containing attestations)."

Without a standardized distribution mechanism, clients cannot reliably discover and retrieve attestations. This CEP addresses that gap by defining a simple, read-only HTTP sidecar endpoint that:

1. **Enables client verification**: Clients can fetch attestations alongside packages and verify them before installation.

2. **Supports multiple attestations**: A single package may have multiple attestations, such as attestations produced during build, during channel upload, or by other review processes.

3. **Works with existing infrastructure**: The sidecar file approach integrates naturally with static file hosting, CDNs, and mirrors.

4. **Follows ecosystem conventions**: Similar approaches are used by PyPI ([Integrity API][PyPI Integrity]), npm ([provenance attestations][npm provenance]), and ([RubyGems][rubygems]).

## Specification

### Endpoint Definition

For any conda package artifact at URL:

```text
<channel_url>/<subdir>/<artifact_filename>
```

For channels implementing this CEP, attestations MUST be available at:

```text
<channel_url>/<subdir>/<artifact_filename>.sigs
```

#### Examples

| Package URL                                                                         | Attestation URL                                                                          |
| ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `https://conda.anaconda.org/conda-forge/linux-64/numpy-2.0.0-py312h1234567_0.conda` | `https://conda.anaconda.org/conda-forge/linux-64/numpy-2.0.0-py312h1234567_0.conda.sigs` |
| `https://prefix.dev/my-channel/noarch/my-package-1.0.0-pyhd8ed1ab_0.conda`          | `https://prefix.dev/my-channel/noarch/my-package-1.0.0-pyhd8ed1ab_0.conda.sigs`          |
| `https://example.com/channel/win-64/pkg-1.0-0.tar.bz2`                              | `https://example.com/channel/win-64/pkg-1.0-0.tar.bz2.sigs`                              |

### Response Format

For channels implementing this CEP, the `.sigs` endpoint MUST return a JSON array containing zero or more [Sigstore bundles][Sigstore Bundle]. Each bundle represents one attestation for the package.

#### Content-Type

The response MUST have `Content-Type: application/json`.

#### Schema

```json
[
  <Sigstore Bundle>,
  <Sigstore Bundle>,
  ...
]
```

Each element in the array MUST be a valid [Sigstore Bundle] as defined by the Sigstore specification.

#### Empty Response

If no attestations exist for a package, the endpoint MUST return an empty JSON array:

```json
[]
```

### HTTP Status Codes

| Status Code     | Meaning                                                                                         |
| --------------- | ----------------------------------------------------------------------------------------------- |
| `200 OK`        | The package exists and attestations were returned successfully (the array may be empty)         |
| `404 Not Found` | For channels implementing this CEP, the package does not exist                                  |

Channels that support attestations MUST return `200 OK` with an empty array `[]` when the package exists but no attestations are available for it.

For backwards compatibility, clients MUST NOT use a `404 Not Found` response from the `.sigs` endpoint alone to determine whether a package exists. Channels that do not implement this CEP may return `404 Not Found` for every `.sigs` URL, even when the underlying package exists. Clients that need to determine package existence MUST use the channel's package metadata or the package artifact URL itself.

### Repodata changes

The repodata index is changed to include a new `attestations` field that MUST contain the SHA256 hash of the signatures file.

```json
{
  "name": "foobar",
  "version": "1.2.3",
  "attestations": "37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570"
}
```

This hash allows mirrors and clients to detect changes to the `.sigs` sidecar, including attestations added after the package was first published, and re-fetch the sidecar when it changes.

### Attestation Requirements

This CEP defines discovery and distribution of attestations. Verification of publish attestations MUST follow [CEP 27].

Each element in the response MUST be a valid [Sigstore Bundle]. If a bundle contains a [CEP 27] publish attestation, then:

1. The in-toto statement's `subject[0].name` MUST match the artifact filename.

2. The in-toto statement's `subject[0].digest.sha256` MUST match the SHA256 hash of the artifact.

3. The `predicateType` MUST be `https://schemas.conda.org/attestations-publish-1.schema.json`.

CEP 27 publish attestations intentionally describe a single package artifact. Other predicate types MAY appear in the same `.sigs` response, but this CEP does not define their verification rules. Clients MUST verify each recognized predicate type according to its own specification and MAY ignore or reject unrecognized predicate types according to local policy.

### Multiple Attestations

A package MAY have multiple attestations, provided each attestation intended to apply to the package artifact identifies that artifact according to the verification rules for its predicate type. Clients MAY choose which attestations to verify based on their trust policy.

This CEP does not define upload authorization, channel admission policy, or access control for adding attestations. For example, a third party may produce an attestation, but the channel decides whether and how that attestation is accepted for distribution.

### Mirror Behavior

Mirrors and proxies SHOULD:

1. Fetch and cache `.sigs` files alongside packages
2. Serve cached attestations without modification
3. Use the repodata `attestations` hash to detect changed `.sigs` sidecars
4. Re-fetch a cached `.sigs` sidecar when the repodata `attestations` hash changes
5. Preserve upstream `404 Not Found` responses for `.sigs` URLs when the upstream channel does not provide a sidecar

Mirrors MUST NOT infer that a package does not exist solely because the upstream `.sigs` endpoint returns `404 Not Found`.

## Client Behavior

### Verification Workflow

Clients implementing attestation verification SHOULD follow this workflow:

1. **Download package** from the channel
2. **Fetch attestations** from `<package_url>.sigs`
3. **Verify each attestation** using the verification process defined by [CEP 27] or by the attestation's registered predicate type.
4. **Accept or reject** the package based on verification results

### Configuration

Clients SHOULD support the following configuration options:

```yaml
# Example ~/.condarc configuration
attestations:
  conda-forge:
     enabled: true
     require: warn  # "error", "warn", or "ignore"
     trusted_identities:
       - "https://github.com/conda-forge/*"
       - "https://github.com/my-org/*"
  https://prefix.dev/foobar:
    enabled: true
    require: warn
    trusted_identities:
        - "https://github.com/foobar"
```

Each channel entry MUST specify `enabled`, `require`, and `trusted_identities`; clients MUST NOT infer default values for omitted fields.

| Setting              | Values           | Behavior                                                        |
| -------------------- | ---------------- | --------------------------------------------------------------- |
| `enabled`            | `true`/`false`   | Enable or disable attestation fetching and verification         |
| `require`            | `error`          | Fail if attestations are missing or invalid                     |
|                      | `warn`           | Log warning but continue if attestations are missing or invalid |
|                      | `ignore`         | Silently continue (still verify if attestations exist)          |
| `trusted_identities` | List of patterns | Only accept attestations from matching Sigstore identities      |

### Offline and Air-gapped Environments

For offline verification, clients MAY cache `.sigs` files alongside packages in local repositories.
The Sigstore bundle format is self-contained and supports offline verification once the Sigstore trust root is available locally.

Clients MUST periodically update the Sigstore trust root so they do not miss trust-root changes, including key revocations and newly trusted keys.

## References

- [CEP 27 - Standardizing a publish attestation for the conda ecosystem][CEP 27]
- [Sigstore Bundle Specification][Sigstore Bundle]
- [in-toto Attestation Framework][in-toto]
- [PyPI Integrity API][PyPI Integrity]
- [npm Provenance Statements][npm provenance]
- [PEP 740 - Index support for digital attestations][PEP 740]

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

[RFC2119]: https://www.ietf.org/rfc/rfc2119.txt
[Sigstore]: https://sigstore.dev
[Sigstore Bundle]: https://github.com/sigstore/protobuf-specs/blob/main/protos/sigstore_bundle.proto
[in-toto]: https://in-toto.io
[CEP 27]: ./cep-0027.md
[PyPI Integrity]: https://docs.pypi.org/api/integrity/
[npm provenance]: https://docs.npmjs.com/generating-provenance-statements
[PEP 740]: https://peps.python.org/pep-0740/
[rubygems]: https://github.com/rubygems/release-gem
