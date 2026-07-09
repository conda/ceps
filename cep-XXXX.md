# CEP XXXX - Computing the hash of the contents in a directory (v2)

<table>
<tr><td> Title </td><td> Computing the hash of the contents in a directory (v2) </td></tr>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> pb01ka &lt;gaganpb08singh@gmail.com&gt;, hunger &lt;tobias.hunger@slint.dev&gt; </td></tr>
<tr><td> Created </td><td> Jun 4, 2026</td></tr>
<tr><td> Updated </td><td> Jun 5, 2026</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/issues/150, https://github.com/conda/ceps/pull/174 </td></tr>
<tr><td> Implementation </td><td> https://github.com/conda/conda-build/pull/5992 </td></tr>
<tr><td> Supersedes </td><td> <a href="cep-0019.md">CEP 19</a> </td></tr>
</table>

> The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT",
  "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as
  described in [RFC2119][RFC2119] when, and only when, they appear in all capitals, as shown here.

## Abstract

This CEP supersedes [CEP 19](cep-0019.md) and amends the algorithm for computing the aggregated
hash of a directory's contents in a cross-platform way. The original algorithm was susceptible to
hash collisions when filenames contained the same byte sequences used as type markers or field
separators. This CEP fixes that vulnerability by length-prefixing every variable-length field in the
hash stream, making all field boundaries unambiguous.

## Motivation

The CEP 19 algorithm builds the hash stream for each directory entry by concatenating raw bytes in
the order:

```text
<path_bytes> <type_marker> <content_bytes> <separator "-">
```

Because there is no field-length information, two structurally different directory trees can produce
an identical byte stream whenever a filename happens to contain the same bytes used as type markers
(`F`, `D`, `L`) or the entry separator (`-`).

**Concrete example:**

- **Tree 1:** a single file named `testFhello-world` with content `www`
- **Tree 2:** a file named `test` (content `hello`) and a file named `world` (content `www`)

Both trees produce the byte stream `testFhello-worldFwww-`, yielding the same digest: a true hash
collision on structurally different directory trees.

An attacker who controls filenames could exploit this to produce a directory tree whose computed
hash matches that of a different, potentially malicious tree.

## Specification

Given a directory (the "scanned directory"), recursively scan all its contents (without following
symlinks) and sort them by their path relative to the scanned directory. The scanned directory
itself (`.`) MUST NOT be included as an entry. Paths MUST be NFC-normalized and then UTF-8-encoded
before sorting; the sort MUST be a byte-wise comparison of the resulting UTF-8 bytes, ordering by
unsigned byte value (0-255).

The paths MUST be normalized before they are processed by the algorithm below. The following rules
apply to both entry paths and symlink targets:

- Before encoding a path to UTF-8 for sorting or hashing, implementations MUST normalize it to NFC.
- If NFC normalization produces two entries with the same path, implementations MUST error out
  rather than silently feeding duplicate bytes into the hasher.
- Backslashes in the path MUST be normalized to forward slashes (e.g. `path\\to\\file`
  becomes `path/to/file`).
- Redundant path components MUST be removed (e.g. `path/to/../to/file` becomes `path/to/file`).
- A leading `./` MUST be stripped (e.g. `./README.txt` becomes `README.txt`).
- If any path component contains a null byte (`\0`), implementations MUST error out.
- Every path MUST be UTF-8-encodable. If a path contains bytes that are not valid UTF-8,
  implementations MUST error out rather than silently substituting or passing through the invalid
  bytes (see [Rationale](#why-require-utf-8-encodable-paths) for a Python-specific pitfall this
  guards against).

**Entry paths** (the paths of directory entries) are additionally subject to:

- Entry paths MUST be relative; a leading `/` MUST be rejected (implementations MUST error out if an
  entry path is absolute).
- Entry paths MUST NOT contain a drive letter (e.g. `C:`) or a UNC prefix (e.g. `//server/share`);
  implementations MUST error out if such a path is encountered.

**Symlink targets** are subject to different rules, since a symlink MAY legitimately point to an
absolute path:

- Symlink targets MAY be relative or absolute. A leading `/` is a legitimate absolute Unix path and
  MUST be preserved, not rejected.
- Windows drive letters (e.g. `C:`) and UNC prefixes (e.g. `//server/share`) in a symlink target
  MUST cause the implementation to error out, because there is no meaningful cross-platform way to
  normalize them into the hash stream.

For each entry in the sorted contents, feed the following bytes into the hasher in order:

1. The byte length of the UTF-8-encoded normalized relative path, written in decimal and that decimal
   string encoded as UTF-8, followed by the UTF-8 encoded byte of `:`.
2. The UTF-8 encoded bytes of the normalized relative path.
3. Then, depending on the entry type:
   - For a **regular file**:
     - The UTF-8 encoded byte of `F`.
     - The content bytes are determined as follows:
       - If the file is a text file (i.e. its entire contents can be UTF-8 decoded): the file's raw
         bytes with every `\r\n` byte sequence (`0x0D 0x0A`) replaced by `\n` (`0x0A`). The
         substitution MUST be performed directly on the raw bytes, not via a decode-to-text-then-
         re-encode round-trip. This is the default, normative mode; see
         [Rationale](#why-keep-the-textbinary-distinction-and-line-ending-normalization) for an
         optional alternative mode.
       - If the file is binary: its raw bytes, unmodified.
       - If the file can't be opened or read, implementations MUST error out.
     - The byte length of those content bytes, written in decimal and encoded as UTF-8, followed by
       the UTF-8 encoded byte of `:`, MUST be fed into the hasher immediately before the content
       bytes themselves. Content is length-prefixed for the same reason entry paths and symlink
       targets are: without it, content containing `-` followed by bytes that look like a valid
       subsequent entry can reproduce the byte stream of a different, structurally distinct tree
       (see [Rationale](#why-length-prefix-file-content-too) for a worked collision).
   - For a **directory**: the UTF-8 encoded byte of `D`, and nothing else.
   - For a **symlink**:
     - The UTF-8 encoded byte of `L`.
     - The byte length of the UTF-8-encoded symlink target path, written in decimal and that decimal
       string encoded as UTF-8, followed by the UTF-8 encoded byte of `:`.
     - The UTF-8 encoded bytes of the symlink target path, normalized per the common rules and the
       **Symlink targets** rules above (the **Entry paths** rules do not apply to symlink targets).
   - For **any other type**, implementations MUST error out.
4. The UTF-8 encoded byte of `-`.

### Summary of changes from CEP 19

| Field | CEP 19 | This CEP |
| --- | --- | --- |
| Path | `<path_bytes>` | `<len(path_bytes)>:<path_bytes>` |
| Symlink target | `<target_bytes>` | `<len(target_bytes)>:<target_bytes>` |
| File content | `<content_bytes>` | `<len(content_bytes)>:<content_bytes>` |
| Sorting | Raw Unicode code point comparison | NFC-normalized, UTF-8-encoded byte comparison |
| Error handling | Unreadable files, unknown entry types | Additionally: null bytes, invalid/absolute entry paths, drive letters/UNC prefixes, non-UTF-8 paths, NFC-induced path collisions |

Text vs. binary detection and line-ending normalization work the same way as in CEP 19: given the
same file, they produce the same content bytes in both algorithms. Only the reference
implementation's internal mechanics were clarified (see
[Rationale](#why-keep-the-textbinary-distinction-and-line-ending-normalization)) - this does not
mean the overall per-entry byte stream is unchanged, since it still includes the new length prefixes
shown in the table above.

### Reference implementation

For Python 3.6+:

```python
import hashlib
import posixpath
import re
import unicodedata
from pathlib import Path

_DRIVE_LETTER_RE = re.compile(r"^[A-Za-z]:")


def _normalize_path(raw: str) -> str:
    # Applies the common rules: reject null bytes, normalize separators, collapse
    # redundant components (including a leading "./"), then NFC-normalize.
    if "\0" in raw:
        raise ValueError(f"path contains a null byte: {raw!r}")
    raw = raw.replace("\\", "/")
    collapsed = posixpath.normpath(raw)
    if collapsed == ".":
        collapsed = ""
    return unicodedata.normalize("NFC", collapsed)


def _encode_path(path: str) -> bytes:
    # `path` may contain surrogate-escaped code points (PEP 383) if the on-disk name isn't
    # valid UTF-8. Encoding with the default "strict" handler (not "surrogateescape") raises
    # UnicodeEncodeError in that case, which is the required behavior: error out rather than
    # silently letting non-UTF-8 bytes into the hash stream.
    return path.encode("utf-8")


def _check_entry_path(path: str) -> None:
    if path.startswith("/"):
        raise ValueError(f"entry path must be relative: {path!r}")
    if _DRIVE_LETTER_RE.match(path):
        raise ValueError(f"entry path must not contain a drive letter: {path!r}")


def _check_symlink_target(target: str) -> None:
    if target.startswith("//"):
        raise ValueError(f"symlink target must not contain a UNC prefix: {target!r}")
    if _DRIVE_LETTER_RE.match(target):
        raise ValueError(f"symlink target must not contain a drive letter: {target!r}")


def contents_hash(directory: str, algorithm: str) -> str:
    directory = Path(directory)
    entries = []
    seen_paths = set()
    for path in directory.rglob("*"):
        rel = _normalize_path(path.relative_to(directory).as_posix())
        _check_entry_path(rel)
        if rel in seen_paths:
            raise ValueError(f"NFC normalization collision on path: {rel!r}")
        seen_paths.add(rel)
        entries.append((_encode_path(rel), path))

    hasher = hashlib.new(algorithm)
    for rel_bytes, path in sorted(entries, key=lambda entry: entry[0]):
        hasher.update(f"{len(rel_bytes)}:".encode("utf-8"))
        hasher.update(rel_bytes)
        if path.is_symlink():
            target = _normalize_path(str(path.readlink()))
            _check_symlink_target(target)
            target_bytes = _encode_path(target)
            hasher.update(b"L")
            hasher.update(f"{len(target_bytes)}:".encode("utf-8"))
            hasher.update(target_bytes)
        elif path.is_dir():
            hasher.update(b"D")
        elif path.is_file():
            hasher.update(b"F")
            with open(path, "rb") as fh:
                data = fh.read()
            try:
                data.decode("utf-8")
            except UnicodeDecodeError:
                pass  # binary: hash the raw bytes unmodified
            else:
                data = data.replace(b"\r\n", b"\n")  # text: normalize line endings
            hasher.update(f"{len(data)}:".encode("utf-8"))
            hasher.update(data)
        else:
            raise RuntimeError(f"Unknown file type: {path}")
        hasher.update(b"-")
    return hasher.hexdigest()
```

This implementation attempts to cover every normalization and error-handling rule from the
[Specification](#specification) above (NFC normalization and collision detection, null bytes,
redundant components, absolute/drive-letter/UNC rejection, non-UTF-8 paths, unreadable files); it is
provided as a normative illustration, not a certified conformance suite, so a discrepancy against the
Specification text should be treated as a bug in this snippet rather than in the rule it's illustrating.

## Examples

### Example 1: Text file and subdirectory

Given the directory:

```text
mydir/
├── README.txt   (content: "Hello\n")
└── src/
```

Entries sorted by NFC-normalized UTF-8 byte comparison: `README.txt`, `src`.

**CEP 19 byte stream** (concatenated across both entries):

```text
README.txtFHello\n-srcD-
```

**This CEP byte stream:**

```text
10:README.txtF6:Hello\n-3:srcD-
```

The `10:` prefix encodes the 10-byte path `README.txt`; `6:` encodes the 6-byte content `Hello\n`;
`3:` encodes the 3-byte path `src`. The type markers (`F`, `D`) and the entry separator (`-`) are
unchanged and still unambiguous because both the path and content boundaries are now known exactly.

### Example 2: Directory containing a symlink

Given the directory:

```text
mydir/
└── link -> ../target
```

**CEP 19 byte stream:**

```text
linkL../target-
```

**This CEP byte stream:**

```text
4:linkL9:../target-
```

The first `4:` encodes the 4-byte path `link`. After the `L` type marker, `9:` encodes the 9-byte
symlink target `../target`.

### Example 3: Dotfile sort position

Given the directory:

```text
mydir/
├── .gitignore   (content: "*.pyc\n")
├── README.txt   (content: "Hello\n")
└── src/
```

Sorting compares the UTF-8 bytes of each path. The byte `.` (`0x2E`) is lower than any ASCII
letter, so `.gitignore` sorts before `README.txt` and `src`:

```text
.gitignore, README.txt, src
```

**This CEP byte stream:**

```text
10:.gitignoreF6:*.pyc\n-10:README.txtF6:Hello\n-3:srcD-
```

The `10:` prefix encodes the 10-byte path `.gitignore`, which is processed as an ordinary regular
file: the leading `.` has no special meaning to the algorithm. Its `6:` content prefix encodes the
6-byte content `*.pyc\n`.

### Example 4: NFC normalization before sorting

Unicode allows the same visible filename to be encoded as different code point sequences. For
example, `é` can be a single precomposed code point (`U+00E9`) or a decomposed sequence of `e`
(`U+0065`) followed by a combining acute accent (`U+0301`). Filesystems are not consistent about
which form they hand back to a directory scan (e.g. HFS+ on macOS tends to decompose), so the
algorithm normalizes every path to NFC first to get a reproducible result across platforms.

Given the directory:

```text
mydir/
├── café.txt   (name stored on disk as decomposed "e" + combining acute accent, content: "espresso\n")
└── cafe.txt   (content: "drip\n")
```

**Step 1 - NFC normalize each path:**

| On-disk path (code points) | NFC-normalized path (code points) |
| --- | --- |
| `c a f e U+0301 . t x t` (9 code points) | `c a f U+00E9 . t x t` (8 code points) |
| `c a f e . t x t` (8 code points) | `c a f e . t x t` (unchanged) |

**Step 2 - encode the normalized paths as UTF-8 bytes:**

| Normalized path | UTF-8 bytes (hex) | Byte length |
| --- | --- | --- |
| `café.txt` | `63 61 66 c3 a9 2e 74 78 74` | 9 |
| `cafe.txt` | `63 61 66 65 2e 74 78 74` | 8 |

**Step 3 - compare the byte sequences (unsigned byte value) and sort:**

The first three bytes (`63 61 66`) are equal in both paths. The fourth byte decides the order:
`cafe.txt` has `0x65` (`e`) and `café.txt` has `0xc3` (the first byte of `é`). Since `0x65 < 0xc3`,
`cafe.txt` sorts before `café.txt`:

```text
cafe.txt, café.txt
```

**This CEP byte stream:**

```text
8:cafe.txtF5:drip\n-9:café.txtF9:espresso\n-
```

Without the NFC normalization step, a directory tree using the decomposed form of `café.txt` would
hash differently from an otherwise identical tree using the precomposed form, even though both
represent the same filename and content. Normalizing to NFC before hashing removes that
platform-dependent discrepancy.

### Example 5: Collision (CEP 19 vulnerability)

This example reproduces the collision from the Motivation section at the byte-stream level.

**Tree 1:** one file named `testFhello-world` (16 UTF-8 bytes) with content `www`.

**Tree 2:** a file named `test` (content `hello`) and a file named `world` (content `www`).

| Algorithm     | Tree 1                       | Tree 2                          | Collision? |
| ------------- | ---------------------------- | ------------------------------- | ---------- |
| CEP 19        | `testFhello-worldFwww-`      | `testFhello-worldFwww-`         | Yes        |
| This proposal | `16:testFhello-worldF3:www-` | `4:testF5:hello-5:worldF3:www-` | No         |

Under CEP 19 both trees yield the identical stream `testFhello-worldFwww-` and therefore the same
digest. Under this proposal, the `16:` length prefix on Tree 1 unambiguously marks the path as 16
bytes, so the `F` that follows is the type marker - not part of the filename. Tree 2 produces a
completely different stream and a different digest.

The step-by-step breakdown for this CEP:

**Tree 1** - one file named `testFhello-world` (content `www`):

| Step | Field                | Bytes fed to hasher |
| ---- | -------------------- | ------------------- |
| 1    | path length + `:`    | `16:`               |
| 2    | path                 | `testFhello-world`  |
| 3    | type marker          | `F`                 |
| 4    | content length + `:` | `3:`                |
| 5    | file content         | `www`               |
| 6    | entry separator      | `-`                 |

Full stream: `16:testFhello-worldF3:www-`

**Tree 2** - file `test` (content `hello`) followed by file `world` (content `www`):

| Step | Field                         | Bytes fed to hasher |
| ---- | ----------------------------- | ------------------- |
| 1    | path length + `:` for `test`  | `4:`                |
| 2    | path                          | `test`              |
| 3    | type marker                   | `F`                 |
| 4    | content length + `:`          | `5:`                |
| 5    | file content                  | `hello`             |
| 6    | entry separator               | `-`                 |
| 7    | path length + `:` for `world` | `5:`                |
| 8    | path                          | `world`             |
| 9    | type marker                   | `F`                 |
| 10   | content length + `:`          | `3:`                |
| 11   | file content                  | `www`               |
| 12   | entry separator               | `-`                 |

Full stream: `4:testF5:hello-5:worldF3:www-`

The two streams are distinct, so the digests are distinct.

## Rationale

### Why length-prefix rather than escaping?

An alternative fix would be to escape occurrences of the separator bytes inside filenames. However,
escaping requires a second escape character, which must itself be escaped, creating additional
complexity and potential for bugs. Length-prefixing is simpler, well-established (it is the basis
of netstrings and many binary protocols), and adds a constant, predictable overhead of a few bytes
per field.

### Why length-prefix file content too?

Type markers (`F`, `D`, `L`) and the entry separator (`-`) are single fixed bytes that are always
present in a known position relative to the length-prefixed path, so they do not need their own
length prefix. File content is different: it is arbitrary bytes chosen by whoever created the file,
so it cannot be assumed to be safely bracketed by the `F` marker on one side and the `-` separator on
the other - content can itself contain a `-` followed by bytes that look like a valid subsequent
entry, reproducing a different tree's byte stream.

For example, a single file `README.txt` containing the literal bytes `Hello\n-3:srcD` and a
directory containing `README.txt` (content `Hello\n`) plus an empty subdirectory `src` would, without
a content length prefix, both produce the identical stream `10:README.txtFHello\n-3:srcD-`: a hash
collision between two structurally different trees, the same class of bug this CEP exists to fix for
paths. Prefixing the content with its byte length, exactly as done for paths and symlink targets,
closes this gap: the two trees instead produce `10:README.txtF13:Hello\n-3:srcD-` and
`10:README.txtF6:Hello\n-3:srcD-`, which are no longer equal.

### Why erroring out on unreadable files?

The rationale is unchanged from CEP 19: we can't verify the contents of such entries, and an
attacker could hide malicious content in those paths and later make them accessible
(e.g. by `chmod`ing them readable).

### Why keep the text/binary distinction and line-ending normalization?

This was considered for removal, since it adds complexity: implementations must attempt a UTF-8
decode of every file and rewrite `\r\n` to `\n` before hashing. It is kept because it exists to
prevent an otherwise-identical directory checked out on Unix and on Windows from producing different
hashes purely due to line-ending differences (CRLF vs. LF), which is a common and unwanted source of
false hash mismatches in practice. Relying solely on `.gitattributes` (or equivalent) to pin line
endings does not fully solve this, since some data files are intentionally meant to carry
platform-specific line endings and would be misclassified if forced to a single style.

Because normalizing line endings is a deliberate, lossy step - it makes two files that differ only
in line endings hash identically - implementations MAY offer skipping it (i.e. hashing every file's
raw bytes, with no text/binary distinction) as an additional, opt-in mode for cases where exact byte
fidelity matters more than cross-platform reproducibility. Implementations that do so MUST treat the
resulting hashes as a distinct key family from the default mode's hashes (following the same
versioning approach described in
[Backwards compatibility and migration](#backwards-compatibility-and-migration)), since the two modes
are not interchangeable and silently mixing them would reintroduce the same kind of ambiguity this
CEP otherwise eliminates.

### Why single out `\0`, `/`, `\\`, and `:` in filenames?

These four bytes have a well-documented history as sources of archive-extraction vulnerabilities:

- `\0`: Used to truncate strings passed to C-based filesystem APIs. Path-validation code then
  inspects a different (longer) name than the one actually written to disk.
- `/` and `\\`: Embedded path separators inside what should be a single path component. This is the
  classic vector for "Zip Slip"-style path traversal. It lets an entry escape the intended output
  directory during extraction.
- `:`: Significant on Windows. It introduces a drive letter or an NTFS Alternate Data Stream.

This CEP treats null bytes and drive-letter/UNC colons as hard errors. It normalizes path separators
explicitly (see Specification). Implementations are not left to independently decide - and
potentially disagree - on how to handle these historically dangerous characters.

### Why require UTF-8-encodable paths?

On POSIX systems, filenames are arbitrary byte sequences and are not guaranteed to be valid UTF-8.
Python (and similar language runtimes) bridges this gap by decoding raw filesystem paths with a
`surrogateescape` error handler ([PEP 383](https://peps.python.org/pep-0383/)): any byte that isn't
valid UTF-8 is silently mapped to a lone surrogate code point (`U+DC80`-`U+DCFF`) instead of raising
an error. This makes it easy to obtain a `str` for any path on disk, but that `str` is not itself
valid Unicode text, and it is easy to forget that a later encoding step needs to reject it rather
than pass it through.

If an implementation is not careful - for example, by explicitly or implicitly re-encoding with
`errors="surrogateescape"` instead of the default strict handler - a non-UTF-8 filename can silently
round-trip into the hash stream as an encoded surrogate, rather than causing an error. That would
mean two different, non-UTF-8 filenames could feed distinguishable-looking but non-standard byte
sequences into the hasher, or, depending on the implementation, be normalized in incompatible ways
across languages and platforms, undermining the cross-platform reproducibility this CEP is meant to
guarantee. Requiring implementations to error out on non-UTF-8 paths - i.e. to encode with a strict
error handler, not `surrogateescape` - keeps the hash stream well-defined and prevents this class of
implementation-specific divergence.

### Backwards compatibility and migration

The algorithm change produces different digests for the same directory contents, so existing stored
hashes computed with CEP 19 are not compatible with hashes computed under this CEP. Implementations
that currently use CEP 19 should:

1. Treat the v1 (CEP 19) and v2 (this CEP) hashes as distinct key families (e.g. by using
   different key names such as `content_sha256` vs `content_sha256_v2`, or by tagging stored
   hashes with a version identifier).
2. Provide an option to compute hashes using the CEP 19 algorithm for backwards compatibility with
   existing stored hashes.

The `conda-build` implementation in [conda/conda-build#5992][conda-build-5992] follows this
approach by retaining support for the legacy algorithm behind a compatibility flag.

## Backwards Compatibility

This CEP changes the computed hash for any directory that contains entries whose relative path or
(for symlinks) target path contains any of the bytes `F`, `D`, `L`, or `-`. In practice, that means
many real-world directories will produce a different digest under this CEP than under CEP 19.

Existing `content_sha256`, `content_sha384`, and `content_sha512` recipe keys continue to be
validated using the original CEP 19 algorithm (legacy mode) but are deprecated; implementations
SHOULD emit a deprecation warning when these keys are used. New recipes SHOULD migrate to
`content_sha256_v2`, `content_sha384_v2`, and `content_sha512_v2`, which are validated using the
fixed algorithm defined in this CEP.

## Alternatives

### Merkle trees

Merkle trees provide a collision-resistant structure by design, since each node's hash incorporates
the hashes of its children rather than raw content bytes. They were explicitly considered and
rejected in CEP 19 for simplicity reasons. That rationale still applies here: the fix requires only
a small, localized change to the existing algorithm, and the benefits of Merkle trees (efficient
incremental updates, pinpointing which file changed) are not needed for this use case.

### A different separator byte

Choosing a separator byte that is unlikely to appear in paths (e.g. `\0`) would not by itself close
the vulnerability. This CEP already forbids `\0` in path components (see
[Specification](#specification)), but file content is arbitrary bytes and may legitimately contain
`\0`, so a null-byte separator could still be defeated via file content the same way `-` can be
today. Length-prefixing every variable-length field - paths, symlink targets, and file content, as
this CEP already does - is the only approach that is provably collision-free regardless of what
bytes appear in filenames or file data.

## References

- The hash collision bug is reported in [`conda/ceps#150`][ceps-issue-150].
- The working fix is implemented in [`conda/conda-build#5992`][conda-build-5992].
- CEP 19 (superseded): [`cep-0019.md`](cep-0019.md).
- The original issue that motivated CEP 19: [`conda-build#4762`][conda-build-4762].
- Netstrings, a well-known length-prefixing format: [cr.yp.to/proto/netstrings.txt][netstrings].

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

<!-- links -->

[RFC2119]: https://www.ietf.org/rfc/rfc2119.txt
[ceps-issue-150]: https://github.com/conda/ceps/issues/150
[conda-build-5992]: https://github.com/conda/conda-build/pull/5992
[conda-build-4762]: https://github.com/conda/conda-build/issues/4762
[netstrings]: https://cr.yp.to/proto/netstrings.txt
