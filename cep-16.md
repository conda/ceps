# Sharded Repodata

We propose a new "repodata" format that can be sparsely fetched. That means, generally, smaller fetches (only fetch what you need) and faster updates of existing repodata (only fetch what has changed).

## Motivation

The current repodata format is a JSON file that contains all the packages in a given channel. Unfortunately, that means it grows with the number of packages in the channel. This is a problem for large channels like conda-forge, which has over 150,000+ packages. It becomes very slow to fetch, parse and update the repodata.

## Design goals

1. **Speed**: Fetching repodata MUST be very fast. Both in the hot- and cold-cache case.
2. **Easy to update**: The channel MUST be very easy to update when new packages become available.
3. **CDN friendly**: A CDN MUST be usable to cache the majority of the data. This reduces the operating cost of a channel.
4. **Support authN and authZ**: It MUST be possible to implement authentication and authorization with little extra overhead.
5. **Easy to implement**: It MUST be relatively straightforward to implement to ease the adoption in different tools.
6. **Client-side cachable**: If a user has a hot cache the user SHOULD only have to download small incremental changes. Preferably as little communication as possible with the server should be required to check freshness of the data.
7. **Bandwidth optimized**: Any data that is transferred SHOULD be as small as possible.

## Previous work

### JLAP

In a previously proposed CEP, [JLAP](https://github.com/conda-incubator/ceps/pull/20) was introduced. 
With JLAP only the changes to an initially downloaded `repodata.json` file have to be downloaded which means the user drastically saves on bandwidth which in turn makes fetching repodata much faster.

However, in practice patching the original repodata can be a very expensive operation, both in terms of memory and in terms of compute because of the shear amount of data involved.

JLAP also does not save anything with a cold cache because the initial repodata still has to be downloaded. This is often the case for CI runners.

Finally, the implementation of JLAP is quite complex which makes it hard to adopt for implementers. 

### ZSTD compression

A notable improvement is compressing the `repodata.json` with `zst` and serving that file. In practice this yields a file that is 20% smaller (20-30 Mb for large cases). Although this is still quite a big file its substantially smaller. 

However, the file still contains all repodata in the channel. This means the file needs to be redownloaded every time anyone adds a single package (even if a user doesnt need that package).

Because the file is relatively big this means that often a large `max-age` is used for caching which means it takes more time to propagate new packages through the ecosystem.

## Proposal

We propose a "sharded" repodata format. It works by splitting the repodata into multiple files (one per package name) and recursively fetching the "shards".

The shards are stored by the hash of their content (e.g. "content-addressable"). 
That means that the URL of the shard is derived from the content of the shard. This allows for efficient caching and deduplication of shards on the client. Because the files are content-addressable no round-trip to the server is required to check fressness of individual shards.

Additionally an index file stores the mapping from package name to shard hash.

Although not explicitly required the server SHOULD support HTTP/2 to reduce the overhead of doing a massive number of requests. 

### Repodata shard index

The shard index is a file that is stored under `<shard_base_url>/<subdir>/repodata_shards.msgpack.zst`. It is a zstandard compressed `msgpack` file that contains a mapping from package name to shard hash. The `<shard_base_url>` is defined in [Authentication](#authentication).

The contents look like the following (written in JSON for readability):

```js
{
  "version": 1,
  "info": {
    "base_url": "https://example.com/channel/subdir/",
    "created_at": "2022-01-01T00:00:00Z",
    "...": "other metadata"
  },
  "shards": {
    // note that the hashes are stored as binary data (hex encoding just for visualization)
    "python": b"ad2c69dfa11125300530f5b390aa0f7536d1f566a6edc8823fd72f9aa33c4910",
    "numpy": b"27ea8f80237eefcb6c587fb3764529620aefb37b9a9d3143dce5d6ba4667583d"
    "...": "other packages"
  }
}
```

The index is still updated regularly but the file does not increase in size with every package added, only when new package names are added which happens much less often.

For a large case (conda-forge linux-64) this files is 670kb at the time of writing.

We suggest serving the file with a short lived `Cache-Control` `max-age` header of 60 seconds to an hour but we leave it up to the channel administrator to set a value that works for that channel.

### Repodata shard

Individual shards are stored under the URL `<shard_base_url>/<subdir>/shards/<sha256>.msgpack.zst`. Where the `sha256` is the lower-case hex representation of the bytes from the index. It is a zstandard compressed msgpack file that contains the metadata of the package. The `<shard_base_url>` is defined in [Authentication](#authentication).

The files are content-addressable which makes them ideal to be served through a CDN. They SHOULD be served with `Cache-Control: immutable` header.

The shard contains the repodata information that would otherwise have been found in the `repodata.json` file. 
It is a dictionary that contains the following keys:

**Example (written in JSON for readability):**

```json
{
  "packages": {
    "rich-10.15.2-pyhd8ed1ab_1.tar.bz2": {
      "build": "pyhd8ed1ab_1",
      "build_number": 1,
      "depends": [
        "colorama >=0.4.0,<0.5.0",
        "commonmark >=0.9.0,<0.10.0",
        "dataclasses >=0.7,<0.9",
        "pygments >=2.6.0,<3.0.0",
        "python >=3.6.2",
        "typing_extensions >=3.7.4,<5.0.0"
      ],
      "license": "MIT",
      "license_family": "MIT",
      "md5": "2456071b5d040cba000f72ced5c72032",
      "name": "rich",
      "noarch": "python",
      "sha256": "a38347390191fd3e60b17204f2f6470a013ec8753e1c2e8c9a892683f59c3e40",
      "size": 153963,
      "subdir": "noarch",
      "timestamp": 1638891318904,
      "version": "10.15.2"
    }
  },
  "packages.conda": {
    "rich-13.7.1-pyhd8ed1ab_0.conda": {
      "build": "pyhd8ed1ab_0",
      "build_number": 0,
      "depends": [
        "markdown-it-py >=2.2.0",
        "pygments >=2.13.0,<3.0.0",
        "python >=3.7.0",
        "typing_extensions >=4.0.0,<5.0.0"
      ],
      "license": "MIT",
      "license_family": "MIT",
      "md5": "ba445bf767ae6f0d959ff2b40c20912b",
      "name": "rich",
      "noarch": "python",
      "sha256": "2b26d58aa59e46f933c3126367348651b0dab6e0bf88014e857415bb184a4667",
      "size": 184347,
      "subdir": "noarch",
      "timestamp": 1709150578093,
      "version": "13.7.1"
    }
  }
}
```

The `sha256` and `md5` from the original repodata fields are converted from their hex representation to bytes. 
This is done to reduce the overall file size of the shards.

Although these files can become relatively large (100s of kilobytes) typically for a large case (conda-forge) these files remaing very small, e.g. 100s of bytes to a couple of kilobytes.

## <a id="authentication"></a>Authentication

To faciliate authentication and authorization we propose to add an additional endpoint at `<channel>/<subdir>/token` with the following content:

```json
{
    "shard_base_url": "https://shards.prefix.dev/conda-forge/<subdir>/",
    "token": "<bearer token>",
    "issued_at": "2024-01-30T03:35:39.896023447Z",
    "expires_in": 300,
}
```

`shard_base_url` is an optional url to use as the base url for the `repodata_shards.msgpack.zst` and the individual shards. If the field is not specified it should default to `<channel>/<subdir>`.

`token` is an optional field that if set MUST be added to any subsequent request in the `Authentication` header as `Authentication: Bearer <token>`. If the `token` field is not set sending the `Authentication` header is also not required. 

The optional `issued_at` and `expires_in` fields can be used to verify the freshness of a token. If the fields are not present a client can assume that the token is valid for any subsequent request.

For a simple implementor this endpoint could just be a static file with `{}` as the content.

## Fetch process

To fetch all needed package records, the client should implement the following steps:

1. Acquire a token (see: [Authentication](#authentication)). Acquiring a token can be done lazily as to only request a token when an actual network request is performed.
2. Fetch the `repodata_shards.msgpack.zst` file. Standard HTTP caching semantics can be applied to this file.
3. For each package name, start fetching the corresponding hashes from the index file (for both arch & and noarch). 
    Shards can be cached locally and because they are content-addressable no additional round-trips to the server are required to check freshness. The server should also mark these with an `immutable` `Cache-Control` header.
4. Parsing the requirements of the fetched records and add the package names of the requirements to the set of packages to fetch.
5. Loop back to 2. until there are no new package names to fetch.

## Garbage collection

To avoid the cache from growing indefinitely, we propose to implement a garbage collection mechanism that removes shards that have no entry in the index file. The server should keep old shards for a certain amount of time (e.g. 1 week) to allow for clients with older shard-index data to fetch the previous versions.

On the client side, a garbage collection process should run every so often to remove old shards from the cache. This can be done by comparing the cached shards with the index file and removing those that are not referenced anymore.


## Rejected ideas

### SHA hash compression

SHA hashes are non-compressable because in the eyes of the compressor it is just random data. We have investigated using a binary prefix tree to enable better compression but this increased the complexity of the implementation quite a bit which conflicts with our goal of keeping things simple.

### Shorter SHA hashes

Another approach would be to only store the first 100 bytes or so of the SHA hash. This reduces the total size of the sha hashes significantly but it makes the client side implementation more complex because hash conflicts become an issue. 

This also makes a future implementation based on a OCI registry harder because layers in an OCI registry are also referenced by SHA256 hash.

### Storing the data as a struct of arrays

To improve compression we investigated storing the index file as a struct of arrays instead of as an array of structs:

```json
[
 {
  "name": "",
  "hash": "",
 },
 {
  "name": "",
  "hash": "",
 } 
]
```

vs

```json
{
  "names": [...],
  "hashes": [...]
}
```

This did yield slightly better compression but we felt it makes it slightly harder to implement and adapt in the future which we deemed not worth the small size decrease.

## Future improvements

### Remove redundant keys

`platform` and `arch` can be removed because these can be inferred from `subdir`.

### Integrating additional data

With the total size of the repodata reduced it becomes feasible to add additional fields directly to the repodata records. Examples are:

- add `purl` as a list of strings (Package URLs to reference to original source of the package) (See: https://github.com/conda-incubator/ceps/pull/63)
- add `run_exports` as a list of strings (run-exports needed to build the package) (See: https://github.com/conda-incubator/ceps/pull/51)

### Update optimization

We could implement support for smaller index update files. This can be done by creating a rolling daily and weekly index update file that can be used instead of fetching the whole `repodata_shards.msgpack.zst` file. The update operation is very simple (just update the hashmap with the new entries).

For this we propose to add the following two files:

- `<channel>/<subdir>/repodata_shards_daily.msgpack.zst`
- `<channel>/<subdir>/repodata_shards_weekly.msgpack.zst`

They will contain the same format as the `repodata_shards.msgpack.zst` file but only contain the packages that have been updated in the last day or week respectively. The `created_at` field in the index file can be used to determine which file to fetch to make sure that the client has the latest information.

### Store `set(dependencies)` at the start of the shards or in a header

To reduce the time it takes to parse a shard and start fetching its dependencies we could also store the set of all dependencies in the file at the start of the shard or in a separate header. This could enable fetching recursive dependencies while still parsing the records.
