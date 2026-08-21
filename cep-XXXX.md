# CEP XXXX - Prefix replacement at install time

<table>
<tr><td> Title </td><td> Prefix replacement at install time </td></tr>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Chris Burr &lt;christopher.burr@cern.ch&gt; </td></tr>
<tr><td> Created </td><td> Jul 15, 2026 </td></tr>
<tr><td> Updated </td><td> Jul 22, 2026 </td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/180 </td></tr>
<tr><td> Implementation </td><td> NA (documents existing behavior; see <a href="https://github.com/conda/conda/blob/2b543296f5c8a08a78ad2a8a5251091c3538f205/conda/core/portability.py">conda</a>, <a href="https://github.com/mamba-org/mamba/blob/614b93b8d7db3c9112943bedfaf1d464cdb8401a/libmamba/src/core/link.cpp">libmamba</a>, <a href="https://github.com/conda/rattler/blob/720114bff4675dc99ac32c18df88600478efdc87/crates/rattler/src/install/link.rs">rattler</a>) </td></tr>
</table>

> The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
> "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this
> document are to be interpreted as described in [RFC2119][RFC2119] when, and
> only when, they appear in all capitals, as shown here.

[RFC2119]: https://datatracker.ietf.org/doc/html/rfc2119

## Abstract

Conda packages are built inside a placeholder prefix. At install time, files
that embed this placeholder are patched to point at the target environment.
How this patching works has never been written down: it exists as code in
conda, libmamba, and rattler, and the three implementations disagree in
several places. This CEP documents the behavior. The parts all installers
share are stated normatively; the divergences are recorded as such.

## Motivation

[CEP 34](./cep-0034.md) defines the `prefix_placeholder` and `file_mode`
fields of `paths.json` but says only that the placeholder "MAY be replaced at
install time with the target location". Everything else, from binary padding
to shebang handling, is undocumented.

The gap has practical costs. Proposals that build on replacement, such as the
prefix offsets CEP ([conda/ceps#179][ceps-179]), have nothing to cite.
Installers have dropped behavior without tracing what it was for: rattler
removed the only Windows binary replacement after judging the "pyzzer"
launcher format irrelevant ([conda/rattler#589][rattler-589]), although the
launchers pip generates today still use it, and conda's multi-encoding
replacement ([conda/conda#9946][conda-9946]) is implemented nowhere else. The
same package can install correctly under one installer and broken under
another. Documenting the status quo is a prerequisite for deciding which of
these behaviors belong to the format and which are bugs.

## Nomenclature

- _Placeholder_: the `prefix_placeholder` value of a path entry, i.e. the
  prefix the package was built in.
- _Target prefix_: the absolute path of the environment being installed into.
- _Occurrence_: a leftmost, non-overlapping match of the placeholder's UTF-8
  encoding in a file's bytes.
- _Target platform_: the platform the environment is being created for.
  Usually this is the machine running the installer, but not when creating
  environments for another platform, and `noarch` packages are installed on
  every platform. Some behavior documented below is instead keyed to the
  installing machine; this distinction is noted where it applies.

## Specification

Only files whose path entry carries a `prefix_placeholder` are processed. All
other files are linked or copied unmodified. Which files receive an entry is
decided at build time and is out of scope here.

### Text files

Installers MUST replace every occurrence of the placeholder with the target
prefix. The file length may change.

When the target prefix contains backslashes (Windows), installers MUST
convert them to forward slashes before replacement. This matches the
separator convention CEP 34 requires of the placeholder itself and avoids
producing invalid escape sequences in patched source files.

### Binary files

Binary replacement MUST preserve the file length. Installers replace each
occurrence, shift the remainder of the surrounding NUL-terminated string
towards the start, and fill the gap before the original NUL terminator with
NUL bytes. A target prefix longer than the placeholder cannot be padded and
MUST be reported as an error.

When the target platform is Windows, installers MUST NOT apply C-string
replacement. The pyzzer rewrite described under divergences is the one
exception conda and libmamba make.

On macOS, modifying a Mach-O file invalidates its code signature. All three
installers re-sign modified binaries with an ad-hoc signature after
replacement.

### Shebang lines

On Unix target platforms, a text file starting with `#!` gets special
treatment: the first line is rewritten as a unit rather than by plain
substitution. If the patched interpreter path fits within the length limit
and contains no spaces, it is kept. Otherwise the line is rewritten to an
`#!/usr/bin/env <program>` form, on the assumption that the environment will
be activated when the script runs. The limits in use are 127 bytes on Linux
and 512 on macOS.

The rewritten output differs between installers; see below. Only the intent
is shared: the first line must remain a working interpreter directive.

## Known divergences

| Behavior | conda | libmamba | rattler |
| --- | --- | --- | --- |
| UTF-16/32 occurrences | replaced | not replaced | not replaced |
| pyzzer launchers (Windows) | shebang rewritten | shebang rewritten | untouched |
| Shebang limit keyed to | installing machine | installing machine | target platform |
| `paths_version != 1` | error | error | not checked |
| Unknown `file_mode` | error | first-character match | error |

### Encodings

conda replaces occurrences of the placeholder encoded as UTF-8, UTF-16-LE/BE
and UTF-32-LE/BE, in both text and binary mode. This was added by
[conda/conda#9946][conda-9946] for packages that store paths as wide strings
([conda/conda#4298][conda-4298], wxWidgets). libmamba and rattler replace
UTF-8 only; [mamba-org/mamba#2215][mamba-2215] tracks this but was never
implemented. Neither conda-build nor rattler-build detects wide-encoding
occurrences at build time, so affected files only receive a path entry
through conda-build's `binary_has_prefix_files` or by also containing a UTF-8
occurrence.

The multi-encoding replacement is a sequence of byte-level search passes,
one per encoding in the order listed above, and byte-level search cannot
always tell the two endiannesses of a wide encoding apart. An ASCII
character encodes to its ASCII byte plus zero bytes, on opposite sides
depending on the endianness, so the big-endian encoding of an ASCII string
contains the little-endian byte pattern of the same string at a shift of
one byte (three bytes for UTF-32), with the final zero byte supplied by
whatever follows the last character: the high bytes of the next character
or the NUL terminator. For example, a placeholder `/pfx` stored as a
NUL-terminated UTF-16-BE string, followed by one more zero byte (padding,
or the high byte of the next big-endian character), admits two complete
readings, each leaving a single unclaimed zero byte at the opposite end:

```text
bytes:       00 2f 00 70 00 66 00 78 00 00 00
read as BE:  └'/'┘ └'p'┘ └'f'┘ └'x'┘ └NUL┘
read as LE:     └'/'┘ └'p'┘ └'f'┘ └'x'┘ └NUL┘
```

A big-endian wide string containing the placeholder therefore also matches
the little-endian pass, which runs first and splices the little-endian
target at the shifted position. Whether the wrong guess matters depends on
the characters involved. Below U+0100 every byte the wide encoding adds is
zero, and the zeros are interchangeable between the two readings: the
spliced bytes read back correctly at the big-endian alignment, so the
wrong guess produces exactly the bytes the right one would. At U+0100 and
above the added bytes are no longer zero, the shift pairs bytes across
character boundaries, and the string is corrupted instead of replaced (a
little-endian splice of `ā`, U+0101, reads back big-endian as the pair
U+0001, U+0170). The ambiguity is symmetric, since a little-endian string
preceded by a zero byte contains a phantom big-endian match one byte
earlier, so no pass order resolves it; it merely goes unnoticed while the
target prefix and the remainder of the affected string stay below U+0100,
which paths in practice almost always do. A target prefix containing
characters at or above U+0100, installed over a wide string of the
opposite endianness, is the combination that corrupts. Metadata that
records the encoding of each occurrence, as proposed in
[conda/ceps#179][ceps-179], is not subject to this ambiguity.

### pyzzer launchers

pip, via distlib, creates Windows console-script executables as a stub
`.exe` with a shebang line and a zipped script appended. conda and libmamba
detect the appended archive and rewrite the embedded shebang; this is the
only binary replacement either performs on Windows. rattler removed its
C-string replacement on Windows in [conda/rattler#589][rattler-589] without
implementing the pyzzer rewrite, so packages that ship pip-generated entry
points keep their build-time interpreter paths when installed by rattler.

### Shebang details

conda and libmamba derive the length limit from the machine performing the
installation; rattler derives it from the target platform. The results
differ when creating an environment for another platform. The rewritten
lines also differ: conda escapes spaces in the interpreter path, while
rattler rewrites Python interpreters to a `/bin/sh` trampoline instead of
the `#!/usr/bin/env` form.

### Format strictness

conda and libmamba refuse a `paths.json` whose `paths_version` is not `1`,
with an explicit "too new" error. rattler does not check the field. conda
and rattler reject unknown `file_mode` values when parsing; libmamba matches
only the first character (`t` for text, `b` for binary) and treats anything
else as text at link time. A future CEP that changes replacement semantics
can therefore use `paths_version` as an upgrade gate for conda and libmamba,
but not, today, for rattler.

## What this CEP does not decide

Whether the divergent behaviors are features to standardize or bugs to
retire is left to follow-up proposals, as is everything that changes the
format: recording occurrence positions in `paths.json`
([conda/ceps#179][ceps-179]) and alternative padding strategies for binaries
([conda/rattler#2342][rattler-2342], [conda/rattler#2503][rattler-2503]).

## References

- [conda - `conda/core/portability.py`](https://github.com/conda/conda/blob/main/conda/core/portability.py)
- [libmamba - `src/core/link.cpp`](https://github.com/mamba-org/mamba/blob/main/libmamba/src/core/link.cpp),
  [`src/core/package_paths.cpp`](https://github.com/mamba-org/mamba/blob/main/libmamba/src/core/package_paths.cpp)
- [rattler - `crates/rattler/src/install/link.rs`](https://github.com/conda/rattler/blob/main/crates/rattler/src/install/link.rs)
- [CEP 34 - Contents of conda packages](./cep-0034.md)
- [conda-build documentation - Making packages relocatable](https://docs.conda.io/projects/conda-build/en/stable/resources/make-relocatable.html)

[ceps-179]: https://github.com/conda/ceps/pull/179
[conda-4298]: https://github.com/conda/conda/issues/4298
[conda-9946]: https://github.com/conda/conda/pull/9946
[mamba-2215]: https://github.com/mamba-org/mamba/issues/2215
[rattler-589]: https://github.com/conda/rattler/pull/589
[rattler-2342]: https://github.com/conda/rattler/issues/2342
[rattler-2503]: https://github.com/conda/rattler/pull/2503

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
