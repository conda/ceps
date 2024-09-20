<table>
<tr><td> Title </td><td> Define a vendor-neutral channel registry</td>
<tr><td> Status </td><td> Discussion</td></tr>
<tr><td> Author(s) </td><td> Wolf Vollprecht</td></tr>
<tr><td> Created </td><td> Sep 20, 2024</td></tr>
<tr><td> Updated </td><td> Sep 20, 2024</td></tr>
<!-- <tr><td> Discussion </td><td> <a href="https://github.com/conda-incubator/ceps/pull/8" target="_blank">conda-incubator/ceps#8</a> </td></tr> -->
<!-- <tr><td> Implementation </td><td> <a href="https://github.com/conda/menuinst/tree/cep-devel" target="_blank"><code>conda/menuinst</code>@<code>cep-devel</code></a> </td></tr> -->
</table>

# Conda Enhancement Proposal: Vendor-Independent Channel Registry

## Problem Statement

Currently, conda channels are typically tied to specific vendors or platforms, leading to potential vendor lock-in and limiting the flexibility of the conda ecosystem. This situation can create challenges for users and organizations who want to switch between different mirrors or providers.

Additionally it is currently impossible to attach certain metadata to channels, such as inter-channel dependencies, license (Terms of Service) information and other metadata.

The proposal would thus also help to:

- Understand the dependencies between channels
- Easily access metadata about channels (license, homepage, etc.)
- Ensure the authenticity and integrity of channel content by adding trust roots

### Proposed Solution

We propose creating a community-maintained channel registry hosted on a platform such as GitHub. This registry will serve as a centralized resource that maps _channel names_ to their associated information.

The registry will be hand-curated by trusted users who wish to have a channel-name resolve to a specific set of mirrors. Commits will _have_ to be signed.

## Key Benefits

- Reduced Vendor Lock-in: Users can easily switch between different mirrors or providers for a given channel.
- Increased Transparency: Channel metadata, including license information and dependencies, will be readily available.
- Enhanced Security: Inclusion of cryptographic trust roots enables better verification of channel content.
- Improved Discoverability: A centralized registry makes it easier for users to find and compare available channels.
- Community-Driven: Hosting on GitHub allows for community contributions and maintenance.

## Implementation Details

The registry will be implemented as a JSON file in a public GitHub repository. It will include the following information for each channel:

- List of mirrors
- Cryptographic trust root for The Update Framework (TUF)
- License information
- Description
- Channel dependencies, that link a given channel to other channels
- Homepage and GitHub URL, Logo, etc.
- Wether the channel is commercial, and where the Terms of Service are located

The JSON file would look like the following:

```js
{
  "channels": {
    "conda-forge": {
      "mirrors": [
        "https://conda.anaconda.org/conda-forge",
        "oci://ghcr.io/channel-mirrors/conda-forge",
        "https://prefix.dev/conda-forge",
        "https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge"
      ],
      "trust_root": "sha256:a1b2c3d4e5f6...",
      "license": "BSD-3-Clause",
      "description": "Community-led collection of recipes, build infrastructure and distributions for the conda package manager.",
      "dependencies": [],
      "homepage": "https://conda-forge.org",
      "github_url": "https://github.com/conda-forge",
      "logo_url": "https://conda-forge.org/assets/img/logo.png",
      "commercial": false,
    },
    "bioconda": {
      "mirrors": [
        "https://conda.anaconda.org/bioconda",
        "oci://ghcr.io/channel-mirrors/bioconda",
        "https://prefix.dev/bioconda",
        "https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/bioconda"
      ],
      "trust_root": "sha256:g7h8i9j0k1l2...",
      "license": "MIT",
      "description": "Bioinformatics packages for conda.",
      "dependencies": ["conda-forge"],
      "homepage": "https://bioconda.github.io",
      "github_url": "https://github.com/bioconda",
      "logo_url": "https://bioconda.github.io/assets/img/logo.png",
      "commercial": false,
    },
    ...
  },
  "last_updated": "2024-09-02T12:00:00Z"
}
```

A conda client would try to resolve the name of a channel from this public location. The file should be served under `https://conda.org/channels.json`. When the channel name cannot be resolved from the public registry, the client should fall back to a configured default host such as `https://conda.anaconda.org`.

We encourage clients to make use of additional metadata to display to their users, such as the logo of the channel, the description, and the license information. Most importantly, clients can give hints if a channel relies on another channel that is not part of the configuration (for example, if someone uses the `bioconda` channel but forgets to add `conda-forge`).

## Impact and Adoption

This proposal aims to benefit the entire conda ecosystem:

- Users will have more flexibility in choosing and verifying channels.
- Channel Maintainers can more easily publicize their channels and provide critical metadata.
- Tool Developers can leverage the registry to build more robust and flexible conda-related tools.