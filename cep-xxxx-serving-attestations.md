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

Without a standardized distribution mechanism, clients cannot reliably discover and retrieve attestations. This CEP addresses that gap by defining a simple, RESTful endpoint that:

1. **Enables client verification**: Clients can fetch attestations alongside packages and verify them before installation.

2. **Supports multiple attestations**: A single package may have multiple attestations (e.g., from the build system, from the channel on upload, from third-party auditors).

3. **Works with existing infrastructure**: The sidecar file approach integrates naturally with static file hosting, CDNs, and mirrors.

4. **Follows ecosystem conventions**: Similar approaches are used by PyPI ([Integrity API][PyPI Integrity]), npm ([provenance attestations][npm provenance]), and RubyGems.

## Specification

### Endpoint Definition

For any conda package artifact at URL:

```
<channel_url>/<subdir>/<artifact_filename>
```

Attestations MUST be available at:

```
<channel_url>/<subdir>/<artifact_filename>.sigs
```

#### Examples

| Package URL | Attestation URL |
|-------------|-----------------|
| `https://conda.anaconda.org/conda-forge/linux-64/numpy-2.0.0-py312h1234567_0.conda` | `https://conda.anaconda.org/conda-forge/linux-64/numpy-2.0.0-py312h1234567_0.conda.sigs` |
| `https://prefix.dev/my-channel/noarch/my-package-1.0.0-pyhd8ed1ab_0.conda` | `https://prefix.dev/my-channel/noarch/my-package-1.0.0-pyhd8ed1ab_0.conda.sigs` |
| `https://example.com/channel/win-64/pkg-1.0-0.tar.bz2` | `https://example.com/channel/win-64/pkg-1.0-0.tar.bz2.sigs` |

### Response Format

The `.sigs` endpoint MUST return a JSON array containing zero or more [Sigstore bundles][Sigstore Bundle]. Each bundle represents one attestation for the package.

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

Each element in the array MUST be a valid [Sigstore Bundle] as defined by the Sigstore specification. The bundle format supports multiple versions; implementations SHOULD support at least bundle versions v0.2 and v0.3.

#### Empty Response

If no attestations exist for a package, the endpoint MUST return an empty JSON array:

```json
[]
```

#### Example Response

The following is an abbreviated example of a `.sigs` response containing a single attestation:

```json
[
  {
    "mediaType": "application/vnd.dev.sigstore.bundle.v0.3+json",
    "dsseEnvelope": {
      "payload": "<base64-encoded in-toto statement>",
      "payloadType": "application/vnd.in-toto+json",
      "signatures": [
        {
          "keyid": "",
          "sig": "<base64-encoded signature>"
        }
      ]
    },
    "verificationMaterial": {
      "certificate": {
        "rawBytes": "<base64-encoded Fulcio certificate>"
      },
      "tlogEntries": [
        {
          "logIndex": "168604147",
          "logId": {
            "keyId": "<base64-encoded log ID>"
          },
          "kindVersion": {
            "kind": "dsse",
            "version": "0.0.1"
          },
          "integratedTime": "1738678814",
          "inclusionPromise": {
            "signedEntryTimestamp": "<base64-encoded SET>"
          },
          "inclusionProof": {
            "logIndex": "46699885",
            "rootHash": "<base64-encoded root hash>",
            "treeSize": "46699887",
            "hashes": ["<base64-encoded hashes>"],
            "checkpoint": {
              "envelope": "<signed checkpoint>"
            }
          },
          "canonicalizedBody": "<base64-encoded canonical body>"
        }
      ]
    }
  }
]
```

### HTTP Status Codes

| Status Code | Meaning |
|-------------|---------|
| `200 OK` | Attestations returned successfully (may be empty array) |
| `404 Not Found` | The package does not exist (distinct from "no attestations") |

Channels MUST return `200 OK` with an empty array `[]` when a package exists but has no attestations. Channels MUST return `404 Not Found` only when the underlying package does not exist.

This distinction allows clients to differentiate between:

- "This package has no attestations" (expected during transition period)
- "This package does not exist" (client error or tampering)

### Attestation Requirements

Each attestation in the response MUST comply with [CEP 27]. Specifically:

1. The in-toto statement's `subject[0].name` MUST match the artifact filename.

2. The in-toto statement's `subject[0].digest.sha256` MUST match the SHA256 hash of the artifact.

3. The `predicateType` MUST be `https://schemas.conda.org/attestations-publish-1.schema.json` or another registered predicate type.

### Multiple Attestations

A package MAY have multiple attestations from different sources. Common scenarios include:

| Source | Purpose |
|--------|---------|
| Build system (e.g., GitHub Actions) | Proves the package was built from specific source code |
| Channel operator | Proves the channel accepted and published the package |
| Third-party auditor | Proves the package passed security review |

When multiple attestations are present, they MUST all refer to the same artifact (same filename and SHA256 hash). Clients MAY choose which attestations to verify based on their trust policy.

### Mirror Behavior

Mirrors and proxies SHOULD:

1. Fetch and cache `.sigs` files alongside packages
2. Serve cached attestations without modification
3. Return `404` if the upstream `.sigs` endpoint returns `404`

TODO: specify further the desired behavior of mirrors.

## Client Behavior

### Verification Workflow

Clients implementing attestation verification SHOULD follow this workflow:

1. **Download package** from the channel (or use the SHA256 sum from the repodata.json)
2. **Fetch attestations** from `<package_url>.sigs`
3. **Verify each attestation** according to the client's trust policy:
   - Verify the Sigstore bundle signature
   - Verify the certificate chain to Fulcio root
   - Verify the transparency log inclusion proof
   - Verify the in-toto subject matches the downloaded package
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
    trusted_identities:
        - "https://github.com/foobar"
```

| Setting | Values | Behavior |
|---------|--------|----------|
| `enabled` | `true`/`false` | Enable or disable attestation fetching and verification |
| `require` | `error` | Fail if attestations are missing or invalid |
| | `warn` | Log warning but continue if attestations are missing or invalid |
| | `ignore` | Silently continue (still verify if attestations exist) |
| `trusted_identities` | List of patterns | Only accept attestations from matching Sigstore identities |

### Offline and Air-gapped Environments

For offline verification, clients MAY cache `.sigs` files alongside packages in local repositories
The Sigstore bundle format is self-contained and supports offline verification once the Sigstore trust root is available locally.

## Security Considerations

### Trust Model

The security of this scheme depends on:

1. **Sigstore infrastructure**: Fulcio CA, Rekor transparency log, and their availability
2. **Identity binding**: OIDC providers correctly authenticating signing identities
3. **Client trust policy**: Correctly configured trusted identities
4. **TLS security**: Secure transport when fetching attestations

### Threat Mitigations

| Threat | Mitigation |
|--------|------------|
| Forged attestations | Sigstore signatures are cryptographically verified against Fulcio certificates |
| Tampered attestations | Rekor transparency log provides tamper evidence |
| Replay attacks | In-toto subject binds attestation to specific artifact hash |
| Removed attestations | Rekor log entries are permanent; monitors can detect removal |
| Compromised signing identity | Transparency log enables detection; trust policy limits blast radius |

### Limitations

This scheme does NOT protect against:

1. Legitimate signers publishing malicious packages
2. Compromise of the Sigstore infrastructure itself
3. Incorrect client trust policies
4. Attacks before attestation was added to the package

## Backwards Compatibility

This proposal is fully backwards compatible:

1. **Existing channels**: No changes required; clients will receive `404` for `.sigs` endpoints
2. **Existing clients**: Will not request `.sigs` endpoints; behavior unchanged

The `.sigs` extension was chosen to avoid conflicts with existing URL patterns and file extensions in the conda ecosystem.

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
