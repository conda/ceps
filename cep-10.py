from hashlib import blake2b

lines = [
    b"ea3f3b1853071a4b1004b9f33594938b01e01cc8ca569f20897e793c35037de4",
    b'{"to": "20af8f45bf8bc15e404bea61f608881c2297bee8a8917bee1de046da985d6d89", "'
    b'from": "4324630c4aa09af986e90a1c9b45556308a4ec8a46cee186dd7013cdd7a251b7", "'
    b'patch": [{"op": "add", "path": "/packages/snowflake-snowpark-python-0.10.0-p'
    b'y38hecd8cb5_0.tar.bz2", "value": {"build": "py38hecd8cb5_0", "build_number":'
    b' 0, "constrains": ["pandas >1,<1.4"], "depends": ["cloudpickle >=1.6.0,<=2.0'
    b'.0", "python >=3.8,<3.9.0a0", "snowflake-connector-python >=2.7.12", "typing'
    b'-extensions >=4.1.0"], "license": "Apache-2.0", "license_family": "Apache", '
    b'"md5": "91fc7aac6ea0c4380a334b77455b1454", "name": "snowflake-snowpark-pytho'
    b'n", "sha256": "3cbfed969c8702673d1b281e8dd7122e2150d27f8963d1d562cd66b3308b0'
    b'b31", "size": 359503, "subdir": "osx-64", "timestamp": 1663585464882, "versi'
    b'on": "0.10.0"}}, {"op": "add", "path": "/packages.conda/snowflake-snowpark-p'
    b'ython-0.10.0-py38hecd8cb5_0.conda", "value": {"build": "py38hecd8cb5_0", "bu'
    b'ild_number": 0, "constrains": ["pandas >1,<1.4"], "depends": ["cloudpickle >'
    b'=1.6.0,<=2.0.0", "python >=3.8,<3.9.0a0", "snowflake-connector-python >=2.7.'
    b'12", "typing-extensions >=4.1.0"], "license": "Apache-2.0", "license_family"'
    b': "Apache", "md5": "7353a428613fa62f4c8ec9b5a1e4f16d", "name": "snowflake-sn'
    b'owpark-python", "sha256": "e3b5fa220262e23480d32a883b19971d1bd88df33eb90e955'
    b'6e2a3cfce32b0a4", "size": 316623, "subdir": "osx-64", "timestamp": 166358546'
    b'4882, "version": "0.10.0"}}]}',
    b'{"url": "repodata.json", "latest": "20af8f45bf8bc15e404bea61f608881c2297bee8'
    b'a8917bee1de046da985d6d89"}',
    b"c540a2ab0ab4674dada39063205a109d26027a55bd8d7a5a5b711be03ffc3a9d",
]

N = len(lines)


def BLAKE2_256(data: bytes, key: bytes) -> bytes:
    return blake2b(data, key=key, digest_size=32).digest()


def checksum(n: int) -> bytes:
    if n == 0:
        return bytes.fromhex(lines[0].decode("utf-8"))
    else:
        return BLAKE2_256(lines[n], key=checksum(n - 1))


# The last line is the hex-encoded checksum of the next-to-last line,
# `checksum(N-2).hex()`, and is used to verify the integrity of the file. The last
# line must not end with `\n`.

if bytes(checksum(N - 2)).hex() == lines[N - 1].decode("utf-8"):
    valid = True
else:
    raise ValueError(
        "Invalid", bytes(checksum(N - 2)).hex(), lines[N - 1].decode("utf-8")
    )
