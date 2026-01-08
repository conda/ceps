# CEP XXXX - Repodata Wheel Support

<table>
<tr><td> Title </td><td> Repodata Wheel Support</td></tr>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td>
  Dan Yeaw &lt;dyeaw@anaconda.com&gt; <br/>
  Travis Hathaway &lt;travis.j.hathaway@gmail.com&gt;
</td></tr>
<tr><td> Created </td><td> Dec 23, 2025</td></tr>
<tr><td> Updated </td><td> Dec 23, 2025</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/145 </td></tr>
<tr><td> Implementation </td><td> TBD </td></tr>
<tr><td> Requires </td><td>N/A</td></tr>
</table>

> The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT",
"RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as
described in [RFC2119][RFC2119] when, and only when, they appear in all capitals, as shown here.

## Abstract

This CEP outlines how native support for pure Python wheel packages will be achieved by adding support for them to conda's package index (repodata). When implemented, conda clients will be able to seamlessly install conda packages and pure Python wheels from enabled channels.
We explicitly limit the scope of this CEP to pure Python wheels to avoid platform-specific binary compatibility issues, but even with this limitation, we dramatically expand the number of available packages for users in the conda ecosystem.

## Motivation

While conda remains a language-agnostic packaging distribution, installing packages for use with Python represents the majority of conda usage. Users frequently encounter packages only available as wheels on PyPI, forcing them to use hybrid workflows that mix conda and PyPI installations. This approach creates several problems:

- Mixing of conda and pip or uv can result in overwritten files and broken environments
- Users must understand two package managers, their interaction points, and which of their dependencies are available from which  ecosystem
- Where there is support for mixing environments, it requires multiple solves which reduces overall package installation performance

By adding native support for pure Python wheels to repodata, conda clients can:

- Eliminate the cognitive burden of managing two package managers
- Provide users with transparent access to the broader Python ecosystem
- Maintain environment consistency and reproducibility
- Resolve dependencies across conda and PyPI packages in a single solve
- Fill gaps in conda package availability for simpler pure-Python packages
- Reduce the maintenance burden for straightforward pure-Python packages that don't require metadata modifications

Note that this CEP does not eliminate the need for conda recipes entirely. Many packages will still require proper conda feedstocks due to metadata differences, dependency corrections, or other ecosystem-specific needs. This CEP provides an additional tool for handling simpler pure-Python cases more efficiently.

## Specification

### Add a new top-level key `packages.whl` to list wheels in a channel

According to the current draft schema for [repodata.json][repodata-schema], repodata consists of five top
level keys:

- repodata_version
- info
- packages
- packages.conda
- removed

This CEP proposes the addition of a new `packages.whl` section to account for the wheel format. This key points to a mapping that MUST contain [repodata record][repodata-record-schema] objects.

### `packages.whl` dictionary structure

The `packages.whl` dictionary maps conda-like filenames to repodata records. The key MUST follow the format specified in [Key naming requirements](#key-naming-requirements). The value MUST be a repodata record object that conforms to the [repodata record schema][repodata-record-schema] with the following field specifications:

- **`name`**: Taken from the wheel's METADATA `Name` field, normalized per [CEP 26][cep-26] and any parent channel name mappings.
- **`version`**: Taken from the wheel's METADATA `Version` field, normalized per PEP 440.
- **`build`**: Format `py{PY_MAJOR_VERSION}_{build_number}` (e.g., `py3_0`), conforming to CEP 26 build string conventions.
- **`build_number`**: As in regular conda packages. MUST be 0 initially; MAY be incremented for rebuilds.
- **`depends`**: Array including:
  - `python` dependency from `Requires-Python` (if present), converted to conda format
  - All `Requires-Dist` entries from METADATA, converted from PEP 440 to conda format per [Dependency conversion](#dependency-conversion)
  - Package names normalized to conda-style names per [CEP 26][cep-26]
- **`constrains`**: Contains `!=` version specifiers from PEP 440 (not included in `depends`).
- **`fn`**: The wheel filename (e.g., `package-1.0.0-py3-none-any.whl`).
- **`subdir`**: MUST be `"noarch"`.
- **`noarch`**: MUST be `"python"`.
- **`artifact_url`**: MAY be present. See [Wheel download URLs](#wheel-download-urls) for semantics.
- **`sha256`**, **`size`**, **`timestamp`**: Standard repodata fields for the wheel file.
- **`record_version`**: MUST be present (currently 3).

### Key naming requirements

The key for each entry in `packages.whl` MUST follow the format `{name}-{version}-{build}__{abi_tag}__{platform_tag}`, where:

- `{name}` is derived from the wheel's METADATA file (the `Name` field), normalized according to conda naming conventions per [CEP 26][cep-26] and any name mappings inherited from a parent channel (see [Naming standard and channel mapping](#naming-standard-and-channel-mapping))
- `{version}` is the package version from METADATA
- `{build}` is the build string (e.g., `py3_0`, `py3_1`) from the `build` field
- `{abi_tag}-{platform_tag}` are extracted from the wheel filename (stored in the `fn` field)

Examples:

- `httpx-0.28.1-py3_0-none-any`
- `typing_extensions-4.15.0-py3_0-none-any` (METADATA name `typing-extensions` mapped to conda name `typing_extensions`)
- `requests-2.32.5-py3_1-none-any` (rebuild with build_number 1)

### Why wheel names may differ from conda names

Several factors can cause wheel names to differ from conda-style names:

1. **Wheel filename normalization:** Wheel filenames normalize hyphens to underscores per PEP 427, but the METADATA `Name` field contains the canonical name (which may have hyphens).
    - Example: `lazy-loader` (METADATA name) vs `lazy_loader` (wheel filename)

2. **Python-specific clarification:** PyPI packages are implicitly Python libraries
    - Example: `authzed-py` (conda-forge) vs `authzed` (PyPI)

3. **Variant differences:** Conda may offer multiple variants with different dependencies
    - Example: `seaborn-base` (conda-forge) vs `seaborn` (PyPI)

4. **Cross-channel naming:** Different conda channels may use different names
    - Example: `pyperformance` (conda-forge) vs `performance` (main)

### Naming standard and channel mapping

The key name for wheel records SHALL be constructed by combining the conda-style name (derived from METADATA and normalized per conda conventions) with the version, build string, and wheel tags (abi_tag-platform_tag) extracted from the filename. The python_tag is omitted as it is redundant with the build string. This ensures the name portion follows conda naming conventions, supports multiple rebuilds, and the tags portion aligns with the wheel filename structure.

When there are naming differences between PyPI wheels and conda packages, channel operators MUST determine the appropriate conda-style name by applying conda naming conventions per [CEP 26 - Identifying Packages and Channels in the conda Ecosystem][cep-26].

To help users understand which naming conventions are being used, channels MAY reference a parent channel that defines the naming conventions and mappings for wheel-to-conda name translation. Parent/child channel relationships will be defined in a separate CEP, which will specify how channels can declare a `parent_channel` field in the `info` section of repodata to inherit naming conventions and mappings from another channel.
For example, a wheel channel could reference conda-forge as its parent channel, inheriting conda-forge's established naming conventions and package name mappings. This allows channels to avoid duplicating name mapping definitions and ensures consistency across related channels.

Channel operators SHOULD document any naming conventions and mappings specific to their channel, including whether they reference a parent channel for naming conventions.

### Wheel download URLs

This CEP introduces a new optional `artifact_url` field in package records to specify download locations for individual packages.

> Note for this draft: The `artifact_url` field could also be added as a separate CEP to allow it for other record types.

When present, the `artifact_url` field SHALL follow these semantics:

- If `artifact_url` is an absolute URL, use it as is.
- If `artifact_url` is a relative URL, append it to the `base_url`.

When not present (`null`), the download location is constructed from `base_url` and `fn` (existing behavior).

This approach allows packages to be served from:

- A shared relative or absolute `base_url` with all wheels in the same directory, by populating the `base_url` field and leaving the `artifact_url` field empty.
- A manual PyPI repository with wheels in directories by the package name by populating the absolute URL in the `artifact_url` field, or the `base_url` and a relative path in the `artifact_url` field.
- External PyPI mirrors or CDNs using absolute URLs by populating the `artifact_url` field, for example to <https://files.pythonhosted.org/packages/.../package-1.0.0-py3-none-any.whl>
- Mixed sources within the same repodata file

### Wheel-Specific Record Values

When populating repodata records for pure Python wheels:

- `build`: MUST be py`PY_MAJOR_VERSION`_`build_number` (e.g. py3_0)
- `build_number`: MUST be 0 for the initial addition of a wheel version. MAY be incremented for subsequent rebuilds of the same - wheel version (e.g., to correct dependencies or metadata)
- `fn`: MUST be the wheel filename (e.g., package-1.0.0-py3-none-any.whl)
- `subdir`: MUST be "noarch"
- `noarch`: MUST be "python"
- `artifact_url`: MAY be present and follow the semantics described above

### Pure Python wheel validation

Before adding a wheel to `packages.whl`, channel operators MUST verify:

- The wheel's platform tag is `any` (e.g., `py3-none-any`, `py2.py3-none-any`)
- The wheel's ABI tag is `none`
- The wheel contains no compiled extensions (`.so`, `.pyd`, `.dylib` files)
- The wheel's `METADATA` file is present and valid

Wheels that fail any of these checks MUST NOT be added to `packages.whl`.

### Dependency conversion

Wheel dependencies (from METADATA file's Requires-Dist entries) MUST be converted to conda format following these rules:

- **Package names:** Names per [CEP 26][cep-26] and match existing conda-forge package names where they exist
- **Version specifiers:** Map PEP 440 [version specifiers][version-specifiers] to conda format:
  - The `==` operator is converted to an exact pin (removing the `==`)
  - All other PEP 440 operators (`>=`, `<=`, `<`, `>`, `~=`, `!=`) are used as-is
  - Multiple version specifiers are combined with commas (e.g., `>=1.0,<2.0`)

- **Multiple specifiers:** Combine with commas (e.g., >=1.0,<2.0)
- **Python version requirements:** Convert Requires-Python to explicit python dependency
- **Environment markers:** Ignore markers other than Python version (pure Python assumption)

Example conversion:

```text
# Wheel METADATA
Requires-Python: >=3.8
Requires-Dist: requests (>=2.20.0,<3.0.0)
Requires-Dist: click (>=7.0)
Requires-Dist: numpy (>=1.20.0,!=1.24.0)
Requires-Dist: importlib-metadata (>=1.0) ; python_version < '3.8'
```

Resulting conda record:

```json
{
  "depends": [
    "python >=3.8",
    "requests >=2.20.0,<3.0",
    "click >=7.0",
    "numpy >=1.20.0,!=1.24.0"
  ]
}
```

### Handling conditional and extra dependencies

Like in the example above of only requiring `importlib-metadata` for certain Python versions, conditional and extra dependencies MUST be supported to enable full interoperability between the ecosystems. This will be supported through a separate CEP: <https://github.com/conda/ceps/pull/111>.

### Solver behavior and package preference

#### Dependency resolution

Solvers MUST treat pure Python wheels as valid package candidates during dependency resolution with these constraints:

- **Exclusivity:** Solvers MUST NOT install both a conda package and wheel for the same package name.
- **Dependency satisfaction:** When a wheel is selected, its `depends` list MUST be satisfied like any conda package. Dependencies in the `depends` list MAY be satisfied by either wheels or conda packages.
- **Platform matching:** Since all wheels in `packages.whl` are pure Python (noarch), no platform filtering is needed.

#### User control of precedence

By default, channels with conda packages MUST prefer conda packages when they are available. Users MAY override default precedence through:

- Channel priority configuration (prefer channels with wheels).
- Explicit wheel requests through `<channel name>::<package name>` syntax.
- Explicit configuration in the client itself (e.g. `prefer_conda` or `prefer_wheel`)

### Limitations

This CEP has the following known limitations:

1. **Pure Python only:** This CEP explicitly does not address wheels with binary extensions, which require platform-specific compatibility guarantees beyond the current scope. Conda’s strength is binary compatibility, so using conda packages may be the optimal solution.
2. **Environment markers**:** Only Python version markers are converted to dependencies. Other environment markers (OS, platform, etc.) are ignored based on the pure Python assumption.
3. **Conditionals and Extras:** Conditional dependencies and extras are specified by a separate CEP.
4. **Repodata size:** Supporting a significant portion of pure Python packages from PyPI (potentially hundreds of thousands of packages with multiple versions each) will substantially increase repodata size. Channels adopting wheel support at scale will need to implement sharded repodata ([CEP 16][cep-16]) to maintain acceptable performance. Alternatively, channels may choose to curate a subset of popular or requested packages rather than mirroring all of PyPI.
5. **PyPI package deletion:** PyPI allows package maintainers to delete packages (as opposed to just yanking them), which can break locked environments that reference those packages. Channels using external PyPI URLs directly are subject to this risk. For production use and reproducible environments, channels MAY mirror and store wheel artifacts locally rather than relying solely on external PyPI URLs.

## Implementation Notes

### For conda clients

Clients implementing this CEP SHOULD:

- Parse the new `packages.whl` section alongside existing package sections
- Apply the same filtering and preference logic used for conda packages
- Extract wheel metadata during solving to populate dependency information
- Provide the ability to natively install wheels or on-the-fly convert wheels to conda packages for installation

### For channel operators

Channel operators adding wheel support SHOULD:

- Implement validation to ensure only pure Python wheels are included
- Maintain a mapping of PyPI to conda-style names for their channel, or reference a parent channel that provides these mappings (see [Naming standard and channel mapping](#naming-standard-and-channel-mapping))
- Consider automation to keep the repodata up to date with newer releases on PyPI
- Document any naming conventions specific to their channel
- For production channels, consider mirroring wheel artifacts locally to ensure reproducibility and protect against PyPI deletions
- Establish patching workflows to correct metadata issues and resolve dependency conflicts
- Document patching policies and maintain transparency about modified packages

### Implementation approaches

Channels MAY implement wheel support through various approaches:

- **Manual curation**: Channels can manually add specific pure-Python wheels via repodata patching, providing full control over which packages are included and allowing for quality control and metadata validation before exposure to users.
- **Semi-automated**: Channels can implement automated processes to discover and add wheels, with manual review and patching workflows for quality assurance.
- **Full automation**: Channels can automatically mirror and index wheels from PyPI, though this requires robust validation, patching infrastructure, and consideration of repodata size impacts.

A phased approach starting with manual curation and moving toward increased automation as processes mature is RECOMMENDED. This balances the lower barrier to entry (no recipes needed for many packages) with quality control. Complex packages with metadata conflicts or special requirements should still use traditional conda feedstocks.

## Examples

### Download wheels from the default location

Below represents the default behavior and shows when the `artifact_url` field is not set:

```json
{
  "packages.whl": {
    "requests-2.32.5-py3_0-none-any": {
      "record_version": 3,
      "name": "requests",
      "version": "2.32.5",
      "build": "py3_0",
      "build_number": 0,
      "depends": [
        "charset-normalizer <4,>=2",
        "idna <4,>=2.5",
        "urllib3 <3,>=1.21.1",
        "certifi >=2017.4.17",
        "python >=3.9"
      ],
      "constrains": [],
      "fn": "requests-2.32.5-py3-none-any.whl",
      "sha256": "78820a3e5d9d3b25ce8e1c99c1c89cd19caa904a92973a3e50f8426009e8a4b3",
      "size": 6899,
      "subdir": "noarch",
      "timestamp": 1764005009,
      "noarch": "python",
      "artifact_url": null
    }
 }
}
```

With this configuration, the wheel file will be downloaded from the following location (assuming we are hosting this from `https://repo.example.com/channel`):

- `https://repo.example.com/channel/noarch/requests-2.32.5-py3-none-any.whl`

### Downloading wheels from a relative location with `base_url`

The `artifact_url` can also be relative as described above. Here's an example of what that looks like combined with setting the `base_url` property at the top level, and also showing how a channel can reference a parent channel:

```json
{
  "info": {
    "subdir": "noarch",
    "base_url": "https://repo.example.com/channel/",
    "parent_channel": "https://conda.anaconda.org/conda-forge"
  },
  "packages.whl": {
    "requests-2.32.5-py3_0-none-any": {
      "record_version": 3,
      "name": "requests",
      "version": "2.32.5",
      "build": "py3_0",
      "build_number": 0,
      "depends": [
        "charset-normalizer <4,>=2",
        "idna <4,>=2.5",
        "urllib3 <3,>=1.21.1",
        "certifi >=2017.4.17",
        "python >=3.9"
      ],
      "constrains": [],
      "fn": "requests-2.32.5-py3-none-any.whl",
      "sha256": "78820a3e5d9d3b25ce8e1c99c1c89cd19caa904a92973a3e50f8426009e8a4b3",
      "size": 6899,
      "subdir": "noarch",
      "timestamp": 1764005009,
      "noarch": "python",
      "artifact_url": "requests/requests-2.32.5-py3-none-any.whl"
    }
  }
}
```

This would result in the following being fetched by conda clients:

- `https://repo.example.com/channel/noarch/requests/requests-2.32.5-py3-none-any.whl`

### Downloading wheels from external location

The following shows an example of using an external location to download the wheel from PyPI's file hosting:

```json
{
  "packages.whl": {
    "requests-2.32.5-py3_0-none-any": {
      "record_version": 3,
      "name": "requests",
      "version": "2.32.5",
      "build": "py3_0",
      "build_number": 0,
      "depends": [
        "charset-normalizer <4,>=2",
        "idna <4,>=2.5",
        "urllib3 <3,>=1.21.1",
        "certifi >=2017.4.17",
        "python >=3.9"
      ],
      "constrains": [],
      "fn": "requests-2.32.5-py3-none-any.whl",
      "sha256": "78820a3e5d9d3b25ce8e1c99c1c89cd19caa904a92973a3e50f8426009e8a4b3",
      "size": 6899,
      "subdir": "noarch",
      "timestamp": 1764005009,
      "noarch": "python",
      "artifact_url": "https://files.pythonhosted.org/packages/1e/db/4254e3eabe8020b458f1a747140d32277ec7a271daf1d235b70dc0b4e6e3/requests-2.32.5-py3-none-any.whl"
    }
  }
}
```

### Name mapping

Here is an example of name mapping and normalization of the record name and dependencies.

```json
{
  "packages.whl": {
    "annotated_types-0.7.0-py3_0-none-any": {
      "record_version": 3,
      "name": "annotated-types",
      "version": "0.7.0",
      "build": "py3_0",
      "build_number": 0,
      "depends": [
        "typing_extensions >=4.0.0; if python < 3.9",
        "python >=3.8"
      ],
      "constrains": [],
      "fn": "annotated_types-0.7.0-py3-none-any.whl",
      "sha256": "1f02e8b43a8fbbc3f3e0d4f0f4bfc8131bcb4eebe8849b8e5c773f3a1c582a53",
      "size": 13643,
      "subdir": "noarch",
      "timestamp": 1756405206,
      "noarch": "python",
      "artifact_url": "https://files.pythonhosted.org/packages/78/b6/6307fbef88d9b5ee7421e68d78a9f162e0da4900bc5f5793f6d3d0e34fb8/annotated_types-0.7.0-py3-none-any.whl"
    }
  }
}
```

This example demonstrates two types of name normalization:

1. Record key format: The package is indexed using the format `{conda_name}-{version}-{build}-{abi_tag}-{platform_tag}`: `annotated_types-0.7.0-py3_0-none-any`. The name portion (`annotated_types`) comes from the METADATA `Name` field (`annotated-types`), normalized to conda conventions (mapped to `annotated_types` to match conda-forge naming).
The build portion (`py3_0`) comes from the `build` field. The tags portion (`none-any`) is extracted from the wheel filename (`annotated_types-0.7.0-py3-none-any.whl`), which normalizes the package name to underscores per PEP 427.
2. Dependency name mapping: This package depends on `typing_extensions`, which is listed in the `depends` field. On PyPI, this package is named `typing-extensions` (with a hyphen), but it has been mapped to the name `typing_extensions` (with an underscore) to match the existing conda-forge package name. Such mappings may be inherited from a parent channel (see [Naming standard and channel mapping](#naming-standard-and-channel-mapping)).

This example also demonstrates conditional dependencies. The original `METADATA` file from the wheel has the following dependency information:

```text
Requires-Python: >=3.8
Requires-Dist: typing-extensions>=4.0.0; python_version < '3.9'
```

The package record uses conditional dependency syntax (`; if python < 3.9`) to declare `typing_extensions` only when the Python version is < 3.9, matching the original wheel METADATA. The Python version constraint of >=3.8 is directly mapped.

## Rejected ideas

### Only install Python and pip inside conda environments

In this scenario, users only install Python and pip inside a clean conda environment. Here, we simply use conda as an environment manager and let pip manage the project dependencies.

This is what that typically looks like:

```bash
conda create -n pip-environment python pip
conda activate pip-environment
pip install <package>
```

Despite its safety for environment management, relying solely on conda for this purpose prevents leveraging the package distribution capabilities of the conda ecosystem.

### Editable installs with conda for dependencies only

Conda provides all the dependencies of a given package. Then that package is installed on top in editable mode, without addressing dependencies to make sure conda files aren't accidentally overwritten:

```bash
git clone https://github.com/owner/package.git
conda create -n editable-install package --deps-only
conda activate editable-install
pip install -e . --no-deps
```

### Add more conda packages

Create and maintain new conda packages for each PyPI dependency needed. Tools like [Grayskull] exist to make this easier to convert. However, this is a significant workload for the community, with over half of all conda-forge packages being pure Python. Even with more dedicated resources, creating recipes for over 400 thousand pure Python packages is not achievable.

### Add interoperability to tools through pip dependency scanning

The original version of the conda-pypi plugin called `pip` with the `--dry-run` option to analyze the solution to install a package. With a list of all the dependencies needed, the plugin installed everything available in conda channels first and what was left over would be installed with `pip install --no-deps`. Disadvantages of this approach include:

- Users still have to know which packages they want from PyPI and then have to run `conda pip install` to install them.
- There is no guarantee that the conda and pip packages installed have ABI compatibility.
- Calling pip and conda multiple times is slow.

### Add interoperability to tools through on-the-fly conversion

This is the approach that the [conda-pupa][conda-pupa] plugin used and was then implemented in [conda-pypi][conda-pypi]. When `conda pypi install <package>` is called, it fetches its set of required dependencies iteratively from PyPI just like `pip`. Similar to the dependency scanning option above, it then attempts to install as many dependencies as it can from conda.
However, this is where these two approaches start to differ. While conda-pypi simply used `pip` to install the remaining Python dependencies, conda-pupa converts wheel packages to conda and stores them in a local channel, essentially caching these converted wheels on disk. This means that a repodata.json is also generated allowing us to perform a solve entirely in conda.

Unfortunately, there are also disadvantages with this approach. Like the solution above, users still have to know which packages they want from PyPI and then have to run `conda pypi install` to install them. Additionally, the following problems also arise:

- Package conversion can take some time, especially for larger packages.
- Users must rely on a local cache for installing wheels, and this cache cannot easily be shared across computers.
- The current version must solve multiple times which is slow, although this could be optimized.

### Add interoperability to tools through uv integration

Pixi has integrated uv for installing packages from PyPI. The user adds the dependency through `pixi add --pypi <package>`. Then, when Pixi is solving the environment, it solves the conda packages using Rattler, and then calls uv to solve the PyPI dependencies. Disadvantages of this approach include:

- Like the solutions above, users still have to know which packages they want from PyPI and then have to `pixi add --pypi` them.
- Although Pixi and uv are both very fast, it is still slower than performing a single solve of the environment.

### Direct PyPI communication without repodata

Another alternative would be for conda clients to query PyPI's API directly during solving, fetching wheel metadata on-demand rather than including it in repodata. This idea was rejected due to:

- While resolvo (used by Rattler) supports dynamic metadata fetching during solving (as showcased in [rip](https://github.com/prefix-dev/rip)), libsolv requires complete package metadata upfront. This inconsistency across solvers would complicate implementation and limit compatibility.

- While on-demand fetching works well for pip and uv, using repodata provides consistency with conda's existing infrastructure, enables better caching strategies, and allows channels to curate and validate packages before they're available to users.

### Magic local channel approach

The "magic local channel" approach (<https://github.com/jaimergp/conda-pypi-channel>) was considered but rejected. This approach involves:

- A local FastAPI app intercepts the CLI and detects PyPI specs
- Fetches metadata on the fly and converts it to repodata (following some of the ideas discussed above)
- Downloads the wheels and converts them to .conda via whl2conda
- Caches and installs the .conda artifacts

While this approach provides on-demand conversion and caching, it requires a separate service to be running and adds complexity to the user workflow. The chosen approach of native repodata wheel support provides a more seamless experience where wheels are pre-indexed in channels and work with standard conda workflows without requiring additional services.

### Automatic wheel to conda package conversion and hosting

Another alternative would be establishing a build farm to automatically convert wheels to conda packages and host them on a channel, with conversion triggered by popularity, community requests, or on-demand.

#### Advantages of automatic conversion

- All packages are conda packages, simplifying client implementation
- Leverages mature conda infrastructure and tooling without client changes
- Enables metadata enrichment, quality control, and validation before publishing

#### Disadvantages and why native wheel support was chosen

Despite these advantages, this approach was rejected because:

- **Infrastructure burden:** Requires significant storage and bandwidth to host and serve converted packages that duplicate PyPI's CDN infrastructure
- **Resource inefficiency:** Wheels are already an excellent format for pure Python packages; conversion adds no technical value and wastes resources

Native wheel support provides the same user experience (transparent PyPI access) while avoiding the infrastructure burden and resource inefficiency of conversion. Channel operators who prefer converted packages can continue building conda packages from PyPI sources.

## History

The desire for better interoperability is not new and there has been a discussion over the last 12 years about balancing conda's core strengths (reproducibility, binary packages, cross-language support) with the Python community's expectations for seamless PyPI access.

### Early Vision (2012-2014)

The conda project's earliest discussions reveal a consistent vision for broad package manager interoperability that extends beyond just PyPI integration:

- Issue [#307](https://github.com/conda/conda/issue/307) (2013) proposed conda should work with pip, npm, gem, rpm, and brew, envisioning conda as a universal package manager interface
- Issue [#292](https://github.com/conda/conda/issue/292) (2013) explicitly titled "Making conda the ultimate package manager" outlined ambitious cross-ecosystem integration
- Issue [#224](https://github.com/conda/conda/issue/224) (2012) discussed deprecating pip commands in favor of native conda functionality

### The PyPI Integration Debate (2013-2016)

Two competing philosophies emerged on how or if we should provide better integration with PyPI.

#### Pro-integration

Issue [#262](https://github.com/conda/conda/issue/262) (2013): conda should install directly from PyPI to reduce duplication and improve package availability.

Arguments for this approach:

- Users frequently need packages not available on conda channels
- Building conda packages for every PyPI package is unsustainable

#### Status quo

Arguments to for maintaining an independent packaging ecosystem prevailed at the time for the following reasons:

- Conda's value proposition is reproducible, binary-focused environments with precise dependency resolution
- PyPI's source distributions and pip's resolver could compromise conda's guarantees
- The conda-forge community successfully scaled recipe creation

### Wheel Support Proposal (2017)

Issue [#5202](https://github.com/conda/conda/issues/5202) proposed direct wheel installation support, recognizing:

- Wheels provide binary distributions similar to conda packages
- Growing wheel availability on PyPI reduced build complexity
- Could bridge the gap between conda's reliability and PyPI's breadth

### Broader Context (2018)

The Python Discourse thread on [packaging scope boundaries](https://discuss.python.org/t/drawing-a-line-to-the-scope-of-python-packaging/883) reflects the larger ecosystem's struggle with:

- Multiple competing package management tools (pip, conda, poetry, pipenv)
- Unclear responsibilities and interoperability expectations
- Need for clearer standards and communication between tools

### conda-pypi development starts (2022)

Jaime Rodríguez-Guerra starts development on the conda-pypi plugin aimed to improve conda and PyPI interoperability.

### Rip development starts (2023)

Prefix.dev starts a barebones pip implemented in Rust to resolve and install PyPI dependencies with Pixi.

### Pixi Integrates with uv (Jan 2024)

Pixi changes course to use uv directly instead of rip, which unlocks features like editable installations, and git and path dependencies.

### conda-pupa creates on-the-fly conversion plugin (July 2024)

Daniel Holth creates a conda plugin that supports on-the-fly conversion of conda packages to wheels in a local channel.

### conda-whl-channel creates proof-of-concept wheel channel from repodata (Nov 2024)

Jonathan Helmus and Anil Kulkarni begin development on [conda-whl-channel](<https://github.com/Anaconda/conda-whl-channel>, a proof-of-concept that adds wheels to the `packages` section of repodata and patches conda to recognize them. The implementation supports conditional dependencies through additional meta packages. In February 2025, the conda-specific functionality is extracted into a separate plugin called [conda-whl-support](<https://github.com/Anaconda/conda-whl-support>.

### conda-pypi merges in conda-pupa functionality (Oct 2025)

conda-pupa is merged into conda-pypi which adds a `conda pypi install <package>` command and support for editable installations.

### conda-pypi integrates parts of conda-whl-support (Nov 2025)

Conda-pypi incorporates the wheel detection logic from conda-whl-support, providing the core functionality needed beyond the solver and index changes required to support the `packages.whl` section proposed in this CEP.

## References

- [Adopting uv in pixi][uv-in-pixi]
- [rip][rip]
- [conda-pypi project][conda-pypi]
- [conda-pupa][conda-pupa]

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

<!-- links -->
[RFC2119]: https://datatracker.ietf.org/doc/html/rfc2119
[repodata-schema]: https://schemas.conda.org/repodata-1.schema.json
[repodata-record-schema]: https://schemas.conda.org/repodata-record-1.schema.json
[cep-16]: https://conda.org/learn/ceps/cep-0016
[cep-26]: https://conda.org/learn/ceps/cep-0026
[version-specifiers]: https://packaging.python.org/en/latest/specifications/version-specifiers/#id5
[conda-pypi]: https://github.com/conda-incubator/conda-pypi
[conda-pupa]: https://github.com/dholth/conda-pupa
[uv-in-pixi]: https://prefix.dev/blog/uv_in_pixi
[rip]: https://github.com/prefix-dev/rip
[grayskull]: https://conda.github.io/grayskull/
