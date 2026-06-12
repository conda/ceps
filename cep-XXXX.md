# CEP XXXX - Computing the hash of the contents in a directory (v2)

<table>
<tr><td> Title </td><td> Computing the hash of the contents in a directory (v2) </td></tr>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> pb01ka &lt;gaganpb08singh@gmail.com&gt; </td></tr>
<tr><td> Created </td><td> Jun 4, 2026</td></tr>
<tr><td> Updated </td><td> Jun 5, 2026</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/issues/150 </td></tr>
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

Given a directory, recursively scan all its contents (without following symlinks) and sort them by
their full path as a Unicode string. More specifically, it MUST follow an ascending lexicographical
comparison using the numerical Unicode code points (i.e. the result of Python's built-in function
`ord()`) of their characters [^1].

The paths MUST be normalized before they are processed by the algorithm below:

- Backslashes in the path MUST be normalized to forward slashes (e.g. `path\\to\\file`
  becomes `path/to/file`).
- Redundant path components MUST be removed (e.g. `path/to/../to/file` becomes `path/to/file`).

For each entry in the sorted contents, feed the following bytes into the hasher in order:

1. The decimal representation of the byte length of the normalized relative path, encoded as UTF-8,
   followed by the UTF-8 encoded bytes of `:`.
2. The UTF-8 encoded bytes of the normalized relative path.
3. Then, depending on the entry type:
   - For a **regular file**:
     - The UTF-8 encoded bytes of `F`.
     - If the file is a text file (i.e. its entire contents can be UTF-8 decoded): the UTF-8
       encoded bytes of its line-ending-normalized contents (`\r\n` replaced with `\n`). If the
       file can't be opened, it MUST be handled as if it were empty.
     - If the file is binary: the raw bytes of its contents.
     - If the file can't be read, implementations MUST error out.
   - For a **directory**: the UTF-8 encoded bytes of `D`, and nothing else.
   - For a **symlink**:
     - The UTF-8 encoded bytes of `L`.
     - The decimal representation of the byte length of the symlink target path, encoded as UTF-8,
       followed by the UTF-8 encoded bytes of `:`.
     - The UTF-8 encoded bytes of the symlink target path (normalized as above).
   - For **any other type**, implementations MUST error out.
4. The UTF-8 encoded bytes of `-`.

### Summary of changes from CEP 19

| Field          | CEP 19           | This CEP                             |
| -------------- | ---------------- | ------------------------------------ |
| Path           | `<path_bytes>`   | `<len(path_bytes)>:<path_bytes>`     |
| Symlink target | `<target_bytes>` | `<len(target_bytes)>:<target_bytes>` |

All other aspects of the algorithm (sorting order, text vs. binary detection, line-ending
normalization, error handling) are unchanged.

### Stream comparison: CEP 19 vs this CEP

The table below shows the raw byte sequences fed to the hasher for two structurally different
directory trees that produce a **collision under CEP 19** but distinct digests under this CEP.

**Tree 1:** one file named `testFhello-world` (16 UTF-8 bytes) with content `www`.

**Tree 2:** a file named `test` (content `hello`) and a file named `world` (content `www`).

| Algorithm     | Tree 1                     | Tree 2                      | Collision? |
| ------------- | -------------------------- | --------------------------- | ---------- |
| CEP 19        | `testFhello-worldFwww-`    | `testFhello-worldFwww-`     | Yes        |
| This proposal | `16:testFhello-worldFwww-` | `4:testFhello-5:worldFwww-` | No         |

Under CEP 19 both trees yield the identical stream `testFhello-worldFwww-` and therefore the same
digest. Under this proposal, the `16:` length prefix on Tree 1 unambiguously marks the path as 16
bytes, so the `F` that follows is the type marker - not part of the filename. Tree 2 produces a
completely different stream and a different digest.

More cases discussed in the Examples section.

### Reference implementation

For Python 3.6+:

```python
import hashlib
from functools import partial
from pathlib import Path


def contents_hash(directory: str, algorithm: str) -> str:
    hasher = hashlib.new(algorithm)
    for path in sorted(Path(directory).rglob("*")):
        rel = path.relative_to(directory).as_posix().replace("\\", "/")
        rel_bytes = rel.encode("utf-8")
        hasher.update(f"{len(rel_bytes)}:".encode("utf-8"))
        hasher.update(rel_bytes)
        if path.is_symlink():
            target = str(path.readlink()).replace("\\", "/")
            target_bytes = target.encode("utf-8")
            hasher.update(b"L")
            hasher.update(f"{len(target_bytes)}:".encode("utf-8"))
            hasher.update(target_bytes)
        elif path.is_dir():
            hasher.update(b"D")
        elif path.is_file():
            hasher.update(b"F")
            try:
                # assume it's text
                lines = []
                with open(path) as fh:
                    for line in fh:
                        lines.append(line.replace("\r\n", "\n"))
                for line in lines:
                    hasher.update(line.encode("utf-8"))
            except UnicodeDecodeError:
                # file must be binary
                with open(path, "rb") as fh:
                    for chunk in iter(partial(fh.read, 8192), b""):
                        hasher.update(chunk)
        else:
            raise RuntimeError(f"Unknown file type: {path}")
        hasher.update(b"-")
    return hasher.hexdigest()
```

## Examples

### Example 1: Text file and subdirectory

Given the directory:

```text
mydir/
├── README.txt   (content: "Hello\n")
└── src/
```

Entries sorted by Unicode code points: `README.txt`, `src`.

**CEP 19 byte stream** (concatenated across both entries):

```text
README.txtFHello\n-srcD-
```

**This CEP byte stream:**

```text
10:README.txtFHello\n-3:srcD-
```

The `10:` prefix encodes the 10-byte path `README.txt`; `3:` encodes the 3-byte path `src`. The
type markers (`F`, `D`) and the entry separator (`-`) are unchanged and still unambiguous because
the path boundary is now known exactly.

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

### Example 3: The collision case (CEP 19 vulnerability)

This example reproduces the collision from the Motivation section at the byte-stream level.

**Tree 1** - one file named `testFhello-world` (content `www`):

| Step | Field             | Bytes fed to hasher |
| ---- | ----------------- | ------------------- |
| 1    | path length + `:` | `16:`               |
| 2    | path              | `testFhello-world`  |
| 3    | type marker       | `F`                 |
| 4    | file content      | `www`               |
| 5    | entry separator   | `-`                 |

Full stream: `16:testFhello-worldFwww-`

**Tree 2** - file `test` (content `hello`) followed by file `world` (content `www`):

| Step | Field                         | Bytes fed to hasher |
| ---- | ----------------------------- | ------------------- |
| 1    | path length + `:` for `test`  | `4:`                |
| 2    | path                          | `test`              |
| 3    | type marker                   | `F`                 |
| 4    | file content                  | `hello`             |
| 5    | entry separator               | `-`                 |
| 6    | path length + `:` for `world` | `5:`                |
| 7    | path                          | `world`             |
| 8    | type marker                   | `F`                 |
| 9    | file content                  | `www`               |
| 10   | entry separator               | `-`                 |

Full stream: `4:testFhello-5:worldFwww-`

The two streams are distinct, so the digests are distinct. Under CEP 19 both trees produced the
same stream `testFhello-worldFwww-`, making the collision possible.

## Rationale

### Why length-prefix rather than escaping?

An alternative fix would be to escape occurrences of the separator bytes inside filenames. However,
escaping requires a second escape character, which must itself be escaped, creating additional
complexity and potential for bugs. Length-prefixing is simpler, well-established (it is the basis
of netstrings and many binary protocols), and adds a constant, predictable overhead of a few bytes
per field.

### Why only prefix the path and symlink target?

Type markers (`F`, `D`, `L`) and the entry separator (`-`) are single fixed bytes that are always
present in a known position relative to the length-prefixed path. Because the path length is now
unambiguous, the parser always knows exactly where the path ends and where the type marker begins,
so these fields do not need their own length prefix. File contents are similarly unambiguous because
they are bracketed by the type marker on one side and the `-` separator on the other, with no
variable-length field interleaved.

### Why erroring out on unredable files?

The rationale is unchanged from CEP 19: we can't verify the contents of such entries, and an
attacker could hide malicious content in those paths and later make them accessible
(e.g. by `chmod`ing them readable).

### Backwards compatibility and migration

The algorithm change produces different digests for the same directory contents, so existing stored
hashes computed with CEP 19 are not compatible with hashes computed under this CEP. Implementations
that currently use CEP 19 SHOULD:

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
nearly all real-world directories will produce a different digest under this CEP than under CEP 19.

Existing `content_sha256`, `content_sha384`, and `content_sha512` recipe keys continue to be
validated using the original CEP 19 algorithm (legacy mode) but are deprecated; implementations
SHOULD emit a `PendingDeprecationWarning` when these keys are used. New recipes SHOULD migrate to
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

Choosing a separator byte that is unlikely to appear in filenames (e.g. `\0`) would reduce the
practical collision surface but would not eliminate it, since `\0` is a legal byte in many
filesystems' raw representations and the algorithm operates on Unicode strings. Length-prefixing is
the only approach that is provably collision-free regardless of file naming.

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
[^1]: This is what Python does. See "strings" in [Value comparisons](https://docs.python.org/3/reference/expressions.html#value-comparisons).
