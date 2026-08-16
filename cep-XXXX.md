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
hash collisions when a filename, a symlink target, or a file's contents contained the same byte
sequences used as type markers or field separators. This CEP fixes that vulnerability by
length-prefixing every variable-length field in the hash stream, making all field boundaries
unambiguous.

## Motivation

The CEP 19 algorithm builds the hash stream for each directory entry by concatenating raw bytes in
the order:

```text
<path_bytes> <type_marker> <content_bytes> <separator "-">
```

Because there is no field-length information, two structurally different directory trees can produce
an identical byte stream whenever a filename, a symlink target, or a file's contents happen to
contain the same bytes used as type markers (`F`, `D`, `L`) or the entry separator (`-`).

**Concrete example:**

- **Tree 1:** a single file named `testFhello-world` with content `www`
- **Tree 2:** a file named `test` (content `hello`) and a file named `world` (content `www`)

Both trees produce the byte stream `testFhello-worldFwww-`, yielding the same digest: a true hash
collision on structurally different directory trees. The same construction works through file
contents rather than filenames, since content bytes are equally unbounded in the CEP 19 stream (see
[Rationale](#why-length-prefix-file-content-too) for a worked example).

An attacker who controls filenames or file contents could exploit this to produce a directory tree
whose computed hash matches that of a different, potentially malicious tree.

## Specification

### Entry collection

Given a directory (the "scanned directory"), recursively scan all of its contents. Each individual
regular file, each directory, and each symlink found anywhere beneath the scanned directory is one
**entry**: a single item produced by the scan, identified by its own path relative to the scanned
directory and contributing exactly one record of its own to the hash stream. A tree containing three
files and two subdirectories therefore has five entries, not one. The resulting set of entries is
what the rest of this algorithm operates on:

- **Regular files** are collected as entries. A regular file is the only entry type whose contents
  participate in the hash (see [File content handling](#file-content-handling)); every other type
  contributes only path-derived bytes.
- **Directories** are collected as entries in their own right, in addition to the entries for
  whatever they contain. This includes empty directories: an empty directory is collected and is
  represented solely by its own entry, which is what makes it visible to the hash at all.
- **Symlinks** are collected as symlinks and MUST NOT be followed. Whatever a symlink points at is
  therefore not scanned through that symlink - only the symlink's own entry (and its target path) is
  hashed, even when the target is a directory inside the scanned directory.
- **Any other entry type** (device nodes, FIFOs, sockets, ...) MUST cause the implementation to
  error out, per the [Hash stream](#hash-stream) rules below.
- The scanned directory itself (`.`) MUST NOT be included as an entry.

An entry's relative path MUST be normalized per [Path normalization](#path-normalization) before it
is used for anything. That normalized relative path is the only form of the path this algorithm ever
uses: it is what entries are sorted by here, and it is also what is fed into the hasher in steps 1
and 2 of the [Hash stream](#hash-stream).

Entries MUST be sorted by that path: NFC-normalize it, encode it as UTF-8, and compare the resulting
UTF-8 bytes, byte-wise, ordering by unsigned byte value (0-255).

### Path normalization

The paths MUST be normalized before they are sorted or fed into the hasher. The following rules
apply to both entry paths and symlink targets:

- Every path MUST be UTF-8-encodable. If a path contains bytes that are not valid UTF-8,
  implementations MUST error out rather than silently substituting or passing through the invalid
  bytes (see [Rationale](#why-require-utf-8-encodable-paths) for a Python-specific pitfall this
  guards against). Every rule below that speaks of encoding a path to UTF-8 relies on this: a path
  that fails here never reaches them.
- If any path component contains a null byte (`\0`), implementations MUST error out.
- Before encoding a path to UTF-8 for sorting or hashing, implementations MUST normalize it to NFC.
  If this leaves two entries with the same path, implementations MUST error out rather than silently
  feeding duplicate bytes into the hasher.
- Backslashes in the path MUST be normalized to forward slashes (e.g. `path\\to\\file`
  becomes `path/to/file`).
- `.` and `..` components MUST NOT be collapsed (e.g. `foo/../bar` MUST NOT be rewritten to `bar`);
  see [Rationale](#why-not-collapse-redundant-path-components).

**Entry paths** (the paths of directory entries) are additionally subject to:

- A leading `./` MUST be stripped (e.g. `./README.txt` becomes `README.txt`) before the rules below
  are applied.
- An entry path MUST NOT be absolute: a leading `/` MUST be rejected.
- An entry path MUST NOT contain a drive letter (e.g. `C:`) or a UNC prefix (e.g. `//server/share`).
- An entry path MUST NOT contain any `.` or `..` component.

Implementations MUST error out on an entry path that violates any of these rules, rather than
rewrite it to satisfy them.

**Symlink targets** are subject to different rules, since a symlink MAY legitimately point to an
absolute path:

- Symlink targets MAY be relative or absolute. A leading `/` is a legitimate absolute Unix path and
  MUST be preserved, not rejected.
- A symlink target MUST be hashed as stored, apart from the common rules above: `.` and `..`
  components, repeated slashes, and trailing slashes MUST all be preserved verbatim, and the target
  MUST NOT be resolved against the filesystem. Two symlinks whose stored targets differ are different
  symlinks, and MUST hash differently.
- Windows drive letters (e.g. `C:`) and UNC prefixes (e.g. `//server/share`) in a symlink target
  MUST cause the implementation to error out, because there is no meaningful cross-platform way to
  normalize them into the hash stream.

### File content handling

The bytes hashed for a regular file are its **unmodified raw bytes**:

- If the file can't be opened or read, implementations MUST error out.
- Otherwise, the unmodified raw bytes are exactly the file's raw bytes as read from disk. No UTF-8
  decode is attempted, no text/binary distinction is made, and no line-ending rewriting (e.g.
  `\r\n` -> `\n`) is performed.

See [Rationale](#why-doesnt-the-hash-normalize-line-endings) for why line endings are deliberately
left unnormalized, and Appendix A and Appendix B for the underlying research and mitigations.

Wherever the hash stream below refers to a file's content - both for the length prefix and for the
content bytes themselves - it refers to the unmodified raw bytes as defined here. The length prefix
MUST be the raw on-disk byte length. A file whose only difference from another is CRLF vs. LF line
endings therefore produces a different length prefix and different content bytes, and the two are
expected to hash differently.

### Hash stream

For each entry in the sorted contents, feed the following bytes into the hasher in order:

1. The byte length of the UTF-8-encoded normalized relative path, written in decimal and that decimal
   string encoded as UTF-8, followed by the UTF-8 encoded byte of `:`.
2. The UTF-8 encoded bytes of the normalized relative path (per
   [Path normalization](#path-normalization)).
3. Then, depending on the entry type:
   - For a **regular file**:
     - The UTF-8 encoded byte of `F`.
     - The byte length of the file's unmodified raw bytes (per
       [File content handling](#file-content-handling)), written in decimal and that decimal string
       encoded as UTF-8, followed by the UTF-8 encoded byte of `:`.
     - The file's unmodified raw bytes (per
       [File content handling](#file-content-handling)).

     Content is length-prefixed for the same reason entry paths and symlink targets are: without it,
     content containing `-` followed by bytes that look like a valid subsequent entry can reproduce
     the byte stream of a different, structurally distinct tree (see
     [Rationale](#why-length-prefix-file-content-too) for a worked collision).
   - For a **directory**: the UTF-8 encoded byte of `D`, and nothing else.
   - For a **symlink**:
     - The UTF-8 encoded byte of `L`.
     - The byte length of the UTF-8-encoded symlink target path, written in decimal and that decimal
       string encoded as UTF-8, followed by the UTF-8 encoded byte of `:`.
     - The UTF-8 encoded bytes of the symlink target path, normalized per the common rules and the
       **Symlink targets** rules in [Path normalization](#path-normalization) (the **Entry paths**
       rules do not apply to symlink targets).
   - For **any other type**, implementations MUST error out.
4. The UTF-8 encoded byte of `-`.

### Summary of changes from CEP 19

| Field | CEP 19 | This CEP |
| --- | --- | --- |
| Path | `<path_bytes>` | `<len(path_bytes)>:<path_bytes>` |
| Symlink target | `<target_bytes>` | `<len(target_bytes)>:<target_bytes>` |
| File content | `<content_bytes>` | `<len(content_bytes)>:<content_bytes>` |
| File content normalization | Text/binary detection; CRLF -> LF rewrite for text files | None: raw on-disk bytes hashed as-is |
| Sorting | Raw Unicode code point comparison | NFC-normalized, UTF-8-encoded byte comparison |
| Error handling | Unreadable files, unknown entry types | Additionally: null bytes, invalid/absolute entry paths, `.`/`..` components in entry paths, drive letters/UNC prefixes, non-UTF-8 paths, NFC-induced path collisions |

Unlike CEP 19, this CEP no longer performs text/binary detection or line-ending normalization: file
content is hashed as raw on-disk bytes (see
[Rationale](#why-doesnt-the-hash-normalize-line-endings)). Combined with the new length prefixes,
this means a file whose only difference from another is CRLF vs. LF line endings now produces a
different digest under this CEP, even though CEP 19 hashed the two identically.

### Reference implementation

For Python 3.6+:

```python
import hashlib
import os
import re
import unicodedata
from pathlib import Path

_DRIVE_LETTER_RE = re.compile(r"^[A-Za-z]:")


def _encode_path(path: str) -> bytes:
    # `path` may contain surrogate-escaped code points (PEP 383) if the on-disk name isn't
    # valid UTF-8. Encoding with the default "strict" handler (not "surrogateescape") raises
    # UnicodeEncodeError in that case, which is the required behavior: error out rather than
    # silently letting non-UTF-8 bytes into the hash stream.
    return path.encode("utf-8")


def _normalize_path(path: str) -> str:
    # Applies the common rules in the order they are listed in the Specification: require
    # UTF-8-encodability, reject null bytes, normalize separators, then NFC-normalize.
    # "." and ".." components are deliberately NOT collapsed (no posixpath.normpath here):
    # for a symlink target, collapsing them changes which file the target names.
    _encode_path(path)  # raises before anything else looks at the path
    if "\0" in path:
        raise ValueError(f"path contains a null byte: {path!r}")
    return unicodedata.normalize("NFC", path.replace("\\", "/"))


def _normalize_entry_path(path: str) -> str:
    normalized = _normalize_path(path)
    while normalized.startswith("./"):  # scanner artifact, carries no information
        normalized = normalized[2:]
    if normalized.startswith("/"):
        raise ValueError(f"entry path must be relative: {normalized!r}")
    if _DRIVE_LETTER_RE.match(normalized):
        raise ValueError(f"entry path must not contain a drive letter: {normalized!r}")
    if any(part in (".", "..") for part in normalized.split("/")):
        # Cannot come from a directory scan; treat it as a caller bug rather than resolving it.
        raise ValueError(f"entry path must not contain '.' or '..' components: {normalized!r}")
    return normalized


def _normalize_symlink_target(target: str) -> str:
    # Everything the common rules don't touch is preserved verbatim: "." / ".." components,
    # repeated slashes and trailing slashes are all part of what the symlink actually stores.
    normalized = _normalize_path(target)
    if normalized.startswith("//"):
        raise ValueError(f"symlink target must not contain a UNC prefix: {normalized!r}")
    if _DRIVE_LETTER_RE.match(normalized):
        raise ValueError(f"symlink target must not contain a drive letter: {normalized!r}")
    return normalized


def _reraise(error: OSError) -> None:
    # os.walk swallows errors by default; a directory we cannot list would then be silently
    # skipped, hiding entries from the hash. Same reasoning as erroring out on unreadable files.
    raise error


def contents_hash(directory: str, algorithm: str) -> str:
    directory = Path(directory)
    entries = {}  # encoded relative path -> path on disk; the keys double as the seen-set
    # os.walk does not follow symlinks (followlinks=False is the default), which is what the
    # Specification requires: a symlink to a directory is reported as an entry in `dirnames`
    # but never descended into.
    for root, dirnames, filenames in os.walk(directory, onerror=_reraise):
        for name in dirnames + filenames:
            path = Path(root, name)
            rel = _normalize_entry_path(path.relative_to(directory).as_posix())
            rel_bytes = _encode_path(rel)
            if rel_bytes in entries:
                raise ValueError(f"NFC normalization collision on path: {rel!r}")
            entries[rel_bytes] = path

    hasher = hashlib.new(algorithm)
    for rel_bytes, path in sorted(entries.items()):
        hasher.update(f"{len(rel_bytes)}:".encode("utf-8"))
        hasher.update(rel_bytes)
        if path.is_symlink():
            target = _normalize_symlink_target(os.readlink(str(path)))
            target_bytes = _encode_path(target)
            hasher.update(b"L")
            hasher.update(f"{len(target_bytes)}:".encode("utf-8"))
            hasher.update(target_bytes)
        elif path.is_dir():
            hasher.update(b"D")
        elif path.is_file():
            hasher.update(b"F")
            with open(path, "rb") as fh:
                data = fh.read()  # raw on-disk bytes: no text/binary check, no line-ending rewrite
            hasher.update(f"{len(data)}:".encode("utf-8"))
            hasher.update(data)
        else:
            raise RuntimeError(f"Unknown file type: {path}")
        hasher.update(b"-")
    return hasher.hexdigest()
```

This implementation attempts to cover every normalization and error-handling rule from the
[Specification](#specification) above (NFC normalization and collision detection, null bytes,
`.`/`..` rejection in entry paths, absolute/drive-letter/UNC rejection, non-UTF-8 paths, unreadable
files); it is provided as a normative illustration, not a certified conformance suite, so a
discrepancy against the Specification text should be treated as a bug in this snippet rather than in
the rule it's illustrating.

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

### Why are entry paths checked rather than repaired?

An entry path is by construction relative to the scanned directory and built only from real
directory entry names, so [Entry collection](#entry-collection) cannot produce an absolute path, a
drive letter or UNC prefix, or a `.` or `..` component - none of those are directory entry names.
The entry path rules should therefore never fire on a correct implementation.

They are written as checks rather than as transformations for that reason. A path that violates one
did not come from the scan this CEP specifies, so the implementation has a bug or is being fed input
from somewhere else; rewriting the path would paper over that while quietly changing which file the
hash covers. Stopping is the only response that keeps the hash meaningful. The rules also mark where
entry paths and symlink targets part ways, since a symlink target MAY legitimately be absolute or
contain `..`.

The one transformation in the group, stripping a leading `./`, is there because some scanners report
paths that way. It carries no information and is not a repair of a malformed path.

### Why not collapse redundant path components?

Collapsing redundant path components, so that `foo/../bar` became `bar`, might seem like a natural
normalization step. That rule is not safe, and it is also not needed.

It is not needed for entry paths: those come from scanning a directory, and `.` and `..` are not
real directory entries, so a relative path built from scan results cannot contain them. There is
nothing to collapse. If such a component does show up, the path was built wrong, which is why this
CEP makes it an error instead.

It is not safe for symlink targets, which are the only place such components can legitimately
appear. POSIX resolves a path left to right, expanding each symlink as it goes, so `..` means "the
parent of whatever the preceding component resolved to" - not "undo the preceding component". If
`foo` is itself a symlink, the two targets name different files:

```text
a/foo   -> ../x/y     (a directory)
a/link1 -> foo/../bar resolves to x/bar
a/link2 -> bar        resolves to a/bar
```

Collapsing `foo/../bar` to `bar` would make `link1` and `link2` hash identically even though they
point at different files - a collision between structurally different trees, which is the class of
bug this CEP exists to remove. (The two also differ when `foo` does not exist: `foo/../bar` fails to
resolve, `bar` does not.)

Unlike NFC normalization or separator normalization, collapsing components buys nothing in return,
because there is no platform variance to remove: a symlink stores its target as an opaque string and
`readlink` hands back exactly those bytes on every platform. Two symlinks with different stored
targets are different symlinks, so this CEP hashes the target as stored.

### Why erroring out on unreadable files?

The rationale is unchanged from CEP 19: we can't verify the contents of such entries, and an
attacker could hide malicious content in those paths and later make them accessible
(e.g. by `chmod`ing them readable).

### Why doesn't the hash normalize line endings?

CEP 19 rewrote `\r\n` to `\n` in text files before hashing, so that an otherwise-identical directory
checked out on Unix and on Windows would still produce the same hash. This CEP deliberately does not
carry that forward: the hash covers every regular file's raw on-disk bytes, unmodified.

The problem is that a file's bytes alone cannot say whether its CRLFs are meaningful content or an
artifact of checkout-time conversion. Two files can be byte-for-byte identical on disk and still need
opposite treatment depending on what a git index (or equivalent checkout metadata) recorded for each

- information that lives outside the file and that the hash algorithm has no access to. Normalizing
line endings unconditionally treats both cases the same and erases a difference between the two files
that genuinely exists. See
[Appendix A](#appendix-a-why-file-bytes-do-not-reveal-which-crlfs-are-real) for a worked example.

Because this CEP's hash is defined purely over a directory's raw contents, it leaves line-ending
reconciliation to whoever controls the checkout rather than to the hashing algorithm.
[Appendix B](#appendix-b-avoiding-crlf-mismatches-at-checkout) recommends checkout-time and pre-hash
mitigations, plus a last-resort, platform-specific fallback hash for the cases those mitigations
can't cover.

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

This CEP changes the computed hash of any directory that contains at least one entry: the length
prefixes are added unconditionally, so the byte stream differs from CEP 19's even when no path,
symlink target, or file content contains a type marker or the entry separator. Only an empty
directory hashes identically under both algorithms. The collisions the change closes are those
involving an entry whose relative path, (for symlinks) target path, or file contents contain any of
the bytes `F`, `D`, `L`, or `-`.

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

## Appendix A: Why File Bytes Do Not Reveal Which CRLFs Are Real

This appendix elaborates on the claim in
[Rationale](#why-doesnt-the-hash-normalize-line-endings) that a file's raw bytes cannot say whether
its CRLF line endings are checkout-time noise or real content.

Consider a Windows checkout of a git repository containing two files:

| File | Git index (`i/`) | Working tree (`w/`) | Bytes on disk |
| --- | --- | --- | --- |
| `lf.txt` | LF | CRLF | `a\r\nb\r\n` |
| `crlf_committed.txt` | CRLF | CRLF | `a\r\nb\r\n` |

Both files have byte-for-byte identical contents on disk, but they need opposite treatment when
recovering a canonical, cross-platform form:

- `lf.txt` is stored in the index as LF. Git's checkout-time conversion (`core.autocrlf` or a `text`
  attribute) rewrote it to CRLF on the way to the working tree. Recovering the canonical form means
  converting its CRLFs back to LF.
- `crlf_committed.txt` is stored in the index as CRLF. Its CRLFs are the file's real, committed
  content and must be preserved as-is.

Nothing in either file's bytes distinguishes these two cases - the on-disk bytes are identical. Only
the git index records which file was converted and which was not. A hashing algorithm that only ever
sees the bytes on disk, as this CEP's algorithm does, cannot tell them apart, and normalizing both
unconditionally erases a distinction between the two files that genuinely exists. This is why
line-ending normalization is left out of the hash algorithm and pushed to whoever has access to the
index - see [Appendix B](#appendix-b-avoiding-crlf-mismatches-at-checkout) for how to do that.

## Appendix B: Avoiding CRLF Mismatches at Checkout

Because this CEP hashes raw on-disk bytes, a directory checked out from git with different
line-ending conversion settings can hash differently even when the two checkouts would otherwise be
considered equivalent. This appendix recommends ways to avoid that outside the hash algorithm itself.
Both recommendations apply only to git checkouts: a downloaded tarball is extracted without any
line-ending rewriting, so it already hashes the same on every platform and needs neither.

1. **Fix it at checkout.** Set `* text=auto eol=lf` in `.gitattributes`, or set
   `core.autocrlf=input`. This requires no additional tooling and solves the problem for everyone who
   clones the repository, since files are checked out with LF endings regardless of platform.

2. **If you cannot control the checkout, undo the conversion before hashing.** Run
   `git ls-files --eol` and inspect each file's reported index (`i/`) and working-tree (`w/`) line
   endings. For a file reported as `i/lf w/crlf`, replace `\r\n` with `\n` in memory before feeding
   its bytes to the hasher, to recover the form the index actually stores.

If, after applying these mitigations, two trees still differ in raw bytes - for example, files
intentionally marked `eol=crlf`, or files from a source that has no git index to consult at all -
they are different contents and are expected to hash differently; this is the algorithm working
correctly, not a bug. Where this is unavoidable, a recipe MAY carry an additional, platform-specific
hash as a last-resort fallback. Such a fallback hash
MUST be treated as a distinct key family from this algorithm's hashes, following the same versioning
approach as [Backwards compatibility and migration](#backwards-compatibility-and-migration).

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

<!-- links -->

[RFC2119]: https://www.ietf.org/rfc/rfc2119.txt
[ceps-issue-150]: https://github.com/conda/ceps/issues/150
[conda-build-5992]: https://github.com/conda/conda-build/pull/5992
[conda-build-4762]: https://github.com/conda/conda-build/issues/4762
[netstrings]: https://cr.yp.to/proto/netstrings.txt
