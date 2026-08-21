# CEP XXXX - Prefix placeholder offsets in `paths.json`

<table>
<tr><td> Title </td><td> Prefix placeholder offsets in <code>paths.json</code> </td></tr>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Chris Burr &lt;christopher.burr@cern.ch&gt; </td></tr>
<tr><td> Created </td><td> Jul 9, 2026 </td></tr>
<tr><td> Updated </td><td> Jul 15, 2026 </td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/179 </td></tr>
<tr><td> Implementation </td><td> https://github.com/conda/rattler/pull/2565 </td></tr>
<tr><td> Requires </td><td> CEP 34, https://github.com/conda/ceps/pull/180 </td></tr>
</table>

> The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
> "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this
> document are to be interpreted as described in [RFC2119][RFC2119] when, and
> only when, they appear in all capitals, as shown here.

[RFC2119]: https://datatracker.ietf.org/doc/html/rfc2119

## Abstract

This CEP adds two optional fields to the path entries of `./info/paths.json`
(see [CEP 34](./cep-0034.md)): `offsets`, which records, per encoding, the
byte positions at which the prefix placeholder can be replaced by plain
substitution, and `shebang_length`, which marks a leading shebang line that
installers transform under their own rules. Together they allow installers to
perform prefix replacement without searching file contents, and to compute
the exact size of a file after replacement without rendering it.

## Motivation

### Linking performance

For every path entry with a `prefix_placeholder`, installers must read the
complete file contents to search for occurrences of the placeholder before
writing the patched copy into the target environment. The build tool already
located every occurrence when it created the package: `conda-build` and
`rattler-build` scan each file for the build prefix in order to decide whether
to record a `prefix_placeholder` at all. That information is discarded when
the package is written, and every installation recomputes it.

With the occurrences recorded in `paths.json`, replacement becomes a plain
copy with substitutions spliced in at known positions. For binary files, where
replacement preserves the file length, an installer can go further and patch
only the affected byte ranges of a copy-on-write clone of the cached file
(e.g. created with reflink) instead of streaming a full copy.

### Virtual filesystems

An on-demand virtual filesystem that materializes conda environments lazily
(such as the RattlerVFS work in [conda/rattler#2032][rattler-2032]) needs to
answer `stat()` calls, i.e. report the final size of a file, before the file
contents are ever read, and needs to serve reads of arbitrary ranges of the
patched file directly from the original package data.

Both needs reduce to knowing, without reading the file, where the placeholder
occurs and how the file length changes. For binary files replacement preserves
the length. For text files the length changes by a fixed amount per
occurrence, except for the shebang line, which installers rewrite under
special rules. `offsets` and `shebang_length` provide exactly the missing
information.

[rattler-2032]: https://github.com/conda/rattler/pull/2032

## Specification

This CEP amends the _path entry_ schema of `./info/paths.json` defined in
[CEP 34](./cep-0034.md). The replacement behavior itself is documented in
[conda/ceps#180][ceps-180]; this CEP does not change what replacement
produces, only how occurrences are located. Two optional keys are added to
each path entry:

- `offsets: list[dict]`. Optional. A list of _offset groups_, each recording
  where the placeholder occurs in the file contents under one encoding, as
  stored in the package (i.e. before any replacement). It MUST NOT be present
  unless `prefix_placeholder` is present.
- `shebang_length: int`. Optional. The length in bytes of the file's first
  line, including the terminating newline. Its presence is REQUIRED under the
  conditions described below.

Each offset group MUST be a dictionary with exactly two keys:

- `encoding: str`. One of `utf-8`, `utf-16-le`, `utf-16-be`, `utf-32-le`, or
  `utf-32-be`: the encodings replaced by existing installers.
- `ranges: list[int] | list[list[int]]`. The byte offsets of the occurrences
  under that encoding. Its shape depends on `file_mode`, as described below,
  and it MUST NOT be empty.

Throughout this CEP, an _occurrence_ under an encoding is a leftmost,
non-overlapping match of the placeholder encoded with that encoding, i.e. the
matches found by a single left-to-right search. This is the same semantics
used by the search-based replacement in existing installers; which encodings
each installer searches is documented in [conda/ceps#180][ceps-180].

`offsets` MUST NOT contain two groups with the same encoding, and the byte
ranges recorded across all groups MUST NOT overlap. Groups SHOULD be sorted
by their `encoding` so that equivalent metadata serializes identically. The
list itself MUST NOT be empty, except for `file_mode: text` entries where
`shebang_length` is present and every occurrence falls within the shebang
region.

`paths_version` remains `1`.

### Text offsets

When `file_mode` is `text`, the `ranges` of each group MUST be a flat list of
integers, e.g. `{"encoding": "utf-8", "ranges": [10, 45]}`. Each integer is
the offset, in bytes from the beginning of the file, at which one occurrence
under the group's encoding begins.

Each group MUST contain every occurrence under its encoding except those
inside the shebang region (see `shebang_length` below). Its values MUST be
sorted in strictly increasing order and occurrences MUST NOT overlap: each
value MUST be greater than or equal to the previous value plus the byte
length of the placeholder under that encoding.

### Binary offsets

When `file_mode` is `binary`, the `ranges` of each group MUST be a list of
lists of integers, e.g.
`{"encoding": "utf-8", "ranges": [[64, 96], [200, 240, 300]]}`. Replacement
in binary files operates on NUL-terminated strings (C strings), because the
padding that keeps the file length unchanged must stay within the string that
contains the occurrence. The NUL terminator is the encoding's zero code unit:
one zero byte for UTF-8, two for UTF-16, four for UTF-32. Each inner list
describes one C string that contains at least one occurrence under the
group's encoding:

- All values except the last are the offsets, in bytes from the beginning of
  the file, at which an occurrence begins. They MUST be sorted in strictly
  increasing order and MUST NOT overlap, as for text offsets.
- The last value is the offset of the first byte of the NUL terminator that
  ends the C string, or the file size when no terminator follows the final
  occurrence. Every occurrence offset `o` in the same inner list MUST satisfy
  `o + len(placeholder under this encoding) <= nul_offset`.

Each inner list MUST contain at least two values. Within a group, the inner
lists MUST be sorted by their first element and together they MUST cover
every occurrence under the group's encoding.

### `shebang_length`

`shebang_length` MUST be present if and only if all of the following hold:

- `offsets` is present,
- `file_mode` is `text`, and
- the file starts with the bytes `#!`.

Note that its presence does not depend on whether the first line contains the
placeholder (see Rationale).

Its value MUST be `i + 1`, where `i` is the offset of the first newline byte
(`0x0A`) in the file, or the size of the whole file when it contains no
newline. A carriage return (`0x0D`) preceding the newline lies inside the
region.

The first `shebang_length` bytes of the file form the _shebang region_.
Occurrences inside the region MUST NOT be listed in any group of `offsets`,
so every recorded value MUST be greater than or equal to `shebang_length`
when it is present. The region is transformed by the installer's shebang
replacement rules rather than by substitution at listed offsets (see
Installer behavior).

This yields a simple consumer contract: when `offsets` is present without
`shebang_length`, the file does not begin with `#!` and the recorded
positions are the only places the file changes; no content inspection is ever
needed. When `shebang_length` is present, at most the first `shebang_length`
bytes must be read to determine how the region transforms.

### Producer requirements

Build tools MAY include `offsets` and `shebang_length` when writing
`./info/paths.json`. When present, the fields MUST be exhaustive and
consistent with the file contents: for each of the five encodings, every
occurrence MUST either be listed in that encoding's group or fall within the
shebang region, and a group MUST be present exactly when at least one
occurrence is listed in it. Producers therefore MUST search the file under
all five encodings before emitting the field; the absence of a group is a
statement that the file contains no such occurrences. An installer relying on
the recorded positions MUST end up with exactly the bytes its own
search-based replacement would produce. Tools that modify the contents of
files in an existing package (for example repackaging or transmutation tools)
MUST update the fields or remove them.

The binary form describes the length-preserving C string splice only. Files
to which an installer's search-based path applies a different transformation
MUST NOT carry `offsets`. In particular, producers MUST omit the fields for
Windows launcher executables with an appended script archive (distlib
"pyzzer" launchers), which conda and libmamba patch with a length-changing
shebang rewrite.

### Installer behavior

Installers MAY use `offsets` to locate placeholder occurrences instead of
searching the file contents. When the field is absent, installers MUST locate
occurrences by searching, as they do today.

Installers MUST apply exactly the groups whose encodings their own
search-based replacement covers: applying a group the search-based path would
not handle, or skipping one it would, makes the two paths produce different
bytes for the same package.

Offsets are absolute positions in the original file. When splicing,
installers process the recorded ranges in file order regardless of which
group they come from. The bytes between ranges, before the first range
(starting from `shebang_length` when present), and after the last range MUST
be copied verbatim. For reference:

- In text files, each occurrence is replaced with the target prefix encoded
  with the group's encoding, and the file length may change. When
  `shebang_length` is present, the shebang region MUST be handled by the
  installer's shebang replacement rules rather than by substitution at listed
  offsets: on Unix targets the patched line is kept when it fits, but
  collapses to an `#!/usr/bin/env <program>` form when it would exceed kernel
  limits (127 bytes on Linux). The input to the shebang rules is the region
  excluding its trailing newline byte (when present), which is copied through
  unchanged. On targets without special shebang handling, installers MUST
  perform plain placeholder replacement within the shebang region, which
  requires searching at most the first `shebang_length` bytes.
- In binary files, the target prefix MUST NOT be longer than the placeholder
  under the same encoding. Within each affected C string, occurrences are
  replaced, the remaining bytes of the string shift towards the start
  accordingly, and the gap before the original NUL terminator (or the end of
  file, for an unterminated final string) is filled with zero bytes, so the
  overall file length is unchanged.

If the shape of a group's `ranges` does not match `file_mode`, a group has an
unrecognized `encoding` or unrecognized members, or the values are
inconsistent with the file (out of range, unsorted, overlapping, or the
encoded placeholder is not present at a recorded position), installers SHOULD
fall back to searching the file contents and MAY report a warning or an
error. Future CEPs may define additional encodings or group members; until an
installer implements such a CEP, an unknown value is indistinguishable from
corrupt metadata and the fallback applies.

### Computing the size after replacement

This section is informative. For an encoding `E`, let `p_E` and `t_E` be the
byte lengths of the placeholder and the target prefix encoded with `E`, and
`n_E` the number of occurrences the installer will replace under `E`. For a
file of size `S`, the size after replacement is:

- for `file_mode: binary`: `S`, unchanged;
- for `file_mode: text` without `shebang_length`:
  `S + sum(n_E * (t_E - p_E))`;
- for `file_mode: text` with `shebang_length`, on targets where the installer
  rewrites shebang lines: the length of the rewritten first line (computable
  from the first `shebang_length` bytes of the file) plus
  `(S - shebang_length) + sum(n_E * (t_E - p_E))`;
- for `file_mode: text` with `shebang_length`, on targets where the installer
  performs plain replacement within the region: the same sum, extended by the
  occurrences found inside the region (searching at most the first
  `shebang_length` bytes).

In every case, at most `shebang_length` bytes of the file must be read.

### Test cases

This section is informative. Implementations on either side SHOULD cover at
least:

1. a Unix target with a target prefix short enough that the patched shebang
   line is kept;
2. a Unix target with a target prefix long enough that the shebang collapses
   to the `#!/usr/bin/env <program>` form;
3. a non-rewriting target with an occurrence inside the shebang region, e.g. a
   `noarch` package installed on Windows;
4. a shebang file with no trailing newline, where `shebang_length` equals the
   file size;
5. a file whose only occurrence is in the shebang line, where `offsets` is the
   empty list;
6. multiple occurrences within one shebang line;
7. a shebang line longer than the kernel limit that contains no occurrence of
   the placeholder;
8. a binary file whose final C string is unterminated at the end of the file;
9. a binary file with occurrences under more than one encoding, installed by
   an installer that covers all of them and by one that covers only UTF-8.

## Rationale

### Why optional, advisory fields

Existing packages do not carry these fields, so installers have to keep the
searching code path in any case. Making the fields advisory means a package
that carries them installs identically, only faster, and a package that lacks
them behaves exactly as today. For the same reason `paths_version` is not
bumped: existing installers ignore unknown keys in path entries, and ignoring
these keys is harmless.

### Why offsets carry an encoding

Installers do not agree on which encodings of the placeholder they replace:
conda searches UTF-8, UTF-16, and UTF-32 variants (added in
[conda/conda#9946][conda-9946] for packages that store paths as wide strings,
[conda/conda#4298][conda-4298]), while rattler and libmamba search UTF-8 only
([mamba-org/mamba#2215][mamba-2215] is open; [conda/ceps#180][ceps-180]
documents the divergence). Recording the encoding with each group lets one
package serve every installer: each applies exactly the groups its own
search-based replacement covers, so each installer's fast path reproduces its
own slow path. The closed set of encoding names doubles as validation, and a
new name can only be introduced by a CEP that also settles how search-based
replacement handles that encoding.

### Why binary offsets are grouped by C string

Binary replacement must preserve the file length, and the NUL padding must
stay within the affected C string. The position of the string's terminator is
therefore required, and multiple occurrences within one string share a single
terminator. Grouping records each terminator exactly once and keeps the values
that must be interpreted together in one place.

### Why the shebang line is excluded from `offsets`

An occurrence inside a shebang line cannot be patched by plain substitution.
Whether the patched line keeps the target prefix or collapses to an
`#!/usr/bin/env <program>` form depends on the length of the target prefix,
which is only known at install time, so the rewritten line cannot be derived
from the placeholder and target lengths alone. Keeping such occurrences out of
`offsets` preserves a simple invariant: `offsets` is exactly the list of
positions whose handling never depends on install-time shebang policy, and
`shebang_length` marks the one region that does, and bounds how much of the
file must be read to handle it.

### Why `shebang_length` does not depend on the line containing the placeholder

Existing installers collapse an over-long first line even when it contains no
placeholder: both conda and rattler apply the length check to the line after
a replacement that may have changed nothing. If the region were only marked
when it contains an occurrence, an installer relying on the recorded offsets
would produce different bytes than its search-based path for such files, and
the size formulas above would be wrong. Tying the presence of
`shebang_length` only to `#!` also keeps the consumer contract simple: no
`shebang_length` means no content inspection at all.

### Backwards compatibility

The change is purely additive. Packages that include the new fields can be
installed by older tools, which ignore the unknown keys and search file
contents as before. Packages without the new fields are unaffected.

## Examples

A text file whose first line is the shebang
`#!/opt/placeholder/bin/python` (30 bytes including the newline, containing
the 16-byte placeholder) and with one further occurrence of the placeholder at
offset 71. The occurrence inside the shebang is covered by `shebang_length`
and is not listed in `offsets`:

```json
{
  "_path": "bin/example-script",
  "path_type": "hardlink",
  "file_mode": "text",
  "prefix_placeholder": "/opt/placeholder",
  "offsets": [{"encoding": "utf-8", "ranges": [71]}],
  "shebang_length": 30,
  "sha256": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
  "size_in_bytes": 512
}
```

Installed on a Unix target, the first 30 bytes minus the trailing newline are
fed through the installer's shebang rules and the occurrence at offset 71 is
spliced. Installed on a Windows target, for example when the entry belongs to
a `noarch` package, no shebang rewriting applies: the installer instead
performs plain placeholder replacement within the first 30 bytes and then
splices the occurrence at offset 71.

A binary file with two C strings containing UTF-8 occurrences (one at offset
64 with its NUL terminator at 96, one with occurrences at 200 and 240 and its
terminator at 300), and one wide string with a UTF-16-LE occurrence at offset
384 (32 bytes long) whose two-byte NUL terminator starts at offset 448:

```json
{
  "_path": "lib/libexample.so",
  "path_type": "hardlink",
  "file_mode": "binary",
  "prefix_placeholder": "/opt/placeholder",
  "offsets": [
    {"encoding": "utf-16-le", "ranges": [[384, 448]]},
    {"encoding": "utf-8", "ranges": [[64, 96], [200, 240, 300]]}
  ],
  "sha256": "d7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592",
  "size_in_bytes": 4096
}
```

Replacing the 16-byte placeholder in the first C string with the 8-byte target
`/opt/env` rewrites bytes 64 to 88 to hold `/opt/env` followed by the rest of
the string shifted 8 bytes towards the start, and fills the 8-byte gap before
the terminator at offset 96 with zero bytes. An installer whose search-based
replacement covers UTF-16 also patches the wide string at 384 (a 16-byte
change, since each character occupies two bytes); an installer that only
searches UTF-8 leaves it untouched, exactly as its search would. The file
size does not change either way.

## Rejected ideas

### Bumping `paths_version` to `2`

The new fields are advisory and ignoring them is harmless. A version bump
would only prevent older tools from installing otherwise perfectly usable
packages.

### Listing shebang occurrences in `offsets`

Recording every occurrence, including those in the shebang line, would make
`offsets` a strict superset of the chosen layout: verifiable with a plain
search and sufficient, on non-rewriting targets, to compute sizes without any
content reads. It was rejected for its failure mode. The shortcut it invites,
splicing every listed offset without the shebang machinery, works for every
user whose patched shebang stays under the kernel limit and breaks only for
those with long target prefixes: the same latent, environment-dependent
failure class that placeholder padding in `conda-build` exists to suppress,
and one that is invisible to tests that do not use an over-long prefix. With
the chosen layout the same mistake leaves the placeholder in the first line
and fails on the first execution. Installers would also have to filter every
listed offset against the region boundary on every install, instead of
splicing the list uniformly.

### Making text offsets relative to the end of the shebang line

Since the listed offsets only apply to the part of the file after the shebang
line, they could be stored relative to it. The interpretation of the field
would then depend on other properties of the entry, and the values could not
be checked against the file contents without first re-deriving the shebang
boundary. Absolute offsets together with `shebang_length` carry the same
information and remain self-contained.

### A dictionary keyed by encoding

`offsets` could map encoding names directly to ranges,
`{"utf-8": [10, 45]}`, which is marginally simpler to parse and cannot
express duplicate groups. The group form was preferred because it gives any
future extension a natural place to put per-group attributes without changing
the container shape, and the dictionary's advantages are recovered by
requiring unique encodings and a sorted order. Note that the extensions
discussed so far (padding strategies, mixing text and binary substitution in
one file) change what replacement produces, and therefore need a versioned
format regardless of the container shape (see Future work).

### Recording the size after replacement directly

The size of a patched text file depends on the length of the target prefix,
which is unknown at build time.

### Recording C string terminators in a separate field

An earlier iteration of the implementation considered listing the C string end
offsets in a field parallel to the prefix offsets. Grouping keeps values that
must be interpreted together in one place and avoids two lists that can fall
out of sync.

### A separate metadata file

The offsets qualify the `prefix_placeholder` and `file_mode` values of
individual path entries. Storing them in a separate `./info/` file would
require correlating two files by path and could leave them inconsistent.

## Future work

The fields in this CEP are additive and advisory, which is what lets them
ride `paths_version` 1: an installer that ignores them behaves exactly as
today. Changes to what replacement produces cannot be introduced the same
way, because an installer that ignores them corrupts files instead of merely
missing an optimization. Two such changes came up while drafting this CEP:
alternative padding for binaries whose embedded strings are not
NUL-terminated ([conda/rattler#2342][rattler-2342],
[conda/rattler#2503][rattler-2503]), and substituting text and binary
occurrences in the same file. These belong in a future versioned paths format
gated by a `paths_version` bump, so that older installers fail with an
explicit upgrade error rather than corrupting files. conda and libmamba
enforce `paths_version` today; rattler does not, and that gap should be
closed well before any bump is proposed (see [conda/ceps#180][ceps-180]).

## References

- [CEP 34 - Contents of conda packages](./cep-0034.md)
- [conda/ceps#180 - Prefix replacement at install time (draft)][ceps-180]
- [conda/rattler#2032 - Implementation offsets in paths.json (original PR)](https://github.com/conda/rattler/pull/2032)
- [conda/rattler#2565 - Implementation offsets in paths.json (follow-up PR)](https://github.com/conda/rattler/pull/2565)
- [conda/conda#4298 - replace path placeholder even if it's stored in a wide string][conda-4298]
- [conda/conda#9946 - UTF 16 and UTF 32 fixes][conda-9946]
- [mamba-org/mamba#2215 - Also replace wide strings in binaries][mamba-2215]
- [conda-build documentation - Making packages relocatable](https://docs.conda.io/projects/conda-build/en/stable/resources/make-relocatable.html)
- [conda source - core/portability.py (search-based replacement, including multi-encoding search and pyzzer handling)](https://github.com/conda/conda/blob/main/conda/core/portability.py)

[ceps-180]: https://github.com/conda/ceps/pull/180
[conda-4298]: https://github.com/conda/conda/issues/4298
[conda-9946]: https://github.com/conda/conda/pull/9946
[mamba-2215]: https://github.com/mamba-org/mamba/issues/2215
[rattler-2342]: https://github.com/conda/rattler/issues/2342
[rattler-2503]: https://github.com/conda/rattler/pull/2503

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
