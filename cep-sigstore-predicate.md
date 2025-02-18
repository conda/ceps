# CEP - Standardizing the v1 predicate for sigstore attestations

<table>
<tr><td> Title </td><td> Standardizing the v1 predicate for sigstore attestations </td>
<tr><td> Status </td><td> Proposed </td></tr>
<tr><td> Author(s) </td><td> Wolf Vollprecht &lt;wolf@prefix.dev&gt;</td></tr>
<tr><td> Created </td><td> Feb 18, 2025 </td></tr>
<tr><td> Updated </td><td> Feb 18, 2025</td></tr>
<tr><td> Discussion </td><td>  </td></tr>
<tr><td> Implementation </td><td>  </td></tr>
</table>

## Abstract

We want to standardize attestations for the conda ecosystem.

### Sigstore Attestations

Sigstore attestations are cryptographic statements about software artifacts that provide:

- Authenticity: Proof of who created/signed the artifact
- Integrity: Verification that the artifact hasn't been tampered with
- Transparency: Public record of signatures in a tamper-evident log

### Key Components

- Predicates: JSON documents containing metadata about the signing event, using the `in-toto` format
- Signatures: Cryptographic proofs made using ephemeral keys
- Rekor: A tamper-evident log that stores attestations
- Fulcio: A certificate authority that issues short-lived certificates

In this document, we want to standardize the sigstore predicate for conda packages. The bundle format to be used for sigstore attestations is the `v0.3` bundle format.

## Specification

The in-toto predicate should contain the following fields:

```json
{
    "_type": "https://in-toto.io/Statement/v0.1",
    "subject": [{
        "name": "file-name-0.0.1-h123456_5.conda",
        "digest": {"sha256": "..."}, ...
    }],
    // Schema URL
    "predicateType": "https://schemas.conda.org/predicate-v1.json",
    "predicate": {
        // Canonical URL of the target channel
        "targetChannel": "https://prefix.dev/conda-forge",
    }
}
```

The `subject` field is already defined in the in-toto specification and contains the name of the package and its digest.
For conda packages a SHA256 hash MUST be used.
The subject MUST be the full filename of the conda package that will be part of the repodata.json and under which it will appear on the server.

The `predicateType` field is used to specify the schema of the predicate. The `predicate` field contains the actual predicate data.
We propose to publish a schema to validate the `predicate` field. The schema will be available at `https://schemas.conda.org/predicate-v1.json`.

The predicate MUST contain the `targetChannel` field, to indicate where the package is being uploaded to. This field MUST be validated by the receiving server. The channel MUST be in canonical form (full URL, no trailing slashes).

## Discussion

This predicate adds basic verifiable facts about the package. It will tie the producer of the package to the target channel.
This is similar to what PyPI has implemented with the [PyPI publish attestation](https://docs.pypi.org/attestations/publish/v1/). Since there is no single authoritative index in the Conda world, we add the `targetChannel` field to reach parity.

On the server, the certificate should be tested against the Trusted Publisher used to upload the certificate to establish a chain of trust.

## Future work

Once sigstore attestations are established and more research has been done, we might want to use the [SLSA (Supply-chain Levels for Software Artifacts)](https://slsa.dev) spec as base for predicates in the conda ecosystem. 