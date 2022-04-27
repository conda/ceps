<table>
<tr><td> Title </td><td> JSON Patch Incremental Updates for repodata.json </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Daniel Holth &lt;dholth@gmail.com | dholth@anaconda.com&gt;</td></tr>
<tr><td> Created </td><td> Mar 30, 2022</td></tr>
<tr><td> Updated </td><td> Apr 26, 2022</td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> https://github.com/dholth/repodata-fly </td></tr>
</table>

## Abstract

`conda install` and other conda commands must download the entire per-channel
`repodata.json`, a file listing all available packages, if it has changed, but a
typical `repodata.json` update only adds a fraction of the total number of
packages. If conda could download just the changes it would save bandwidth and
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
bytes={offset of start of local metadata line}-` until the end of the remote
file.

The checksum is constructed so that by saving an intermediate checksum, the
client can verify new patches even if it has discarded earlier, consumed
patches. If the trailing checksum does not match the local computed checksum,
then the file was corrupted or the server has begun a new patch series;
re-download the remote `.jlap` from the beginning.

`repodata.json` versions are identified by a hash of their verbatim contents.
Each patch is accompanied by a hash `from` an older version of the file, and a
hash `to` of a newer version of the file.

To apply patches, take the `BLAKE2(256)` hash of the most recent complete
`repodata.json`. Follow the list of patches in `repodata.jlap` from the first
one whose `to` matches `latest`, to the next one whose `to` matches the more
recent `from` and so on, pushing these onto a stack until a patch is found whose
`from` hash matches the local `repodata.json`. If the desired `from` hash is
found, pop each patch off the stack, applying them in turn to the outdated
`repodata.json`. The result is logically equal to the latest `repodata.json`.

Since JSON Patch does not preserve formatting, the new `repodata.json` will not
hash equal to `latest` unless it is sorted and re-serialized, with the
`json.dump(...)` settings used in `conda-build index`. Otherwise it should be
considered to have the `latest` hash for purposes of incremental updates.

If the desired hash is not found in the `repodata.jlap` patch set, download the
complete `repodata.json` as before.

An example of a patche against conda-forge `repodata.json`, adding packages to
this ~170MB (23MB compressed) file:

```
0000000000000000000000000000000000000000000000000000000000000000
... additional lines ...
{"to": "ea8a695e21baa8090691656bbe4a4d2240ee62cdc2539dc5940077ccf2a44efc", "from": "fda691c5ff4e265b580b0dc43cbb0bd95af9920a10bacf621b51e5cfd72baa03", "patch": [{"op": "add", "path": "/packages/mapbox_earcut-1.0.0-py310hbf28c38_2.tar.bz2", "value": {"build": "py310hbf28c38_2", "build_number": 2, "depends": ["libgcc-ng >=10.3.0", "libstdcxx-ng >=10.3.0", "numpy", "python >=3.10,<3.11.0a0", "python_abi 3.10.* *_cp310"], "license": "ISC AND BSD-3-Clause", "md5": "93fc1b1a1e34d2b21fa2136d06aa6c89", "name": "mapbox_earcut", "sha256": "acaca6408c049b0575666614aa9a50f628f345a0b3b7d36ace8d55b2f005ff4d", "size": 80917, "subdir": "linux-64", "timestamp": 1650989008805, "version": "1.0.0"}}, {"op": "add", "path": "/packages/mapbox_earcut-1.0.0-py37h506a98e_2.tar.bz2", "value": {"build": "py37h506a98e_2", "build_number": 2, "depends": ["libgcc-ng >=10.3.0", "libstdcxx-ng >=10.3.0", "numpy", "pypy3.7 >=7.3.7", "python >=3.7,<3.8.0a0", "python_abi 3.7 *_pypy37_pp73"], "license": "ISC AND BSD-3-Clause", "md5": "b486d2bf0b9cb6f9fc9caf29aced70cf", "name": "mapbox_earcut", "sha256": "50242c2aff0fa007135e18b32c540b57460c53ca225f3ee182c13d1e13c7ed09", "size": 80007, "subdir": "linux-64", "timestamp": 1650988961306, "version": "1.0.0"}}, {"op": "add", "path": "/packages/mapbox_earcut-1.0.0-py37h7cecad7_2.tar.bz2", "value": {"build": "py37h7cecad7_2", "build_number": 2, "depends": ["libgcc-ng >=10.3.0", "libstdcxx-ng >=10.3.0", "numpy", "python >=3.7,<3.8.0a0", "python_abi 3.7.* *_cp37m"], "license": "ISC AND BSD-3-Clause", "md5": "a6227836fd9dc731a61ac0ed57589790", "name": "mapbox_earcut", "sha256": "050b3d269a0964c8bd814b2bdcf9f5c523225c3f602a18e4c04e1049438d4826", "size": 79206, "subdir": "linux-64", "timestamp": 1650988985131, "version": "1.0.0"}}, {"op": "add", "path": "/packages/mapbox_earcut-1.0.0-py38h43d8883_2.tar.bz2", "value": {"build": "py38h43d8883_2", "build_number": 2, "depends": ["libgcc-ng >=10.3.0", "libstdcxx-ng >=10.3.0", "numpy", "python >=3.8,<3.9.0a0", "python_abi 3.8.* *_cp38"], "license": "ISC AND BSD-3-Clause", "md5": "26ff06f1842618cd17ab7c99dc7a8a95", "name": "mapbox_earcut", "sha256": "d5e81828bf1cdc6e2105362cf867cb217d7fa38519628936d1a254b0be154bfc", "size": 80431, "subdir": "linux-64", "timestamp": 1650988985479, "version": "1.0.0"}}, {"op": "add", "path": "/packages/mapbox_earcut-1.0.0-py39hf939315_2.tar.bz2", "value": {"build": "py39hf939315_2", "build_number": 2, "depends": ["libgcc-ng >=10.3.0", "libstdcxx-ng >=10.3.0", "numpy", "python >=3.9,<3.10.0a0", "python_abi 3.9.* *_cp39"], "license": "ISC AND BSD-3-Clause", "md5": "4770c3dfb3b34f390e57d1fa3cf208f3", "name": "mapbox_earcut", "sha256": "6941e8d18d283b35e84596014c7ef8bca317ec320ae765eded8ad67fe9d9d0c7", "size": 80689, "subdir": "linux-64", "timestamp": 1650989007616, "version": "1.0.0"}}, {"op": "add", "path": "/packages/poco-1.11.2-h08a2579_0.tar.bz2", "value": {"build": "h08a2579_0", "build_number": 0, "depends": ["libgcc-ng >=10.3.0", "libstdcxx-ng >=10.3.0", "openssl >=3.0.2,<4.0a0", "unixodbc >=2.3.9,<2.4.0a0"], "license": "BSL-1.0", "license_family": "OTHER", "md5": "e1a33760d40c42bb21f10ebbf79fbd24", "name": "poco", "sha256": "6525ab8d6089481938e298dc50f8ca79dbd39ad3e616cbbd3daa9a9fb2cec295", "size": 5332156, "subdir": "linux-64", "timestamp": 1650989286660, "version": "1.11.2"}}, {"op": "add", "path": "/packages/poco-1.11.2-h3790be6_0.tar.bz2", "value": {"build": "h3790be6_0", "build_number": 0, "depends": ["libgcc-ng >=10.3.0", "libstdcxx-ng >=10.3.0", "openssl >=1.1.1n,<1.1.2a", "unixodbc >=2.3.9,<2.4.0a0"], "license": "BSL-1.0", "license_family": "OTHER", "md5": "5af5066afe0a90be9a2f95d92f3b225e", "name": "poco", "sha256": "bc86251c0a0f86146423996b8b8db30358a61d7f911c2322fe70ca2df7d752a8", "size": 5225400, "subdir": "linux-64", "timestamp": 1650989278591, "version": "1.11.2"}}, {"op": "add", "path": "/packages/poppler-22.04.0-h1434ded_0.tar.bz2", "value": {"build": "h1434ded_0", "build_number": 0, "depends": ["boost-cpp >=1.74.0,<1.74.1.0a0", "cairo >=1.16.0,<1.17.0a0", "fontconfig >=2.13.96,<3.0a0", "fonts-conda-ecosystem", "freetype >=2.10.4,<3.0a0", "gettext >=0.19.8.1,<1.0a0", "jpeg >=9e,<10a", "lcms2 >=2.12,<3.0a0", "libcurl >=7.82.0,<8.0a0", "libgcc-ng >=10.3.0", "libglib >=2.70.2,<3.0a0", "libiconv >=1.16,<1.17.0a0", "libpng >=1.6.37,<1.7.0a0", "libstdcxx-ng >=10.3.0", "libtiff >=4.3.0,<5.0a0", "libzlib >=1.2.11,<1.3.0a0", "nss >=3.77,<4.0a0", "openjpeg >=2.4.0,<2.5.0a0", "poppler-data"], "license": "GPL-2.0-only", "license_family": "GPL", "md5": "864687071a99df6f24dd587b77e4c753", "name": "poppler", "sha256": "53593388bb16933c2c711d0fb8e46b6cf6f429acb19a204b6e1cd6eaf1646288", "size": 20191738, "subdir": "linux-64", "timestamp": 1650986618544, "version": "22.04.0"}}, {"op": "add", "path": "/packages/poppler-qt-22.04.0-hf358c63_0.tar.bz2", "value": {"build": "hf358c63_0", "build_number": 0, "depends": ["cairo >=1.16.0,<1.17.0a0", "fontconfig >=2.13.96,<3.0a0", "fonts-conda-ecosystem", "freetype >=2.10.4,<3.0a0", "gettext >=0.19.8.1,<1.0a0", "jpeg >=9e,<10a", "lcms2 >=2.12,<3.0a0", "libcurl >=7.82.0,<8.0a0", "libgcc-ng >=10.3.0", "libglib >=2.70.2,<3.0a0", "libiconv >=1.16,<1.17.0a0", "libpng >=1.6.37,<1.7.0a0", "libstdcxx-ng >=10.3.0", "libtiff >=4.3.0,<5.0a0", "libzlib >=1.2.11,<1.3.0a0", "nss >=3.77,<4.0a0", "openjpeg >=2.4.0,<2.5.0a0", "poppler 22.04.0 h1434ded_0", "qt >=5.12.9,<5.13.0a0"], "license": "GPL-2.0-only", "license_family": "GPL", "md5": "33b3a474e4ecc5ab4e21c2f7912caf3d", "name": "poppler-qt", "sha256": "aa2c23a362c13837edf0763c77c98c97a3412640339924fa17c24f577d63b0ec", "size": 5553975, "subdir": "linux-64", "timestamp": 1650986746308, "version": "22.04.0"}}]}
{"url": "https://conda.anaconda.org/conda-forge/linux-64/repodata.json", "latest": "ea8a695e21baa8090691656bbe4a4d2240ee62cdc2539dc5940077ccf2a44efc", "headers": {"date": "Tue, 26 Apr 2022 18:14:12 GMT", "content-type": "application/json", "transfer-encoding": "chunked", "connection": "keep-alive", "cf-ray": "70214bf9bd722293-MIA", "age": "670", "cache-control": "public, max-age=1200", "etag": "W/\"30e1be6bf1b73889a41eaa4846a59c56-23\"", "expires": "Tue, 26 Apr 2022 18:34:12 GMT", "last-modified": "Tue, 26 Apr 2022 17:38:23 GMT", "vary": "Accept-Encoding", "cf-cache-status": "HIT", "expect-ct": "max-age=604800, report-uri=\"https://report-uri.cloudflare.com/cdn-cgi/beacon/expect-ct\"", "x-amz-id-2": "G2rn+4SD+sHXNxisSHtEbxHLulnvMh/Bj+KotOHzI0zxZDval2V8My839uHEfIC7LjtQRcnTOFA=", "x-amz-request-id": "7X74ZXZB2DMZA92F", "x-amz-version-id": "null", "set-cookie": "__cf_bm=.XMuRKJKwivDP9dELOOpA8NcS__lncLVi06qA6hKELM-1650996852-0-AaceO99Yc9N2lSPDz67hzvxp+BIrIYJE9Wj7HrfdzxL1xiTCx3fG6Cj/d0kODkOelFlXUp+eRnJ0uZE/oLxFysUZVVIu4GUx7gtisLdg5L6i; path=/; expires=Tue, 26-Apr-22 18:44:12 GMT; domain=.anaconda.org; HttpOnly; Secure; SameSite=None", "server": "cloudflare", "content-encoding": "gzip"}}
716c483577e3a3f99a47db5a395f41598c5c5af6b7beaf95601ec8308f4d263d
```

The penultimate metadata line may include response headers for its corresponding
`repodata.json`.

When downloading new patches, a local cache service logs the number of lines,
and number of bytes added, which is greater than the `Content-Encoding: gzip`
compressed bytes transferred. (Ideally the feature would be integrated into
`conda` itself instead of going through a local cache server):

```
206 1517572 https://repodata.fly.dev/conda.anaconda.org/conda-forge/linux-64/repodata.jlap {'accept-ranges': 'bytes', 'content-encoding': 'gzip', 'content-range': 'bytes 2978004-4495575/4495576', 'content-type': 'text/plain; charset=utf-8', 'last-modified': 'Tue, 26 Apr 2022 18:15:13 GMT', 'date': 'Wed, 27 Apr 2022 00:23:05 GMT', 'transfer-encoding': 'chunked', 'server': 'Fly/f71cab89 (2022-04-21)', 'via': '1.1 fly.io', 'fly-request-id': '01G1M6CVSF3Q4MF33QSRMG7B3D-iad'}
Append 2978004-4495576 (135 lines)
Was 2978219, now 4495576 bytes, delta 1517357
serve ~/.cache/repodata-proxy/conda.anaconda.org/conda-forge/linux-64/repodata.json.gz

Apply 134 patches 0575ec9555ea4f05… → 0575ec9555ea4f05…...
0575ec9555ea4f05… → 42e4827f62bb860e…, 173 steps
42e4827f62bb860e… → 54506a213ba69d8f…, 2 steps
54506a213ba69d8f… → 9034f593d5dd3caa…, 18 steps
9034f593d5dd3caa… → fb426b29a4b18882…, 18 steps
fb426b29a4b18882… → 9d4719bfb022dec5…, 11 steps
9d4719bfb022dec5… → 396b0ff8e0a6c8a0…, 14 steps
396b0ff8e0a6c8a0… → 933f40502fa87598…, 22 steps
933f40502fa87598… → 03aa13dfb2e69f7f…, 9 steps
03aa13dfb2e69f7f… → 1fd674e2666585ba…, 12 steps
1fd674e2666585ba… → 5ceb1bbb9700272c…, 18 steps
5ceb1bbb9700272c… → 22b8c95946cf098c…, 40 steps
22b8c95946cf098c… → adc704b5e99ab8cf…, 18 steps
adc704b5e99ab8cf… → a79fcabe46f8cf8c…, 53 steps
a79fcabe46f8cf8c… → edf2bbb96fc1de53…, 20 steps
edf2bbb96fc1de53… → eb0da850bfa0922f…, 27 steps
eb0da850bfa0922f… → b30d39864df4f4bf…, 33 steps
b30d39864df4f4bf… → c0a4d62361418e42…, 16 steps
c0a4d62361418e42… → 3dd8a149c488783a…, 10 steps
3dd8a149c488783a… → a63272f0907b813a…, 5 steps
a63272f0907b813a… → c411aba3530ad690…, 3 steps
c411aba3530ad690… → 8018db73655b0e49…, 25 steps
8018db73655b0e49… → 9f5f144120f6e6a2…, 18 steps
9f5f144120f6e6a2… → 0b31e588bc71cb91…, 20 steps
0b31e588bc71cb91… → a208cb71a326c8d1…, 8 steps
a208cb71a326c8d1… → 0526b4a66f01cd6a…, 13 steps
0526b4a66f01cd6a… → 535f6b3719d42118…, 6 steps
535f6b3719d42118… → 0584fdba1dbd0d62…, 18 steps
0584fdba1dbd0d62… → 3b810fcfe2861839…, 86 steps
3b810fcfe2861839… → b3650156198376d1…, 27 steps
b3650156198376d1… → 83d0b176aa4e8f61…, 10 steps
83d0b176aa4e8f61… → b7e816bee1ee2751…, 11 steps
b7e816bee1ee2751… → 05e1957931f9324d…, 16 steps
05e1957931f9324d… → 09152173f4adda84…, 7 steps
09152173f4adda84… → 2651e6e3240c6de6…, 6 steps
2651e6e3240c6de6… → e1a5b74ecf2ef381…, 4 steps
e1a5b74ecf2ef381… → c5d3dc992933048a…, 10 steps
c5d3dc992933048a… → a75c523fe18c47d6…, 14 steps
a75c523fe18c47d6… → 2f8e1fd799839fbd…, 6 steps
2f8e1fd799839fbd… → 5c537c4942c80dea…, 19 steps
5c537c4942c80dea… → a761c49d4351c6b2…, 70 steps
a761c49d4351c6b2… → 76941d288396d557…, 6 steps
76941d288396d557… → 355bfea9a9471bef…, 27 steps
355bfea9a9471bef… → e21069167fa9f50a…, 24 steps
e21069167fa9f50a… → fb82c87c5ffba679…, 21 steps
fb82c87c5ffba679… → 9b4f3515bb72ee17…, 10 steps
9b4f3515bb72ee17… → b0a8d3bcad743ae6…, 71 steps
b0a8d3bcad743ae6… → 3e08c035739c0114…, 15 steps
3e08c035739c0114… → 01663a979148ec18…, 1 steps
01663a979148ec18… → ca1e41fd318e88b2…, 2 steps
ca1e41fd318e88b2… → 85a09642c0ecef2f…, 30 steps
85a09642c0ecef2f… → 8e378cb321c2590a…, 2 steps
8e378cb321c2590a… → 8b9e4440ecede86f…, 6 steps
8b9e4440ecede86f… → 3161eb721f1ec0cc…, 19 steps
3161eb721f1ec0cc… → e51a3591a53cff4f…, 57 steps
e51a3591a53cff4f… → 506965fa56b788d4…, 6 steps
506965fa56b788d4… → 31ad9eb06e650f53…, 1 steps
31ad9eb06e650f53… → 93c84788bb783ea2…, 8 steps
93c84788bb783ea2… → 0e4796d138e73e90…, 18 steps
0e4796d138e73e90… → f24211e5aa8d8c74…, 457 steps
f24211e5aa8d8c74… → 53d831807c49f514…, 3 steps
53d831807c49f514… → b966f8feb4a61204…, 8 steps
b966f8feb4a61204… → df46189b36643424…, 34 steps
df46189b36643424… → 76a3ad77d8dff01d…, 81 steps
76a3ad77d8dff01d… → 466fd7796323c506…, 6 steps
466fd7796323c506… → 4813dcbe2f81fc61…, 11 steps
4813dcbe2f81fc61… → 5eeb7b79d495551d…, 3 steps
5eeb7b79d495551d… → 216936c60b35694d…, 13 steps
216936c60b35694d… → 168b1d810ce79d67…, 4 steps
168b1d810ce79d67… → ce0a346652cbdc8e…, 36 steps
ce0a346652cbdc8e… → 1a904a583a756e8a…, 17 steps
1a904a583a756e8a… → 54cafc86e0bdcc10…, 15 steps
54cafc86e0bdcc10… → 4e4344450981208d…, 10 steps
4e4344450981208d… → a6f4223534e844e7…, 8 steps
a6f4223534e844e7… → 99edcbd3b12a877b…, 30 steps
99edcbd3b12a877b… → 566784db8dd57822…, 17 steps
566784db8dd57822… → f0b32b9f6c7ec435…, 13 steps
f0b32b9f6c7ec435… → d0f688ec3760c670…, 95 steps
d0f688ec3760c670… → f01c8c4908735736…, 9 steps
f01c8c4908735736… → 589ff3dbe2dec692…, 11 steps
589ff3dbe2dec692… → 33a2c47c96a8b0c5…, 9 steps
33a2c47c96a8b0c5… → 4f0498e69b933998…, 116 steps
4f0498e69b933998… → deb79c8876c6d8c0…, 29 steps
deb79c8876c6d8c0… → 848b753fcc2776b9…, 8 steps
848b753fcc2776b9… → 377895dfffe94a3e…, 2 steps
377895dfffe94a3e… → dbf79362ef190730…, 4 steps
dbf79362ef190730… → 7d25389cad44036b…, 4 steps
7d25389cad44036b… → 5ed1069fa21a7afc…, 29 steps
5ed1069fa21a7afc… → 41cbb4960533bf5c…, 5 steps
41cbb4960533bf5c… → 041170921a19624b…, 11 steps
041170921a19624b… → cb26fb08146b47d2…, 6 steps
cb26fb08146b47d2… → 37e1339f97bac34c…, 11 steps
37e1339f97bac34c… → 6c55041cefcc67b0…, 33 steps
6c55041cefcc67b0… → 052fa5b296656e9d…, 1 steps
052fa5b296656e9d… → cd12fa187cc15b6e…, 1 steps
cd12fa187cc15b6e… → b218a9437570a0f4…, 4 steps
b218a9437570a0f4… → df124f016f7dab47…, 6 steps
df124f016f7dab47… → ee8253efa0c0ffde…, 7 steps
ee8253efa0c0ffde… → dea04baca7856fbe…, 3 steps
dea04baca7856fbe… → 126550f0770b5a10…, 4 steps
126550f0770b5a10… → 2dafc141b6629932…, 1 steps
2dafc141b6629932… → 17a4e6b2e552a970…, 18 steps
17a4e6b2e552a970… → 704dce0b60477958…, 1 steps
704dce0b60477958… → b04e61a94d65d351…, 7 steps
b04e61a94d65d351… → b692a58d5e0183d7…, 7 steps
b692a58d5e0183d7… → e3450ce24b2c433c…, 1 steps
e3450ce24b2c433c… → ad284fd74bf99735…, 6 steps
ad284fd74bf99735… → 1e279bb5e0724194…, 6 steps
1e279bb5e0724194… → 694da3d73e00d235…, 19 steps
694da3d73e00d235… → 32e661bb5eecd5b6…, 18 steps
32e661bb5eecd5b6… → 2cbb5a4f1a6bd09b…, 1 steps
2cbb5a4f1a6bd09b… → 0594dbd72432f131…, 12 steps
0594dbd72432f131… → 570e1232f56f4428…, 1 steps
570e1232f56f4428… → adcc34a4f2f64540…, 6 steps
adcc34a4f2f64540… → 10013ced66dc5327…, 54 steps
10013ced66dc5327… → 5bf2dca0fb0d5e29…, 36 steps
5bf2dca0fb0d5e29… → b0d1824a2c44ebac…, 30 steps
b0d1824a2c44ebac… → e762a87e5bbd564e…, 19 steps
e762a87e5bbd564e… → 31a347c12089ec9a…, 5 steps
31a347c12089ec9a… → 2012bd26ff00f8f7…, 309 steps
2012bd26ff00f8f7… → 3d194171754c2732…, 6 steps
3d194171754c2732… → 23d7ca40b16a797c…, 36 steps
23d7ca40b16a797c… → 37e1ba4f3bd8942a…, 5 steps
37e1ba4f3bd8942a… → c9e035690378ca90…, 4 steps
c9e035690378ca90… → 8c62fec64752f733…, 5 steps
8c62fec64752f733… → 13604558bc1a5d65…, 1 steps
13604558bc1a5d65… → 8d2b5e57d1c897b7…, 1 steps
8d2b5e57d1c897b7… → 558651fbacc6e178…, 23 steps
558651fbacc6e178… → a5661fb43183b877…, 4 steps
a5661fb43183b877… → 300dc9b5cd8801d0…, 8 steps
300dc9b5cd8801d0… → cd9fbab6f5af29da…, 24 steps
cd9fbab6f5af29da… → 0aa315a3c31dd468…, 24 steps
0aa315a3c31dd468… → bf2456c2e8ff30d5…, 31 steps
bf2456c2e8ff30d5… → fda691c5ff4e265b…, 34 steps
fda691c5ff4e265b… → ea8a695e21baa809…, 9 steps
Patch 2.97s
Serialize 1.36s
```

The times are from PyPy running on an older Intel(R) Core(TM) i7-5500U laptop.

## Summary

The proposed system saves bandwith when a locally cached `repodata.json` is
known by the patch server, with a very concise client implementation. After the
first update, subsequent updates fetch only the newest information using a
single round trip to the server.

## Alternatives

JSON Merge Patch is simpler but does not allow the `null` values occasionally
used in `repodata.json`.

Textual diff + patch would work, but `conda` needs the data and not the
formatting.

`zchunk` is a compression format used in Fedora, implemented in C. It splits
files into independently compressed chunks, transferring changed chunks on
update. It is generic on bytes. The server does not have to keep a history of
older versions. The web server should support multipart Range requests, not true
of s3, probably OK for CDN.

## JSON Lines With Leading and Trailing Checksums

```
0000000000000000000000000000000000000000000000000000000000000000
{"to": "af99a2269795b91aee909eebc6b71a127f8001475c67c2345c96253b97378b21", "from": "af99a2269795b91aee909eebc6b71a127f8001475c67c2345c96253b97378b21", "patch": []}
...
{"url": "", "latest": "af99a2269795b91aee909eebc6b71a127f8001475c67c2345c96253b97378b21", "headers": {"date": "Thu, 14 Apr 2022 17:24:36 GMT", "last-modified": "Tue, 28 May 2019 02:01:41 GMT"}}
8b9c825f33cc68354f131dd810a068256e34153b7335619eeb187b51a54c7118
```

The `.jlap` format allows clients to fetch the newest patches with a single HTTP
Range request. It consists of a leading checksum, any number of lines of the
elements of the `"patches"` array and a `"metadata"` line in the [JSON
Lines](https://jsonlines.readthedocs.io/en/latest/) format, and a trailing
checksum.

The checksums are constructed in such a way that the trailing checksum can be
re-verified without re-reading (or retaining) the beginning of the file, if the
client remembers an intermediate checksum.

When `repodata.json` changes, the server wil truncate the `"metadata"` line,
appending new patches, a new metadata line and a new trailing checksum.

When the client wants new data, it issues a single HTTP Range request from the
bytes offset of the beginning of the penultimate `"metadata"` line, to the end
of the file (`Range: bytes=<offset>-`), and re-verifies the trailing checksum.
If the trailing checksum does not match the computed checksum then it must
re-fetch the entire file; otherwise, it may apply the new patches.

If the `.jlap` file represents part of a stream (earlier lines have been
discarded) then the leading checksum is an intermediate checksum from that
stream. Otherwise the leading checksum is all `0`'s.

## Reference

* JSON Patch https://datatracker.ietf.org/doc/html/rfc6902
* Server and client implementation in Python https://github.com/dholth/repodata-fly

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
