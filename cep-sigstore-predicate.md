# CEP - Standardizing a publish attestation for the conda ecosystem

<table>
<tr><td> Title </td><td> Standardizing a publish attestation for the conda ecosystem </td>
<tr><td> Status </td><td> Proposed </td></tr>
<tr><td> Author(s) </td><td> Wolf Vollprecht &lt;wolf@prefix.dev&gt;</td></tr>
<tr><td> Created </td><td> Feb 18, 2025 </td></tr>
<tr><td> Updated </td><td> Feb 18, 2025</td></tr>
<tr><td> Discussion </td><td>  </td></tr>
<tr><td> Implementation </td><td>  </td></tr>
</table>

## Abstract

This CEP proposes a standard attestation layout for the conda ecosystem.
This attestation layout is based on the [in-toto] framework
and will enable further integration with signing schemes like
[Sigstore].

## Definitions and Concepts

- An **attestation** is a machine-readable cryptographically signed statement.
  When an attestation's signature is verified against a trusted key, that
  verification provides integrity and authenticity guarantees about the
  attestation's subject. For example:

    - Alice is the maintainer of the `widgets` package.
    - Alice signs a machine readable statement equivalent to the following
      English sentence, producing her attestation:

        > Alice published the `widgets` package at version v1.2.3 with
        > hash `sha256:abcd...` to the `conda-forge` channel.

    - Bob establishes trust in Alice's public key.
    - Bob can verify the attestation's signature against Alice's public key,
      giving him confidence that the statement is true.
    - Correspondingly, Bob can reject any statement for `widgets` that is not
      signed by Alice's public key.

- [in-toto] is a framework and standard for defining attestations.

    - Within in-toto, an attestation's statement is composed of a
      **subject** and a **predicate**. The subject is the resource
      (or resources) being attested to, and the predicate is a
      an arbitrary collection of metadata about the subject.
      The predicate is identified by a **predicate type**,
      which defines the predicate's expected schema.

- [Sigstore] is a project that enables misuse-resistant software signing
  and verification via short-lived certificates and a tamper-evident log.
  Sigstore composes with attestation frameworks like in-toto to provide
  transparency and misuse-resistance properties on top of the integrity
  and authenticity properties of attestations.

   One of Sigstore's major misuse-resistance contributions is
   the use of *ephemeral keys* for signing. Modifying the example above:

   - Instead of maintaining a long-lived signing key, Alice generates an
     *ephemeral key* and binds it to her *identity*
     ("`alice@trustme.example.com`").

     This binding is done via a certificate issued by [Fulcio], which verifies a
     *proof of possession* (such as from [OpenID Connect]) from Alice for her
     claimant identity. The certificate issued by Fulcio is, in turn auditable
     via [RFC 6962] Certificate Transparency (CT) logs.

    - Alice signs her attestation with her ephemeral key, and distributes a
      "bundle" containing both her attestation and her signing certificate.

    - Instead of establishing trust a long-lived key from Alice, Bob establishes
      trust in Alice's identity.

    - Bob can verify the attestation's signature against Alice's emphemeral key,
      which in turn can be verified as authentically Alice's via the Fulcio-
      issued certificate.

    With this flow, neither Alice nor Bob needs to maintain long-lived signing
    or verifying keyrings, in turn reducing the attacker surface for key
    compromise.

  Another key misuse-resistance contribution within Sigstore is *machine
  identities*. A machine identity behaves similarly to a human identity
  (Alice or Bob), but identifies a machine instead of a human. For example,
  `github.com/example/example/.github/workflows/release.yml@refs/tags/v1.2.3`
  could be the machine identity of a GitHub Actions workflow that ran from
  `release.yml` within `example/example` against the `v1.2.3` tag.

<!-- ### Sigstore Attestations

Sigstore attestations are cryptographic statements about software artifacts that provide:

- Authenticity: Proof of who created/signed the artifact
- Integrity: Verification that the artifact hasn't been tampered with
- Transparency: Public record of signatures in a tamper-evident log

### Key Components

- Predicates: JSON documents containing metadata about the signing event, using the `in-toto` format
- Signatures: Cryptographic proofs made using ephemeral keys
- Rekor: A tamper-evident log that stores attestations
- Fulcio: A certificate authority that issues short-lived certificates

In this document, we want to standardize the sigstore predicate for conda
packages. The bundle format to be used for sigstore attestations is the `v0.3`
bundle format. -->

## Motivation

The conda ecosystem contains metadata that answers the following questions,
in part or in full:

* _Who_ (or _what_) published this package?
* _What_ is the package's hash?
* _Where_ was this package _published from_, and where _to_?
* _When_ was this package published?

However, this metadata is not currently **cryptographically verifiable**:
the consuming party must either trust it as presented, or verify it manually
against independent sources of truth (such as a project's release history).

Attestations that present this metadata in a cryptographically
verifiable manner are desirable for a number of reasons:

* Package maintainers wish to demonstrate the integrity and authenticity
  of their package uploads;
* Individual downstream users wish to verify the integrity and authenticity of
  packages they consume, without placing additional trust in the
  channel or channel's hosting server;
* Attestations change the sophistication and risk profile for attackers in
  defenders' favor: the attacker must be sufficiently sophisticated
  to access private key material, *and* have a risk tolerance profile that
  accepts exposure via auditable transparency logs.

More broadly, attestation schemes like the one proposed in this CEP have
seen adoption in similar and related ecosystems:

* Python (PyPA/PyPI): [PEP 740] and [PyPI - Attestations]
* NodeJS (npm): [npm - Generating provenance statements]
* Ruby (RubyGems): [rubygems/release-gem]

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

The `subject` field is already defined in the in-toto specification and contains
the name of the package and its digest. For conda packages a SHA256 hash MUST be
used. The subject MUST be the full filename of the conda package that will be
part of the repodata.json and under which it will appear on the server.

The `predicateType` field is used to specify the schema of the predicate. The
`predicate` field contains the actual predicate data. We propose to publish a
schema to validate the `predicate` field. The schema will be available at
`https://schemas.conda.org/predicate-v1.json`.

The predicate MUST contain the `targetChannel` field, to indicate where the
package is being uploaded to. This field MUST be validated by the receiving
server. The channel MUST be in canonical form (full URL, no trailing slashes).

## Discussion

This predicate adds basic verifiable facts about the package. It will tie the
producer of the package to the target channel. This is similar to what PyPI has
implemented with the [PyPI publish
attestation](https://docs.pypi.org/attestations/publish/v1/). Since there is no
single authoritative index in the Conda world, we add the `targetChannel` field
to reach parity.

On the server, the certificate should be tested against the Trusted Publisher
used to upload the certificate to establish a chain of trust.

## Future work

Once sigstore attestations are established and more research has been done, we
might want to use the [SLSA (Supply-chain Levels for Software
Artifacts)](https://slsa.dev) spec as base for predicates in the conda
ecosystem.

[in-toto]: https://in-toto.io
[Sigstore]: https://sigstore.dev
[Fulcio]: https://github.com/sigstore/fulcio
[RFC 6962]: https://datatracker.ietf.org/doc/html/rfc6962
[OpenID Connect]: https://openid.net/connect/
[PEP 740]: https://peps.python.org/pep-0740/
[PyPI - Attestations]: https://docs.pypi.org/attestations/
[npm - Generating provenance statements]: https://docs.npmjs.com/generating-provenance-statements
[rubygems/release-gem]: https://github.com/rubygems/release-gem
