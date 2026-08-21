# CEP XXXX - Source Attestation Verification in Recipes

<table>
<tr><td> Title </td><td> Source Attestation Verification in Recipes </td></tr>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Wolf Vollprecht &lt;wolf@prefix.dev&gt;</td></tr>
<tr><td> Created </td><td> May 20, 2026</td></tr>
<tr><td> Updated </td><td> Jul 6, 2026</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/168 </td></tr>
<tr><td> Implementation </td><td> https://github.com/prefix-dev/rattler-build (experimental) </td></tr>
</table>

> The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT",
  "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as
  described in [RFC2119][RFC2119] when, and only when, they appear in all capitals, as shown here.

## Abstract

This CEP extends the conda recipe format ([CEP 14]) with an optional
`attestation` field on URL sources. The field lets recipe authors declare
that an upstream source archive carries a [Sigstore] attestation, and
specifies a minimum set of checks that any conformant builder MUST perform
before using the archive. It further specifies how the verified bundles
are embedded in the built package, so the package itself stays tied to
its upstream producer. The CEP standardizes the recipe schema and this
embedding only: the attestation formats and predicate semantics
themselves remain owned by their upstream issuers (e.g.
[PyPI][PyPI Integrity], GitHub Releases).

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
3. Defining how verified bundles are embedded in the built package, so
   the provenance link survives into the distributed artifact and can be
   re-verified offline.
4. Explicitly **not** redefining upstream predicate formats. PyPI's
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
    predicate_type: https://docs.pypi.org/attestations/publish/v1     # optional
```

The `attestation` mapping has the following fields:

| Field            | Type                          | Required | Description                                                                                   |
| ---------------- | ----------------------------- | -------- | --------------------------------------------------------------------------------------------- |
| `publishers`     | list of publisher identities  | yes      | Publisher identities that the attestations' signing certificates must match. See below.       |
| `bundle_url`     | string or list of strings     | no       | Explicit URL(s) of Sigstore bundles or provenance responses. See **Bundle Discovery** below.  |
| `predicate_type` | string (type URI)             | no       | Restricts which attestations count towards publisher matching. See **Minimum Verification**.  |

The `attestation` field MUST NOT appear on `git:` or `path:` sources in
this CEP. (Future CEPs MAY extend it to other source types.)

When `attestation` is present, the source MUST also declare a `sha256`
hash: the in-toto subject formats used in practice identify artifacts by
SHA-256, and a weaker hash such as `md5` next to an attestation would
undermine the binding.

A recipe MAY omit the `attestation` field; absence means the builder
SHALL NOT perform any source attestation verification for that source.
The field is an additive, backwards-compatible extension of the
[CEP 14] recipe schema and does not change the schema version.

### Publisher Identities

Sigstore binds a signature to the pair of an X.509 certificate *identity*
(the Subject Alternative Name, SAN) and the *OIDC issuer* that vouched
for it. A publisher identity in this CEP therefore always denotes such a
pair. This mirrors established verification interfaces such as `cosign
verify --certificate-identity/--certificate-oidc-issuer` and
`gh attestation verify`, which accept the same two values.

Each entry in `publishers` is either an **explicit mapping** or a
**shorthand string**.

#### Explicit mapping form

```yaml
publishers:
  - identity: https://github.com/pallets/flask
    issuer: https://token.actions.githubusercontent.com
```

| Field      | Required | Description                                                        |
| ---------- | -------- | ------------------------------------------------------------------ |
| `identity` | yes      | The certificate SAN to match. Matching rules are described below.  |
| `issuer`   | yes      | The OIDC issuer URL of the certificate.                            |

An `identity` value that is a URL (starts with `https://`) is matched
against URI SANs using **repository-boundary prefix matching** (see
below); this comparison is case-insensitive, since the providers defined
here treat owner and repository names as case-insensitive while the SAN
carries whatever casing the provider canonicalized. Any other `identity`
value is matched for exact, case-sensitive string equality against the
certificate's SAN (e.g. an email SAN). The `issuer` is always compared
for exact, case-sensitive string equality with the certificate's issuer
extension.

The mapping form can express identities that are not `owner/repo` URLs —
for example artifacts signed via Google Cloud infrastructure carry email
SANs such as `123456789-compute@developer.gserviceaccount.com` with the
issuer `https://accounts.google.com` — as well as self-hosted CI
instances (e.g. a GitHub Enterprise Server or self-managed GitLab
deployment) whose issuer differs from the hosted defaults.

#### Shorthand string form

A shorthand publisher identity is a string of the form:

```text
<provider>:<owner>/<repo>[@<ref>]
```

| Component  | Meaning                                                                                |
| ---------- | -------------------------------------------------------------------------------------- |
| `provider` | The identity provider. This CEP defines `github` and `gitlab`. Others MAY be added.    |
| `owner`    | The owner / organization on that provider. MUST NOT be empty.                          |
| `repo`     | The repository on that provider. MUST NOT be empty.                                    |
| `ref`      | Optional ref constraint (e.g. `refs/tags/v1.0`). Reserved; see **Future Work** below.  |

A shorthand is parsed by splitting at the first `:` (provider), the
first subsequent `/` (owner), and the first `@` (ref), if any. The
`<repo>` component MAY therefore itself contain `/` separators to
address nested namespaces — e.g. GitLab subgroups:
`gitlab:group/subgroup/project` expands to the identity
`https://gitlab.com/group/subgroup/project`.

The `ref` semantics are not defined by this CEP. Builders that do not
implement ref matching MUST fail with an error when a `ref` is present,
rather than silently ignoring the constraint.

Each shorthand is exactly equivalent to an explicit mapping:

| Provider | Expands to `identity`                    | Expands to `issuer`                                  |
| -------- | ---------------------------------------- | ---------------------------------------------------- |
| `github` | `https://github.com/<owner>/<repo>`      | `https://token.actions.githubusercontent.com`        |
| `gitlab` | `https://gitlab.com/<owner>/<repo>`      | `https://gitlab.com`                                 |

The providers named here refer to the hosted `github.com` and
`gitlab.com` services only. Self-hosted instances of these products use
different issuer URLs and MUST be expressed with the explicit mapping
form instead.

Builders that encounter an unknown `provider` MUST fail with an error
rather than silently skipping verification.

> **Why not PURLs?** [Package-URLs][PURL] identify *package artifacts*
> within an ecosystem, not *signing identities*: they cannot carry the
> OIDC issuer, and non-repository identities (such as email SANs) have
> no PURL form. The `(identity, issuer)` pair is the native vocabulary
> of Sigstore certificate verification, so this CEP uses it directly.

#### Repository-boundary prefix matching

Sigstore certificates for CI providers typically encode the full workflow
path as the SAN (for example
`https://github.com/pallets/flask/.github/workflows/release.yml@refs/tags/3.1.1`).
Matching by raw string prefix is unsafe: `https://github.com/pallets/flask`
would match `https://github.com/pallets/flask-cors` as well.

A publisher's URL identity `P` matches a certificate SAN `S` if and
only if:

- `S == P`, or
- `S` starts with `P` *and* the character immediately following `P` in
  `S` is `/` or `@`.

This rule MUST be applied by all conformant builders.

### Bundle Discovery

[CEP 14] allows `url:` to be a list of equivalent mirror URLs; the
*download URL* below refers to the entry from which the builder
actually retrieved the archive.

The bundle URLs are determined as follows, in order:

1. If `bundle_url` is set in the recipe, the builder MUST fetch every
   listed URL (a plain string is equivalent to a single-element list).
2. Otherwise, if the download URL's host is `pypi.org`, `pypi.io`, or
   `files.pythonhosted.org`, the builder MUST construct a PyPI
   Integrity API URL of the form:

   ```text
   https://pypi.org/integrity/<project>/<version>/<filename>/provenance
   ```

   where `<filename>` is the last path segment of the download URL, and
   `<project>` and `<version>` are derived from it: after stripping the
   file extension, an sdist stem is split at its last `-` (sdist
   filenames follow [PEP 625][PEP 625]), while for a wheel the first
   two `-`-separated fields of the stem are the project and version
   (per the [binary distribution format][Wheel Format]). The project
   part is then [PEP 503][PEP 503]-normalized (lowercase, runs of
   `[-_.]` collapsed to `-`). `pypi.io` is a legacy alias of `pypi.org`
   that remains widespread in conda recipes.

   Legacy sdist filenames that predate PEP 625 can parse ambiguously;
   if the derived URL is wrong, the Integrity API fetch fails (and with
   it the build), and the recipe author SHOULD set an explicit
   `bundle_url` instead.
3. Otherwise, the builder MUST fail with an error reporting that no
   `bundle_url` is set and one cannot be auto-derived.

This list is closed for this CEP: builders MUST NOT auto-derive bundle
URLs for other hosts, so that a recipe verifies identically on every
conformant builder. Future CEPs MAY extend the auto-derivation list
(e.g. for GitHub or GitLab releases); until then, recipe authors MUST
provide an explicit `bundle_url` for non-PyPI hosts.

Allowing `bundle_url` to be a list accommodates sources that publish
attestations in more than one place (for example PyPI provenance *and* a
GitHub release bundle); the bundles from all responses are pooled for
verification.

### Response Formats

A builder MUST accept at least the following two response formats from
each bundle URL:

1. A [Sigstore Bundle][Sigstore Bundle] in JSON form, identified by the
   presence of a `mediaType` field.
2. A [PEP 740][PEP 740] provenance response with an `attestation_bundles`
   array, each containing `attestations` that the builder converts to
   Sigstore bundles.

The bundles obtained from all fetched URLs together form the *bundle
set* used in **Minimum Verification** below.

For bundles converted from PEP 740 responses the builder SHOULD skip
transparency-log verification, since PEP 740 does not preserve
canonicalized Rekor entries; all other verification steps proceed
normally.

### Minimum Verification

When the `attestation` field is present, the builder MUST, before using
the downloaded source:

1. **Download** the source archive and verify its `sha256` as it would
   for any URL source.
2. **Fetch** the attestation bundle set from the URLs determined in
   **Bundle Discovery**. If any fetch fails — including a response
   indicating that no attestations are available — the build MUST fail.
3. **Verify** each bundle cryptographically as defined by the
   [Sigstore Client Specification][Sigstore Client Spec]: certificate
   chain validation against the trust root, transparency-log inclusion
   (subject to the PEP 740 exception in **Response Formats**), and
   timestamp verification. The trust root SHOULD be fetched via [TUF]
   from the Sigstore public-good instance; cached trust material MAY be
   used subject to the freshness rules of the Sigstore specification.
   A bundle that fails cryptographic verification indicates tampering:
   the build MUST fail.
4. **Filter** the bundle set to those bundles whose in-toto statement
   lists a `subject[].digest.sha256` equal to the SHA-256 of the
   downloaded archive. Bundles attesting other artifacts — which can
   legitimately occur in pooled responses — are excluded without error.
   If the filtered set is empty, the build MUST fail.
5. **Filter** the bundle set further, if `predicate_type` is set in the
   recipe, to those bundles whose in-toto statement has exactly that
   `predicateType`. If the filtered set is empty, the build MUST fail.
6. **Verify** that for *each* publisher listed in `publishers`, at least
   one bundle in the filtered bundle set has a certificate whose SAN
   matches that publisher's `identity` (see **Publisher Identities**),
   and whose OIDC issuer matches the publisher's `issuer`. If any
   listed publisher cannot be matched, the build MUST fail.

If any of the above checks fail, the builder MUST abort the build and
MUST NOT use the downloaded source for further build steps.

### Predicate Semantics Are Out of Scope

This CEP does not define, restrict, or interpret the predicate types
that appear in the in-toto statement. In particular:

- A PyPI provenance response carries [PEP 740][PEP 740] predicates whose
  semantics are owned by PyPI.
- A GitHub-attested release archive may carry any predicate the
  attester chose (commonly the SLSA build provenance predicate).
- Conda-specific publish attestations are defined by [CEP 27] and apply
  to *built conda packages*, not source archives.

The optional `predicate_type` field does not change this: it pins the
predicate *type string* without interpreting the predicate body, so that
a signature with different semantics from the same identity (e.g. a test
attestation instead of a publish attestation) does not satisfy the
recipe's intent. Recipe authors SHOULD set it when the upstream predicate
type is known and stable.

A builder MAY apply additional predicate-specific checks beyond the
minimum above; such checks are out of scope here.

### Embedding verified bundles in the built package

Builders that embed the rendered recipe in the built package (e.g.
under `info/recipe/`, as rattler-build does with
`info/recipe/rendered_recipe.yaml`) SHOULD also embed the attestation
bundles they verified. The built package then carries the evidence that
ties it back to its upstream source and producer: auditors and
rebuilders can re-run the checks against the package alone, without
re-fetching the bundle URLs — which may have moved or disappeared by
then. Combined with a [CEP 27] publish attestation covering the built
package itself, this yields a machine-checkable chain from the package
through the recipe to the upstream source publisher.

A builder that embeds bundles MUST use the following layout. Every
bundle that survived the filtering steps of **Minimum Verification** is
written, as a [Sigstore Bundle][Sigstore Bundle] in JSON form, to:

```text
info/recipe/attestations/<filename>.<n>.sigstore.json
```

where `<filename>` is the source archive's filename and `<n>` is the
zero-based index of the bundle within that source's filtered bundle
set. Bundles obtained from PEP 740 responses are stored in their
*converted* Sigstore Bundle form. Bundles that were excluded during
filtering MUST NOT be stored. Builders SHOULD serialize each stored
bundle deterministically — byte-for-byte as fetched where possible,
otherwise with stable key ordering — so that repeated builds produce
identical packages.

In the rendered recipe, the source's `attestation` mapping is augmented
with a `verified` list containing one entry per stored bundle:

```yaml
source:
  url: https://files.pythonhosted.org/packages/ab/cd/flask-3.1.1.tar.gz
  sha256: "6489f1..."
  attestation:
    publishers:
      - github:pallets/flask
    verified:
      - path: attestations/flask-3.1.1.tar.gz.0.sigstore.json
        sha256: "9f31ab..."
        predicate_type: https://docs.pypi.org/attestations/publish/v1
        san: https://github.com/pallets/flask/.github/workflows/publish.yml@refs/tags/3.1.1
        issuer: https://token.actions.githubusercontent.com
```

| Field            | Description                                                        |
| ---------------- | ------------------------------------------------------------------ |
| `path`           | Bundle file path, relative to the rendered recipe's directory.     |
| `sha256`         | SHA-256 of the stored bundle file.                                 |
| `predicate_type` | The `predicateType` of the bundle's in-toto statement.             |
| `san`            | The certificate SAN, copied verbatim.                              |
| `issuer`         | The certificate's OIDC issuer, copied verbatim.                    |

The `verified` entries deliberately record no wall-clock timestamp:
embedding one would make otherwise identical builds non-reproducible,
and the transparency-log entries inside the stored bundles already
carry signed time evidence.

A consumer of the built package MAY re-run steps 3–6 of **Minimum
Verification** against the stored bundles (using its own trust root) to
independently confirm the publisher claims recorded in the rendered
recipe. The `verified` metadata is a convenience index; the stored
bundles remain the source of truth.

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

### Explicit identity mapping (email SAN, pinned predicate type)

```yaml
source:
  url: https://files.pythonhosted.org/packages/ab/cd/widget-2.0.tar.gz
  sha256: "abc123..."
  attestation:
    predicate_type: https://docs.pypi.org/attestations/publish/v1
    publishers:
      - identity: 123456789-compute@developer.gserviceaccount.com
        issuer: https://accounts.google.com
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

Every listed publisher must be matched by some bundle in the bundle set.

## Security Considerations

### What attestation verification adds — and what it does not

A pinned `sha256` already guarantees that every build uses exactly the
bytes the recipe author selected; an attacker who replaces the upstream
archive *after* the recipe is written is caught by the hash check alone.
The `attestation` block instead protects the *selection* of those bytes,
and their auditability afterwards:

- At authoring or update time, verification proves that the archive was
  produced by the expected publisher — catching compromised uploads and
  typosquatted or mirrored artifacts *before* their hash is pinned. This
  matters most for automated version bumps, where no human inspects the
  new tarball.
- After the fact, the recipe records a machine-checkable claim about the
  source's origin that auditors and rebuilders can re-verify.

### The recipe itself is not signed

This CEP does not protect against modification of the recipe: an
attacker who can edit the recipe can remove the `attestation` block (or
change `publishers`) along with the hash. Defenses against recipe
tampering — signed recipes or feedstocks, channel policies that
*require* attestation blocks for certain sources, or lockfile-level
pinning of verified provenance — are complementary and out of scope
here.

### Bundle transport

Bundle URLs SHOULD use `https`. The security of verification does not
depend on the transport, however: bundles are signed, so an attacker who
controls the bundle host or the connection can at worst cause a build
failure (denial of service), not a false verification success.

### Network dependence

Verification requires fetching bundles and (via [TUF]) trust-root
updates at build time. Builders MAY cache bundles and trust material
alongside cached sources for offline or air-gapped operation, subject to
the trust root freshness rules. Once a package is built, the embedded
bundles (see **Embedding verified bundles in the built package**) allow
re-verification without any upstream availability; *rebuilding* from the
recipe, however, still depends on the bundle URLs remaining reachable —
see **Future Work**.

## Future Work

- **Ref constraints.** The `@<ref>` suffix in the shorthand grammar is
  reserved but its matching semantics are not yet defined (builders MUST
  reject it for now, see **Publisher Identities**). A follow-up CEP may
  define how `refs/tags/v1.0`, `refs/heads/main`, etc. are matched
  against the certificate SAN.
- **Additional auto-derivation hosts.** GitHub Releases, GitLab Releases,
  and crates.io publish bundles at predictable locations; a follow-up
  may standardize their derivation.
- **Additional shorthand providers.** Follow-up CEPs may register more
  shorthand providers (and their issuer URLs) as ecosystems adopt
  Sigstore signing.
- **Predicate-specific assertions.** Recipes may eventually want to
  assert facts encoded in the predicate (e.g. SLSA build level,
  reproducibility flags). That is deliberately not in this CEP.
- **Bundle vendoring at build time.** Built packages embed their
  verified bundles, but *rebuilding* an old recipe still requires its
  bundle URLs (e.g. the PyPI Integrity API) to remain available. A
  follow-up may standardize vendoring bundles next to the source recipe
  or in channel metadata so that builds themselves remain possible
  offline and long after upstream endpoints change.
- **`git:` and `path:` sources.** Out of scope here; both have weaker
  upstream conventions for attestation distribution today.

## References

- [CEP 14 - Recipe format v1][CEP 14]
- [CEP 27 - Publish attestation for conda packages][CEP 27]
- [Sigstore][Sigstore]
- [Sigstore Bundle Specification][Sigstore Bundle]
- [Sigstore Client Specification][Sigstore Client Spec]
- [in-toto Attestation Framework][in-toto]
- [PEP 740 - Index support for digital attestations][PEP 740]
- [PEP 625 - Filename of a source distribution][PEP 625]
- [Binary distribution format (wheels)][Wheel Format]
- [PyPI Integrity API][PyPI Integrity]
- [Package-URL specification][PURL]
- [`actions/attest`][actions-attest]

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

[RFC2119]: https://www.ietf.org/rfc/rfc2119.txt
[Sigstore]: https://sigstore.dev
[Sigstore Bundle]: https://github.com/sigstore/protobuf-specs/blob/main/protos/sigstore_bundle.proto
[Sigstore Client Spec]: https://github.com/sigstore/architecture-docs/blob/main/client-spec.md
[PEP 625]: https://peps.python.org/pep-0625/
[Wheel Format]: https://packaging.python.org/en/latest/specifications/binary-distribution-format/
[in-toto]: https://in-toto.io
[CEP 14]: ./cep-0014.md
[CEP 27]: ./cep-0027.md
[PEP 740]: https://peps.python.org/pep-0740/
[PEP 503]: https://peps.python.org/pep-0503/
[PyPI Integrity]: https://docs.pypi.org/api/integrity/
[PURL]: https://github.com/package-url/purl-spec
[actions-attest]: https://github.com/actions/attest
[TUF]: https://theupdateframework.io/
