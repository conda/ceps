# CEP XXXX - Virtual Package Detector Protocol

<table>
<tr><td> Title </td><td> Virtual Package Detector Protocol </td></tr>
<tr><td> Status </td><td> Proposed </td></tr>
<tr><td> Author(s) </td><td> Julian Hofer &lt;julian@prefix.dev&gt;, Wolf Vollprecht &lt;wolf@prefix.dev&gt;, Tobias Hunger &lt;tobias@prefix.dev&gt;</td></tr>
<tr><td> Created </td><td> Aug 5, 2026</td></tr>
<tr><td> Updated </td><td> Sep 18, 2026</td></tr>
<tr><td> Discussion </td><td> https://github.com/conda/ceps/pull/188, https://github.com/conda/ceps/pull/191 </td></tr>
<tr><td> Implementation </td><td> https://github.com/conda/rattler/pull/2701 (stack) </td></tr>
<tr><td> Requires </td><td> CEP 26, CEP 29, CEP 30, CEP 32, CEP 33, CEP 34, CEP 46 </td></tr>
</table>

> The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT",
> "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as
> described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) when, and only when, they appear in all capitals, as shown here.

## Abstract

A virtual package detector is a conda package with an executable that reports virtual packages as JSON.
Clients install it in a dedicated environment and use its results in the solve.
This CEP defines that protocol independently of the client's implementation language.
Registration sources define discovery and package resolution.

## Motivation

[CEP 30](./cep-0030.md) standardizes virtual packages detected by clients, but adding detection requires client updates.
Maintainers of external MPI installations, site-specific services and accelerator stacks need a way to distribute their own detectors.

conda's [CEP 4](./cep-0004.md) Python extension hook supports this, but mamba and Pixi cannot use it.
For example, conda-forge's MPI detector must be installed in conda's own Python environment before solving; a target-environment dependency cannot supply detection for that solve.

## Specification

### Registrations

A registration tells the client which detector to run and what virtual packages it reports.
For example, conda-forge could port its [existing MPI detection](https://github.com/regro/conda-forge-conda-plugins) to a package named `mpi-detect`, reporting `__conda_forge_openmpi` and `__conda_forge_mpich`.

| Field | Meaning | Example value |
| --- | --- | --- |
| Origin | Source-defined identifier | `"https://conda.anaconda.org/conda-forge"` |
| Detector name | Lowercase normalized package name, also used as the executable name | `"mpi-detect"` |
| Virtual package names | Non-empty set of virtual package names it reports | `["__conda_forge_openmpi", "__conda_forge_mpich"]` |

Virtual package names MUST satisfy [CEP 26](./cep-0026.md), begin with two underscores, contain at most 64 characters, and match:

```re
^__[a-z0-9][._-]?([a-z0-9]+(\.|-|_|$))*$
```

For example, `__conda_forge_openmpi` is valid; `openmpi` and `__mpi/openmpi` are not.

A detector MAY report virtual packages defined in [CEP 30](./cep-0030.md). This allows new versions of existing virtual packages to be tested without updating clients first.

A name's override variable is `CONDA_OVERRIDE_` followed by the name without its two leading underscores, uppercased, with `-` and `.` replaced by `_`.
Thus `__conda-forge_mpi` and `__conda_forge_mpi` both map to `CONDA_OVERRIDE_CONDA_FORGE_MPI` and collide despite being different names.

### The detector package

The detector name MUST be a valid package name according to [CEP 32](./cep-0032.md).

A detector MUST contain an executable named after its normalized package name in a [CEP 32](./cep-0032.md) environment `PATH` directory. On Windows it MUST have an `.exe`, `.cmd` or `.bat` extension.

A detector MAY have dependencies, but its direct and transitive virtual-package dependencies MUST be limited to names the client is required to provide under CEP 30 or later virtual-package CEPs.
The detector and its dependencies MUST NOT rely on pre-link, post-link or pre-unlink scripts.
Detectors SHOULD minimize and pin dependencies.

The detector MUST be resolvable for the **host platform**, the machine running the client (CEP 30's native platform), as defined by the registration source.

### Resolution and installation

Clients MUST resolve a [CEP 29](./cep-0029.md) MatchSpec containing only the detector name for the host platform, as defined by the registration source.
A source MAY require a channel qualifier but MUST NOT add version or build constraints. Ordinary solver preferences determine the build.
The only virtual packages available MUST be the client's own CEP 30 virtual packages, honoring `CONDA_OVERRIDE_*`. Detector results MUST NOT participate.

Before execution or result-cache lookup, clients MUST resolve against current repodata and compute the [environment digest](#environment-digest), a fingerprint of all resolved package records.
Clients MUST reuse a detector environment only if its digest matches; otherwise they must install the newly resolved packages.

The **detector environment** contains the detector and its resolved dependencies.
Installation MUST follow CEP 32 and [CEP 34](./cep-0034.md), with these restrictions:

- The environment MUST be dedicated to detection, separate from the target environment, the client's environment and user working environments. The detector MUST NOT become a target-environment dependency.
- Clients MUST NOT run any resolved package's pre-link, post-link or pre-unlink scripts.
- Clients MAY skip byte compilation of `noarch: python` packages ([CEP 20](./cep-0020.md)); if performed, it SHOULD be bounded like activation.
- Clients MUST NOT run detectors from incomplete installations and MUST prevent concurrent installations of the same digest from corrupting each other.

Clients MAY share environments between registrations with identical digest.

### Running a detector

The target platform is the platform being solved for.
Clients MUST NOT run detectors when it differs from the host platform (with overrides taken into account).
If the host and target platforms differ, detector-provided names are absent unless overridden, except for values CEP 30 or later virtual-package CEPs require the client to supply for the target.
Clients SHOULD warn once per skipped registration and name its override variables.

Clients SHOULD avoid execution when no applicable name can affect the solve.
They MUST NOT skip a registration whose applicable names the solve could reference, or rely on exact prediction or skipping for correctness.
Clients MAY cache results and avoid re-running the detector while the cache is valid.

To execute a detector, the client MUST:

1. Evaluate the detector environment's activation scripts, including dependencies' scripts, as for normal activation.
2. Prepend the environment's `PATH` directories in CEP 32 order to the inherited `PATH`.
3. Find the normalized detector executable only in those directories, in that order. On Windows, try `.exe`, `.cmd` and `.bat` in that order within each directory.
4. Start it with no arguments, no input on standard input, and the activated environment. The working directory is unspecified.
5. Capture standard output as the report and standard error separately as diagnostics.

A successful detector MUST exit with status `0`.

Execution limits:

- The client MUST time out and terminate the process, and SHOULD terminate its descendants. The clock starts at spawn, excluding resolution, installation and activation. The timeout SHOULD default to 30 seconds; clients MAY let users raise it, but MUST NOT exceed 300 seconds. Activation MUST be bounded separately with the same default and ceiling.
- After reading 1 MiB (1,048,576 bytes) of standard output and standard error combined, the client MUST stop reading, terminate a still-running process, and fail the detector.

Clients MUST retain standard-error diagnostics captured before a bound was reached for [failure reporting](#failure-handling).

### The report

A detector MUST write exactly one UTF-8 JSON object to standard output, with only whitespace around it.
On a host with Open MPI 5.0.10 but no MPICH, `mpi-detect` could report:

```json
{
  "version": 1,
  "virtual_packages": {
    "__conda_forge_openmpi": { "version": "5.0.10", "build_string": "0" },
    "__conda_forge_mpich": null
  },
  "cache": {
    "ttl_seconds": 86400,
    "watch_paths": ["/opt/openmpi/bin/ompi_info"],
    "watch_env": ["PATH"]
  }
}
```

This is the detector's report.
Each detector invocation MUST produce exactly one report.

- `version`: REQUIRED integer, currently `1`. Missing or unsupported versions fail the detector.
- `virtual_packages`: REQUIRED object keyed by virtual package name, compared after normalization. Each result MUST be `null` for absence or an object with a REQUIRED `version` string conforming to [CEP 33](./cep-0033.md) and an OPTIONAL `build_string` string conforming to CEP 26, defaulting to `0`.
- `cache`: OPTIONAL object of hints defined in [Caching](#caching).

Clients MUST ignore unknown top-level keys and unknown keys inside a virtual package result.
Known fields with wrong types are malformed.
Each watch list MUST contain at most 32 strings, each at most 4096 UTF-8 bytes after decoding.
Exceeding either limit makes the report malformed.
Duplicate or missing detector names make the report malformed.
Any missing or undeclared virtual package name makes the report malformed.
The report MUST contain every virtual package name from the registration and no other name.
In the example, `null` reports absent MPICH; omitting `__conda_forge_mpich` would violate the contract.
For standardized virtual package names, detectors MUST follow the presence and absence rules of their defining CEPs.

Clients MUST reject malformed reports in their entirety.
The client MUST NOT invalidate valid reports from other detectors.

### Results in the solve

Clients MUST use the selected detector's successful result in place of any client-provided result for the same name.
A non-null result replaces the whole record; `null` makes the name absent.
Applicable overrides MUST take precedence.

### Overrides

A client MUST support an [override variable](#registrations) for each of its virtual package names:

- A nonempty value MUST be parsed as a version, optionally followed by `=` and a build string; the default build string is `0`.
- An empty value MUST mean absence.
- An invalid value MUST be an error, not a warning or a fallback to detection.

Standardized virtual package names follow their defining CEPs: `CONDA_OVERRIDE_ARCHSPEC` sets the build string, `CONDA_OVERRIDE_UNIX` has no effect, and empty [`CONDA_OVERRIDE_CUDA_ARCH`](./cep-0046.md) means absence.

An override replaces the whole result for the assigned name, including its build string. It never applies to shadowed names or alternative registrations.

### Caching

Clients SHOULD cache results.
A caching client MUST key entries on registration identity, virtual package names and environment digest.
The optional `cache` object MAY contain:

| Field | Meaning |
| --- | --- |
| `ttl_seconds` | Nonnegative integer lifetime, or `"REBOOT"` for the current boot session. |
| `watch_paths` | List of absolute paths whose existence or modification time is watched. |
| `watch_env` | List of environment variable names whose values are watched in the client's own environment. |

Relative watch paths, negative or non-integer lifetimes, and lifetime strings other than `"REBOOT"` are malformed.
Every entry MUST expire.

| Condition | Required behavior |
| --- | --- |
| No `ttl_seconds` | Expiry SHOULD default to 1 hour. |
| Integer lifetime | MUST clamp to at most 30 days; `0` MUST prevent reuse. |
| `"REBOOT"` | MUST expire at the next reboot or after 30 days, whichever comes first. Clients choose how to observe reboot boundaries. |
| Reboot cannot be observed | MUST use a short fallback duration, which SHOULD be 1 hour. |
| A watched path appears, disappears or changes modification time, or a watched variable changes value | MUST expire the entry early, never extend its lifetime. Inaccessible paths count as absent. |

#### Environment digest

Clients MUST compute the environment digest from every resolved package record in the detector environment, including the detector itself.
These are ordinary conda package records. Virtual package records MUST NOT be included.

For each record, clients MUST form a line with four fields separated by a single tab (`U+0009`), in this order:

1. The normalized package name.
2. The verbatim version string.
3. The verbatim build string.
4. The package artifact, identified by the first value present:
   1. Any hash value allowed by [CEP 36](./cep-0036.md) for package authentication
   2. The serialized package URL.
5. All fields and separators must be UTF-8 encoded.

Clients MUST sort the lines in ascending order by their UTF-8 bytes and join them with a single line feed (`U+000A`) between adjacent lines.
There MUST NOT be a line feed after the last line.
The environment digest is the SHA-256 hash of the resulting UTF-8 bytes, encoded as lowercase hexadecimal.

[CEP 26](./cep-0026.md) forbids tab and line feed characters in the first three fields, and hashes or URLs may not contain them either. For this reason, these characters are safe to use as separators.

For example, consider a detector environment with these records:

- `mpi-detect` version `1.0.0`, build `h123_0`, and SHA-256 `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`.
- `python` version `3.13.7`, build `h456_0`, no package hash, and URL `https://conda.example/linux-64/python-3.13.7-h456_0.conda`.

The sorted input is shown below with `<TAB>` standing for one tab:

```text
mpi-detect<TAB>1.0.0<TAB>h123_0<TAB>aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
python<TAB>3.13.7<TAB>h456_0<TAB>https://conda.example/linux-64/python-3.13.7-h456_0.conda
```

With one line feed between the two lines and none after the second, the environment digest is `6050e025841a00c866b37c4b843b1f6bea2be6209fff9deb40303bab8861962a`.

### Failure handling

Resolution or installation errors, failed or timed-out activation, missing executable, exceeded bounds, nonzero exit, empty or malformed reports, contract violations and source-defined failures all fail the detector.

A detector failure MUST NOT abort the solve on its own.
Clients MUST discard all of that detector's results atomically, including valid entries, while preserving overrides, other registrations' results and required client-provided values.
Clients MUST report every detector failure and its captured diagnostics, even if the solve succeeds.

## Backwards compatibility

Existing virtual packages as defined in [CEP 30](./cep-0030.md) continue to work.
However, virtual package detectors are allowed to overrule virtual packages.

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
