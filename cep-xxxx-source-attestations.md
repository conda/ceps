# CEP XXXX - Source Attestation Verification in Recipes

<table>
<tr><td> Title </td><td> Source Attestation Verification in Recipes </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Wolf Vollprecht &lt;wolf@prefix.dev&gt;</td></tr>
<tr><td> Created </td><td> May 20, 2026</td></tr>
<tr><td> Updated </td><td> May 20, 2026</td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> https://github.com/prefix-dev/rattler-build (experimental) </td></tr>
<tr><td> Requires </td><td> CEP 14 (recipe format) </td></tr>
</table>

> The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT",
  "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as
  described in [RFC2119][RFC2119] when, and only when, they appear in all capitals, as shown here.

## Abstract

This CEP extends the conda recipe format ([CEP 14]) with an optional
`attestation` field on URL sources. The field lets recipe authors declare
that an upstream source archive carries a [Sigstore] attestation, and
specifies a minimum set of checks that any conformant builder MUST perform
before using the archive. The CEP standardizes the *recipe schema* only:
the attestation formats and predicate semantics themselves remain owned by
their upstream issuers (e.g. [PyPI][PyPI Integrity], GitHub Releases).

## Motivation

Recipes routinely download source tarballs from third-party hosts (PyPI,
GitHub Releases, project mirrors). Today the only integrity signal in the
recipe is a content hash — `sha256:` or `md5:` — which proves that the
bytes did not change since the recipe was last updated, but says nothing
about *who* produced them.

Several upstream ecosystems now publish [Sigstore] attestations alongside
their release artifacts:

- PyPI exposes [PEP 740][PEP 740] provenance through its [Integrity API][PyPI Integrity].
- GitHub releases can attach `.sigstore.json` bundles via [`actions/attest`][actions-attest].
- Other ecosystems (Rust crates, npm) are following similar patterns.

A recipe author who wants to bind their build to a specific upstream
publisher (e.g. "this Flask tarball must have been produced by the
`pallets/flask` GitHub Actions workflow") currently has no portable way
to express that intent. Tools that verify attestations do so with
out-of-band configuration that does not travel with the recipe.

This CEP closes that gap by:

1. Defining an `attestation` block on URL sources so the intent is
   recorded in the recipe itself, alongside `sha256` and `url`.
2. Defining a *minimum* set of checks that a conformant builder MUST
   perform when the block is present, so a verified build means the same
   thing across implementations.
3. Explicitly **not** redefining upstream predicate formats. PyPI's
   provenance schema, GitHub's bundle format, and the [in-toto] statement
   format are referenced as-is.

## Specification

### Recipe Schema

A URL source ([CEP 14], `source:` mapping with `url:`) MAY include an
`attestation` mapping:

```yaml
source:
  url: https://files.pythonhosted.org/packages/.../flask-3.1.1.tar.gz
  sha256: "6489f1..."
  attestation:
    publishers:
      - github:pallets/flask
    bundle_url: https://example.com/flask-3.1.1.tar.gz.sigstore.json  # optional
```

The `attestation` mapping has the following fields:

| Field        | Type            | Required | Description                                                                 |
| ------------ | --------------- | -------- | --------------------------------------------------------------------------- |
| `publishers` | list of strings | yes      | Publisher identities that the attestation's signing certificate must match. |
| `bundle_url` | string (URL)    | no       | Explicit URL of the Sigstore bundle. See **Bundle Discovery** below.        |

The `attestation` field MUST NOT appear on `git:` or `path:` sources in
this CEP. (Future CEPs MAY extend it to other source types.)

A recipe MAY omit the `attestation` field; absence means the builder
SHALL NOT perform any source attestation verification for that source.

### Publisher Identity Grammar

A publisher identity is a string of the form:

```text
<provider>:<owner>/<repo>[@<ref>]
```

| Component  | Meaning                                                                                |
| ---------- | -------------------------------------------------------------------------------------- |
| `provider` | The identity provider. This CEP defines `github` and `gitlab`. Others MAY be added.    |
| `owner`    | The owner / organization on that provider. MUST NOT be empty.                          |
| `repo`     | The repository on that provider. MUST NOT be empty.                                    |
| `ref`      | Optional ref constraint (e.g. `refs/tags/v1.0`). Reserved; see **Future Work** below.  |

For the providers defined here, the publisher identity maps to the
Sigstore certificate's Subject Alternative Name (SAN) and OIDC issuer
as follows:

| Provider | Identity prefix                          | OIDC issuer                                          |
| -------- | ---------------------------------------- | ---------------------------------------------------- |
| `github` | `https://github.com/<owner>/<repo>`      | `https://token.actions.githubusercontent.com`        |
| `gitlab` | `https://gitlab.com/<owner>/<repo>`      | `https://gitlab.com`                                 |

Builders that encounter an unknown `provider` MUST fail with an error
rather than silently skipping verification.

### Bundle Discovery

The bundle URL is determined as follows, in order:

1. If `bundle_url` is set in the recipe, the builder MUST use that URL.
2. Otherwise, if the source URL host is `pypi.io` or
   `files.pythonhosted.org`, the builder MUST construct a PyPI
   Integrity API URL of the form:

   ```text
   https://pypi.org/integrity/<project>/<version>/<filename>/provenance
   ```

   where `<project>` is the [PEP 503][PEP 503]-normalized project name
   (lowercase, `[-_.]` collapsed to `-`) and `<version>` and `<filename>`
   are extracted from the source URL's filename.
3. Otherwise, the builder MUST fail with an error reporting that no
   `bundle_url` is set and one cannot be auto-derived.

This list MAY be extended by future CEPs (e.g. to auto-derive bundle
URLs for GitHub releases). Builders MAY recognize additional auto-derived
hosts, but the recipe author SHOULD provide an explicit `bundle_url` for
portability between builders that do not.

### Response Formats

A builder MUST accept at least the following two response formats from
the bundle URL:

1. A [Sigstore Bundle][Sigstore Bundle] in JSON form, identified by the
   presence of a `mediaType` field.
2. A [PEP 740][PEP 740] provenance response with an `attestation_bundles`
   array, each containing `attestations` that the builder converts to
   Sigstore bundles.

For PEP 740 responses the builder MUST verify that any in-toto subject
present in each converted bundle matches the artifact (see below), and
SHOULD skip transparency-log verification since PEP 740 does not preserve
canonicalized Rekor entries. Other verification steps proceed normally.

### Minimum Verification

When the `attestation` field is present, the builder MUST, before using
the downloaded source:

1. **Download** the source archive and verify its `sha256` (or other
   declared hash) as it would for any URL source.
2. **Fetch** the attestation bundle from the URL determined in
   **Bundle Discovery**.
3. **Verify** each bundle's Sigstore signature against the current
   Sigstore trust root. The trust root SHOULD be fetched via [TUF] from
   the Sigstore public-good instance; cached trust material MAY be used
   subject to the freshness rules of the Sigstore specification.
4. **Verify** that the in-toto statement's `subject[].digest.sha256`
   contains the SHA-256 of the downloaded archive. If no subject matches,
   the build MUST fail.
5. **Verify** that for *each* publisher listed in `publishers`, at least
   one bundle in the response has a certificate whose SAN matches that
   publisher's identity prefix using **repository-boundary prefix
   matching** (see below), and whose OIDC issuer matches the provider's
   issuer. If any listed publisher cannot be matched, the build MUST fail.

If any of the above checks fail, the builder MUST abort the build and
MUST NOT use the downloaded source for further build steps.

#### Repository-boundary prefix matching

Sigstore certificates for CI providers typically encode the full workflow
path as the SAN (for example
`https://github.com/pallets/flask/.github/workflows/release.yml@refs/tags/3.1.1`).
Matching by raw string prefix is unsafe: `https://github.com/pallets/flask`
would match `https://github.com/pallets/flask-cors` as well.

A publisher's identity prefix `P` matches a certificate SAN `S` if and
only if:

- `S == P`, or
- `S` starts with `P` *and* the character immediately following `P` in
  `S` is `/` or `@`.

This rule MUST be applied by all conformant builders.

### Predicate Semantics Are Out of Scope

This CEP does not define, restrict, or interpret the predicate types
that appear in the in-toto statement. In particular:

- A PyPI provenance response carries [PEP 740][PEP 740] predicates whose
  semantics are owned by PyPI.
- A GitHub-attested release archive may carry any predicate the
  attester chose (commonly the SLSA build provenance predicate).
- Conda-specific publish attestations are defined by [CEP 27] and apply
  to *built conda packages*, not source archives.

A builder MAY apply additional predicate-specific checks beyond the
minimum above; such checks are out of scope here.

## Examples

### PyPI source with auto-derived bundle URL

```yaml
source:
  url: https://files.pythonhosted.org/packages/ab/cd/flask-3.1.1.tar.gz
  sha256: "6489f1..."
  attestation:
    publishers:
      - github:pallets/flask
```

The builder derives
`https://pypi.org/integrity/flask/3.1.1/flask-3.1.1.tar.gz/provenance`,
fetches the PEP 740 response, and verifies that one of the embedded
attestations was signed by a workflow under `github.com/pallets/flask`.

### GitHub release with explicit bundle

```yaml
source:
  url: https://github.com/facebook/zstd/releases/download/v1.5.7/zstd-1.5.7.tar.gz
  sha256: "eb33e5..."
  attestation:
    bundle_url: https://github.com/facebook/zstd/releases/download/v1.5.7/zstd-1.5.7.tar.gz.sigstore.json
    publishers:
      - github:facebook/zstd
```

### Multiple required publishers

```yaml
source:
  url: https://example.com/widget-2.0.tar.gz
  sha256: "abc123..."
  attestation:
    bundle_url: https://example.com/widget-2.0.tar.gz.sigstore.json
    publishers:
      - github:widget-org/widget
      - github:widget-org/release-bot
```

Every listed publisher must be matched by some bundle in the response.

## Future Work

- **Ref constraints.** The `@<ref>` suffix in the publisher grammar is
  reserved but not yet required to be enforced. A follow-up CEP may
  define how `refs/tags/v1.0`, `refs/heads/main`, etc. are matched
  against the certificate SAN.
- **Additional auto-derivation hosts.** GitHub Releases, GitLab Releases,
  and crates.io publish bundles at predictable locations; a follow-up
  may standardize their derivation.
- **Predicate-specific assertions.** Recipes may eventually want to
  assert facts encoded in the predicate (e.g. SLSA build level,
  reproducibility flags). That is deliberately not in this CEP.
- **`git:` and `path:` sources.** Out of scope here; both have weaker
  upstream conventions for attestation distribution today.

## References

- [CEP 14 - Recipe format v1][CEP 14]
- [CEP 27 - Publish attestation for conda packages][CEP 27]
- [Sigstore][Sigstore]
- [Sigstore Bundle Specification][Sigstore Bundle]
- [in-toto Attestation Framework][in-toto]
- [PEP 740 - Index support for digital attestations][PEP 740]
- [PyPI Integrity API][PyPI Integrity]
- [`actions/attest`][actions-attest]

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

[RFC2119]: https://www.ietf.org/rfc/rfc2119.txt
[Sigstore]: https://sigstore.dev
[Sigstore Bundle]: https://github.com/sigstore/protobuf-specs/blob/main/protos/sigstore_bundle.proto
[in-toto]: https://in-toto.io
[CEP 14]: ./cep-0014.md
[CEP 27]: ./cep-0027.md
[PEP 740]: https://peps.python.org/pep-0740/
[PEP 503]: https://peps.python.org/pep-0503/
[PyPI Integrity]: https://docs.pypi.org/api/integrity/
[actions-attest]: https://github.com/actions/attest
[TUF]: https://theupdateframework.io/
