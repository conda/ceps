New history format
------------------

The history file in conda / mamba follows a weird, non specified format.
It currently looks like:

```
==> 2021-11-29 11:06:19 <==
# cmd: mamba
# conda version: 3.8.0
+https://conda.anaconda.org/conda-forge/osx-arm64::libcxx-12.0.1-h168391b_0
+https://conda.anaconda.org/conda-forge/osx-arm64::xtl-0.7.4-hc021e02_0
+https://conda.anaconda.org/conda-forge/osx-arm64::xtensor-0.24.0-hc021e02_0
# update specs: ["xtensor"]
# neutered specs: []
# remove specs: []
```

We should move to a well specified format based on JSON.

I propose:

```json
[
    {
       "cmd": "mamba",
       "conda_version": "3.8.0",
       "timestamp": "2030-01-01T00:00:00Z", // same timestamp format as used in TUF metadata in UTC
       "packages": {
           "added": [
            "https://conda.anaconda.org/conda-forge/osx-arm64::libcxx-12.0.1-h168391b_0",
            "https://conda.anaconda.org/conda-forge/osx-arm64::xtl-0.7.4-hc021e02_0",
            "https://conda.anaconda.org/conda-forge/osx-arm64::xtensor-0.24.0-hc021e02_0"
            ],
            "removed": []
       }
       "specs": {
           "updated": ["xtensor"],
           "neutered": [],
           "removed": []
       }
    },
    ...
]
```
