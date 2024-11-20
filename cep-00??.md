# CEP XX - Computing the hash of the contents in a directory

<table>
<tr><td> Title </td><td> Computing the hash of the contents in a directory </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Jaime Rodríguez-Guerra &lt;jaime.rogue@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> Nov 19, 2024</td></tr>
<tr><td> Updated </td><td> Nov 19, 2024</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/100 </td></tr>
<tr><td> Implementation </td><td> https://github.com/conda/conda-build/pull/5277 </td></tr>
</table>

## Abstract

Given a directory, propose an algorithm to compute the aggregated hash of its contents in a cross-platform way. This is useful to check the integrity of remote sources regardless the compression method used.

> The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT",
  "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as
  described in [RFC2119][RFC2119] when, and only when, they appear in all capitals, as shown here.

## Specification

Given a directory, recursively scan all its contents (without following symlinks) and sort them by their full path. For each entry in the contents table, compute the hash for the concatenation of:
- UTF-8 encoded bytes of the path, relative to the input directory. Backslashes MUST be normalized to forward slashes before encoding.
- Then, depending on the type:
    - For text files, the UTF-8 encoded bytes of an `F` separator, followed by the UTF-8 encoded bytes of its line-ending-normalized contents (`\r\n` replaced with `\n`). A file is considered
    a text file if all the contents can be UTF-8 decoded. Otherwise it's considered binary.
    - For binary files, the UTF-8 encoded bytes of an `F` separator, followed by the bytes of its contents.
    - For a directory, the UTF-8 encoded bytes of a `D` separator, and nothing else.
    - For a symlink, the UTF-8 encoded bytes of an `L` separator, followed by the UTF-8 encoded bytes of the path it points to. Backslashes MUST be normalized to forward slashes before encoding.
- UTF-8 encoded bytes of the string `-`.

Example implementation in Python:

```python
import hashlib
from pathlib import Path

def contents_hash(directory: str, algorithm: str) -> str:
    hasher = hashlib.new(algorithm)
    for path in sorted(Path(directory).rglob("*")):
        hasher.update(path.relative_to(directory).replace("\\", "/").encode("utf-8"))
        if path.is_symlink():
            hasher.update(b"L")
            hasher.update(str(path.readlink(path)).replace("\\", "/").encode("utf-8"))
        elif path.is_dir():
            hasher.update(b"D")
        elif path.is_file():
            hasher.update(b"F") 
            try:
                # assume it's text
                lines = []
                with open(path) as fh:
                    for line in fh:
                        lines.append(line.replace("\r\n", "\n")
                for line in lines:
                    hasher.update(line.encode("utf-8")))
            except UnicodeDecodeError:
                # file must be binary
                with open(path, "rb") as fh:
                    for chunk in iter(partial(fh.read, 8192), b""):
                        hasher.update(chunk)
        hasher.update(b"-")
    return hasher.hexdigest()
```

## Motivation

Build tools like `conda-build` and `rattler-build` need to fetch the source of the project being packaged. The integrity of the download is checked by comparing its known hash (usually SHA256) against the obtained file. If they don't match, an error is raised.

However, the hash of the compressed archive is sensitive to superfluous changes like which compression method was used, the version of the archiving tool and other details that are not concerned with the contents of the archive, which is what a build tool actually cares about.
This happens often with archives fetched live from Github repository references, for example.
It is also useful to verify the integrity of `git clone` operation on a dynamic reference like a branch name.

With this proposal, build tools could add a new family of hash checks that are more robust for content reproducibility.

## Rationale

The proposed algorithm could simply concatenate all the bytes together, once the directory contents had been sorted. Instead, it also encodes relative paths and separators to prevent [preimage attacks][preimage].

Merkle trees were not used for simplicity, since it's not necessary to update the hash often or to point out which file is responsible for the hash change.

The implementation of this algorithm as specific options in build tools is a non-goal of this CEP. That goal is deferred to further CEPs, which could simply say something like:

> The `source` section is a list of objects, with keys [...] `contents_sha256` and `contents_md5` (which implement CEP XX for SHA256 and MD5, respectively).

## References

- The original issue suggesting this idea is [`conda-build#4762`][conda-build-issue].
- The Nix ecosystem has a similar feature called [`fetchzip`][fetchzip].
- There are several [Rust crates][crates] and [Python projects][pymerkletools] implementing similar strategies using Merkle trees. Some of the details here were inspired by [`dasher`][dasher].

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

<!-- links -->

[fetchzip]: https://nixos.org/manual/nixpkgs/stable/#fetchurl
[preimage]: https://flawed.net.nz/2018/02/21/attacking-merkle-trees-with-a-second-preimage-attack/
[dasher]: https://github.com/DrSLDR/dasher#hashing-scheme
[pymerkletools]: https://github.com/Tierion/pymerkletools
[crates]: https://crates.io/search?q=content%20hash
[conda-build-issue]: https://github.com/conda/conda-build/issues/4762
