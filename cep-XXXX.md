# CEP XXXX - Build provenance metadata

<table>
<tr><td> Title </td><td> CEP XXXX - Build provenance metadata </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Jaime Rodríguez-Guerra &lt;jaime.rogue@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> Mar 10, 2025</td></tr>
<tr><td> Updated </td><td> Mar 11, 2025</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/113 </td></tr>
<tr><td> Implementation </td><td> https://github.com/conda/conda-build/pull/4303, https://github.com/conda-forge/conda-smithy/pull/1577 </td></tr>
</table>

## Abstract

This CEP aims to standardize how the conda ecosystem leverages free-form recipe metadata to
annotate build provenance of its published artifacts.

## Motivation

Provenance metadata is useful to assess how and when a conda artifact was built.

Since late 2023, thanks to conda-smithy 3.28.0 and later, conda-forge feedstocks have been adding
CI provenance in the produced artifacts. `defaults` also applies the same conventions. This is used
by apps like `conda-metadata-app` to show provenance information in the build details. See the
table in this [Python 3.13
example](https://conda-metadata-app.streamlit.app/?q=conda-forge%2Flinux-64%2Fpython-3.13.2-hf636f53_101_cp313.conda).

This was possible thanks to a new `--extra-meta` flag added in
[conda-build#4303](https://github.com/conda/conda-build/pull/4303/files) and released in 3.21.8.
Rattler-build also offers the same functionality using the same CLI flag. `--extra-meta` allows
passing arbitrary key-value pairs that will be added to the `info/about.json`, under the `extra`
key (as defined in [CEP PR#133](https://github.com/conda/ceps/pull/133)). For example, if a user
passes `--extra-meta date=2025-03-11`, `about.json` will contain:

```js
{
    // ...
    "extra": {
        "date": "2025-03-11"
    },
    // ...
}
```

Additional provenance metadata can be collected for source origins, which can be useful for efforts
like dependency mapping across ecosystems. See [PEP 725](https://peps.python.org/pep-0725/) for
practical applications in the context of PyPI/conda interoperability. This type of provenance is
out of scope for this CEP and may be discussed separately.

## Specification

Build provenance metadata is optional. If necessary, the following metadata keys MAY be used to
record the corresponding information:

- `sha`: String. Full commit hash of the recipe repository being built.
- `remote_url`: String. CVS URL of the recipe repository being built. HTTP(S) preferred.
- `flow_run_id`: String. CI-specific identifier for the workflow run.

For example, ``conda-forge/linux-64::python-3.13.2-hf636f53_101_cp313.conda` has the following
provenance metadata:

```json
{
    "sha": "50a4e2d4203f05082fcbb93e14541180de3aa8ac",
    "remote_url": "https://github.com/conda-forge/python-feedstock",
    "flow_run_id": "azure_20250217.3.1"
}
```

CI pipelines are strongly encouraged to add this metadata via `--extra-meta` (or equivalent). Local
workflows may not have this information available, but they are still recommended to burn in the
metadata with empty strings.

## Acknowledgements

These efforts were spearheaded by Connor Martin and Daniel Bast at Anaconda, and Isuru Fernando at
conda-forge.

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
