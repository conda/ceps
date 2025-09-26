<table>
<tr><td> Title </td><td> .state.json files for repodata metadata </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Wolf Vollprecht &lt;wolf@prefix.dev&gt;</td></tr>
<tr><td> Created </td><td> Jan 09, 2023</td></tr>
<tr><td> Updated </td><td> Jan 09, 2023</td></tr>
<tr><td> Discussion </td><td> https://conda.slack.com/archives/C017F7C0VM3/p1672669131100819 </td></tr>
<tr><td> Implementation </td><td> https://github.com/mamba-org/mamba/pull/2113 </td></tr>
</table>

## Abstract

Changing how conda and mamba store metadata about repodata.json downloads.

### Motivation

When conda currently downloads `repodata.json` files from the internet, it stores metadata "inside" the file by adding some JSON keys:

- `_url`: The URL that was requested
- `_etag`: ETag returned from server
- `_mod`: Last-Modified header from server
- `_cache_control`: Cache-Control header from server

These are stored as three string values.

This is not an ideal approach as it modifies the `repodata.json` file and corrupts e.g. the hash of the file. Also, the repodata files have gotten increasingly large, and parsing these state values can require parsing a large `json` file.

Therefore we propose to store the metadata in a secondary file called `.state.json` file next to the repodata.

Another motivating factor is that for the `jlap` proposal we need to (repeatedly) compute the hash value of the `repodata.json` file -- that only gives correct results straight away when the repodata is stored externally.

Both mamba and conda currently use the same cache folder. If both don't implement the same storage strategy but continue to share the same repodata cache, it would lead to frequent cache busting.

### Specification

```json5
{
    // we ensure that state.json and .json files are in sync by storing the file
    // last modified time in the state file, as well as the file size

    // seconds and nanoseconds counted from UNIX timestamp (1970-01-01)
    "mtime_ns": INTEGER,
    "size": INTEGER, // file size in bytes

    // The header values as before
    "url": STRING,
    "etag": STRING,
    "mod": STRING,
    "cache_control": STRING,

    // these are alternative encodings of the repodata.json that
    // can be used for faster downloading
    // both `has_zst` and `has_jlap` keys are optional but should be kept
    // even if the other data times out or `file_mtime` does not match
    "has_zst": {
        // UTC RFC3999 timestamp of when we last checked wether the file is available or not
        // in this case the `repodata.json.zst` file
        // Note: same format as conda TUF spec
        // Python's time.time_ns() would be convenient?
        "last_checked": "2023-01-08T11:45:44Z",
        // false = unavailable, true = available
        "value": BOOLEAN
    },
    "has_jlap": {
        // same format as `has_zst`
    },

    "jlap": { } // unspecified additional state for jlap when available
}
```

If the `state.json` file_mtime or file_size does not match the `.json` file actual `mtime`, the header values are discarded. However, the `has_zst` or `has_jlap` values are kept as they are independent from the repodata validity on disk.

If the client is tracking `repodata.json.zst` or `repodata.jlap` instead of
`(current_)?repodata.json`, then `etag`/`mod`/`cache_control` will correspond to
those remote files, instead of `repodata.json`.

### Backward compatibility

Older clients that try to reuse the existing cache will not be able to make use of the cached repodata as they do not know about the state (since it's not written to the same location). That means they will redownload the repodata.

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
