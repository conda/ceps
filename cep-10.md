<table>
<tr><td> Title </td><td> JSON Patch Incremental Updates for repodata.json </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Daniel Holth &lt;dholth@gmail.com | dholth@anaconda.com&gt;</td></tr>
<tr><td> Created </td><td> Mar 30, 2022</td></tr>
<tr><td> Updated </td><td> Oct 11, 2022</td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> https://github.com/dholth/repodata-fly </td></tr>
</table>

## Abstract

`conda install` and other conda commands must download the entire per-channel
`repodata.json`, a file listing all available packages, if it has changed, but a
typical `repodata.json` update only adds a fraction of the total number of
packages. If conda could download just the changes, it would save bandwidth and
time. This document outlines a system to bring `repodata.json` up to date by
applying patches between successive versions. If it has not been too long since
the last complete `repodata.json` was fetched, `conda` can download a tiny file
to bring the user up to date.

## Narrative

When re-indexing a conda repository, also update a line-delimited file
`repodata.jlap` containing a leading checksum; zero or more RFC 6902 JSON Patch
documents listed from oldest to newest, one per line; a metadata line with a
hash of the most recent complete `repodata.json`; and a trailing checksum.

The `repodata.jlap` format has a leading and trailing checksum. The server adds
patches to `repodata.jlap` by truncating the trailing checksum and metadata,
appending new patches, a new metadata line, and a new trailing checksum. The
client receives the newest patches in a single round trip by requesting `Range:
bytes={offset of last metadata line read}-` until the end of the remote
file.

The checksum is constructed so that by saving an intermediate checksum, the
client can verify new patches even if it has discarded earlier, consumed
patches. If the trailing checksum does not match the local computed checksum,
then the file was corrupted or the server has begun a new patch series;
re-download the remote `.jlap` from the beginning.

`repodata.json` versions are identified by a hash of their verbatim contents.
Each patch is accompanied by a hash `from` an older version of the file, and a
hash `to` of a newer version of the file.

To apply patches, take the `BLAKE2-256` hash of the most recent complete
`repodata.json`. Follow the list of patches in `repodata.jlap` from the first
one whose `to` matches `latest`, to the next one whose `to` matches the more
recent `from` and so on, pushing these onto a stack until a patch is found whose
`from` hash matches the local `repodata.json`. If the desired `from` hash is
found, pop each patch off the stack, applying them in turn to the outdated
`repodata.json`. The result is logically equal to the latest `repodata.json`.

Since JSON Patch does not preserve formatting, the new `repodata.json` will not
hash equal to `latest` unless it is sorted and re-serialized, with the
normalization settings, if any, used by `conda index` or the `repodata.json`
generator. Otherwise, the updated local file should be considered to have the
`latest` hash for purposes of incremental updates.

If the desired hash is not found in the `repodata.jlap` patch set, download the
complete `repodata.json` as before.

An example of a patch against conda-forge `repodata.json`, adding packages to
this ~170MB (23MB compressed) file:

```
0000000000000000000000000000000000000000000000000000000000000000
... additional lines ...
{"to": "ea8a695e21baa8090691656bbe4a4d2240ee62cdc2539dc5940077ccf2a44efc", "from": "fda691c5ff4e265b580b0dc43cbb0bd95af9920a10bacf621b51e5cfd72baa03", "patch": [{"op": "add", "path": "/packages/mapbox_earcut-1.0.0-py310hbf28c38_2.tar.bz2", "value": {"build": "py310hbf28c38_2", "build_number": 2, "depends": ["libgcc-ng >=10.3.0", "libstdcxx-ng >=10.3.0", "numpy", "python >=3.10,<3.11.0a0", "python_abi 3.10.* *_cp310"], "license": "ISC AND BSD-3-Clause", "md5": "93fc1b1a1e34d2b21fa2136d06aa6c89", "name": "mapbox_earcut", "sha256": "acaca6408c049b0575666614aa9a50f628f345a0b3b7d36ace8d55b2f005ff4d", "size": 80917, "subdir": "linux-64", "timestamp": 1650989008805, "version": "1.0.0"}}, {"op": "add", "path": "/packages/poco-1.11.2-h08a2579_0.tar.bz2", "value": {"build": "h08a2579_0", "build_number": 0, "depends": ["libgcc-ng >=10.3.0", "libstdcxx-ng >=10.3.0", "openssl >=3.0.2,<4.0a0", "unixodbc >=2.3.9,<2.4.0a0"], "license": "BSL-1.0", "license_family": "OTHER", "md5": "e1a33760d40c42bb21f10ebbf79fbd24", "name": "poco", "sha256": "6525ab8d6089481938e298dc50f8ca79dbd39ad3e616cbbd3daa9a9fb2cec295", "size": 5332156, "subdir": "linux-64", "timestamp": 1650989286660, "version": "1.11.2"}}, {"op": "add", "path": "/packages/poppler-qt-22.04.0-hf358c63_0.tar.bz2", "value": {"build": "hf358c63_0", "build_number": 0, "depends": ["cairo >=1.16.0,<1.17.0a0", "fontconfig >=2.13.96,<3.0a0", "fonts-conda-ecosystem", "freetype >=2.10.4,<3.0a0", "gettext >=0.19.8.1,<1.0a0", "jpeg >=9e,<10a", "lcms2 >=2.12,<3.0a0", "libcurl >=7.82.0,<8.0a0", "libgcc-ng >=10.3.0", "libglib >=2.70.2,<3.0a0", "libiconv >=1.16,<1.17.0a0", "libpng >=1.6.37,<1.7.0a0", "libstdcxx-ng >=10.3.0", "libtiff >=4.3.0,<5.0a0", "libzlib >=1.2.11,<1.3.0a0", "nss >=3.77,<4.0a0", "openjpeg >=2.4.0,<2.5.0a0", "poppler 22.04.0 h1434ded_0", "qt >=5.12.9,<5.13.0a0"], "license": "GPL-2.0-only", "license_family": "GPL", "md5": "33b3a474e4ecc5ab4e21c2f7912caf3d", "name": "poppler-qt", "sha256": "aa2c23a362c13837edf0763c77c98c97a3412640339924fa17c24f577d63b0ec", "size": 5553975, "subdir": "linux-64", "timestamp": 1650986746308, "version": "22.04.0"}}]}
{"url": "https://conda.anaconda.org/conda-forge/linux-64/repodata.json", "latest": "ea8a695e21baa8090691656bbe4a4d2240ee62cdc2539dc5940077ccf2a44efc"}
716c483577e3a3f99a47db5a395f41598c5c5af6b7beaf95601ec8308f4d263d
```

When downloading new patches, a client might log the request and applied patches:

```
206 1517572 https://repodata.fly.dev/conda.anaconda.org/conda-forge/linux-64/repodata.jlap {'accept-ranges': 'bytes', 'content-encoding': 'gzip', 'content-range': 'bytes 2978004-4495575/4495576', 'content-type': 'text/plain; charset=utf-8', 'last-modified': 'Tue, 26 Apr 2022 18:15:13 GMT', 'date': 'Wed, 27 Apr 2022 00:23:05 GMT', 'transfer-encoding': 'chunked'}
Append 2978004-4495576 (135 lines)
Was 2978219, now 4495576 bytes, delta 1517357

Apply 134 patches 0aa315a3c31dd468… → 0575ec9555ea4f05…
0aa315a3c31dd468… → bf2456c2e8ff30d5…, 31 steps
…
bf2456c2e8ff30d5… → fda691c5ff4e265b…, 34 steps
fda691c5ff4e265b… → ea8a695e21baa809…, 9 steps
Patch 2.97s
Serialize 1.36s
```

## Summary

The proposed system saves bandwith when a locally-cached `repodata.json` is
known by the patch server, with a concise client implementation. After the first
update, subsequent updates fetch only the newest information using a single
round trip to the server.

## Alternatives

JSON Merge Patch is simpler but does not allow the `null` values occasionally
used in `repodata.json`.

Textual diff + patch would work, but `conda` needs the data and not the
formatting.

`zchunk` is a compression format used in Fedora, implemented in C. It splits
files into independently compressed chunks, transferring changed chunks on
update. It is generic on bytes. The server does not have to keep a history of
older versions. The web server should support multipart Range requests. (Not
true of s3, but probably OK for CDN.)

## JSON Lines With Leading and Trailing Checksums

The `.jlap` format allows clients to fetch the newest patches with a single HTTP
Range request. It consists of a leading checksum, any number of `"patch"` lines, and
a `"metadata"` line as the line-delimited [JSON
Lines](https://jsonlines.readthedocs.io/en/latest/) format, and a trailing
checksum.

The checksums are constructed in such a way that the trailing checksum can be
re-verified without re-reading (or retaining) the beginning of the file, if the
client remembers an intermediate checksum.

When `repodata.json` changes, the server wil truncate the next-to-last
`"metadata"` line, appending new patches, a new metadata line, and a new
trailing checksum.

When the client wants new data, it issues a single HTTP Range request from the
bytes offset of the beginning of the penultimate `"metadata"` line, to the end
of the file (`Range: bytes=<offset>-`), and re-verifies the trailing checksum.
If the trailing checksum does not match the computed checksum, then it must
re-fetch the entire file; otherwise, it may apply the new patches.

If the `.jlap` file represents part of a stream (earlier lines have been
discarded), then the leading checksum is an intermediate checksum from that
stream. Otherwise, the leading checksum is all `0`'s.

### Payload

Conda will expect a `.jlap` file to contain 0 or more patch objects followed by
a single metadata object.

Patch objects give the difference between two versions of `repodata.json` or
`current_repodata.json`, identified by a `BLAKE2-256` digest.

```python
current_digest = hashlib.blake2b(current_repodata_bytes, digest_size=32).digest()
previous_digest = hashlib.blake2b(previous_repodata_bytes, digest_size=32).digest()

{
    "to": current_digest.hex()
    "from": previous_digest.hex(),
    "patch": [] # RFC 6902 JSON Patch
}
```

The metadata object gives the digest of the latest version, and any other
metadata, especially the `url`.

```python
{ "url": "repodata.json", "latest": latest_digest.hex() }
```

The patch generator is not smart, so the client must check that there is a path
between the local version of `repodata.json` and the `latest` digest in the
`.jlap` file. If there is none, the client falls back to downloading a complete
`repodata.json`; hashes it; and looks for its hash in a future `.jlap`.

### Computing checksums for `JLAP version 1`

This short `.jlap` file represents the end of a larger stream.

0. `ea3f3b1853071a4b1004b9f33594938b01e01cc8ca569f20897e793c35037de4`
1. `{"to": "20af8f45bf8bc15e404bea61f608881c2297bee8a8917bee1de046da985d6d89", "from": "4324630c4aa09af986e90a1c9b45556308a4ec8a46cee186dd7013cdd7a251b7", "patch": [{"op": "add", "path": "/packages/snowflake-snowpark-python-0.10.0-py38hecd8cb5_0.tar.bz2", "value": {"build": "py38hecd8cb5_0", "build_number": 0, "constrains": ["pandas >1,<1.4"], "depends": ["cloudpickle >=1.6.0,<=2.0.0", "python >=3.8,<3.9.0a0", "snowflake-connector-python >=2.7.12", "typing-extensions >=4.1.0"], "license": "Apache-2.0", "license_family": "Apache", "md5": "91fc7aac6ea0c4380a334b77455b1454", "name": "snowflake-snowpark-python", "sha256": "3cbfed969c8702673d1b281e8dd7122e2150d27f8963d1d562cd66b3308b0b31", "size": 359503, "subdir": "osx-64", "timestamp": 1663585464882, "version": "0.10.0"}}, {"op": "add", "path": "/packages.conda/snowflake-snowpark-python-0.10.0-py38hecd8cb5_0.conda", "value": {"build": "py38hecd8cb5_0", "build_number": 0, "constrains": ["pandas >1,<1.4"], "depends": ["cloudpickle >=1.6.0,<=2.0.0", "python >=3.8,<3.9.0a0", "snowflake-connector-python >=2.7.12", "typing-extensions >=4.1.0"], "license": "Apache-2.0", "license_family": "Apache", "md5": "7353a428613fa62f4c8ec9b5a1e4f16d", "name": "snowflake-snowpark-python", "sha256": "e3b5fa220262e23480d32a883b19971d1bd88df33eb90e9556e2a3cfce32b0a4", "size": 316623, "subdir": "osx-64", "timestamp": 1663585464882, "version": "0.10.0"}}]}`
2. `{"url": "repodata.json", "latest": "20af8f45bf8bc15e404bea61f608881c2297bee8a8917bee1de046da985d6d89"}`
3. `c540a2ab0ab4674dada39063205a109d26027a55bd8d7a5a5b711be03ffc3a9d`

Line `0` is called the initialization vector. It is 32 bytes encoded as a
64-character hexademical string, all lowercase.

Lines `1..2` are the payload, and line `3` is the trailing checksum.

* If the `.jlap` specification is revised, line `0` will contain a space
  `chr(32)` and a version identifier. The decoder should stop with a `Not JLAP
  1` error message.

`BLAKE2_256` is the 512-bit `BLAKE2b` hash function with 32 bytes, or 256 bits
output. It is a fast keyed hash, available in Python as `hashlib.blake2b(data,
key=key, digest_size=32)`

Given an `N`-line `.jlap` file,

Let `lines[0..N-1]` = an array of each line of the file, without the `\n`
terminators.

The checksum of `lines[0]` is

`checksum(0) = bytes.fromhex(lines[0])`

The checksum of `lines[1..N-1]` is

`checksum(n) = BLAKE2_256(lines[n], key=checksum(lines[n-1])`

The checksum is 32 binary bytes, not hexadecimal.

In Python,

```python
def BLAKE2_256(data: bytes, key: bytes) -> bytes:
    return blake2b(data, key=key, digest_size=32).digest()

def checksum(n: int) -> bytes:
    if n == 0:
        return bytes.fromhex(lines[0].decode("utf-8"))
    else:
        return BLAKE2_256(lines[n], key=checksum(n - 1))
```

The last line is the hex-encoded checksum of the next-to-last line,
`checksum(N-2).hex()`, and is used to verify the integrity of the file. The last
line must not end with `\n`.

```python
if bytes(checksum(N - 2)).hex() == lines[N - 1].decode("utf-8"):
    valid = True
else:
    raise ValueError(
        "Invalid", bytes(checksum(N - 2)).hex(), lines[N - 1].decode("utf-8")
    )
```

## Reference

* JSON Patch https://datatracker.ietf.org/doc/html/rfc6902
* Server and client implementation in Python https://github.com/dholth/repodata-fly

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
