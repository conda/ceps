# CEP XXXX - Channel-provided virtual package detection plugins

<table>
<tr><td> Title </td><td> Channel-provided virtual package detection plugins </td></tr>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Wolf Vollprecht &lt;wolf@prefix.dev&gt;<br/>Tobias Hunger &lt;tobias@prefix.dev&gt;</td></tr>
<tr><td> Created </td><td> Aug 5, 2026</td></tr>
<tr><td> Updated </td><td> Aug 12, 2026</td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
<tr><td> Requires </td><td> CEP 26, CEP 30, CEP 36, CEP 42 </td></tr>
</table>

> The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT",
> "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as
> described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) when, and only when, they appear in all capitals, as shown here.

## Abstract

[CEP 30](./cep-0030.md) standardizes a fixed set of virtual packages and makes detecting them an obligation of the client.
A client can therefore only offer the names it was written to know about, and a channel shipping packages that depend on any other capability of the system has no way to have that capability detected.

This CEP lets a channel declare, in its `repodata.json`, that a package it serves is a *detection plugin* for one or more virtual packages.
A client resolving that channel installs the plugin into an isolated environment, runs it, and reads the virtual packages it reports from the plugin's standard output.
The reported values then take part in the solve exactly as a client-detected virtual package does.

The mechanism is deliberately narrow: a plugin answers only for names its channel advertised, is bounded in time and output, is cached with a mandatory expiry, and can be overridden or suppressed from the environment.
Virtual package names are assumed to be unique across channels, and a channel introducing one SHOULD build its own name into it.
It is also, unavoidably, arbitrary code execution, see [Security considerations](#security-considerations).

## Motivation

The set of virtual packages in CEP 30 is closed, and extending it requires a CEP per name (as [CEP 46](./cep-0046.md) did for `__cuda_arch`).
That is the right process for capabilities the whole ecosystem shares, and the wrong one for everything else:

- **Accelerator and interconnect stacks.** ROCm, oneAPI, Metal, Infiniband, TPUs and NPUs each need version *and* capability detection.
  Each is relevant to the channels shipping builds against it and to nobody else.
- **Site-specific capability.** An organization's internal channel may need to know about a license server, a filesystem, a kernel module or a CPU feature that no public channel cares about.
- **Capabilities that change faster than clients release.** A new GPU generation is a new value for an existing name.
  Today every client has to ship a new release to know about it, even though the channel that builds for it knows already.

In all three cases whoever builds the packages has the knowledge necessary to get the needed information.
Code that extracts the data from the machine is a typically small, easy to write, and easy to ship *as a conda package*.
What is missing is a standard way for a channel to say "run this program to find out", and a defined way to format the answers.

The workarounds are worse: `CONDA_OVERRIDE_*` variables set by hand in every environment, packages that fail at runtime rather than at solve time, wrapper scripts that solve twice, or clients carrying vendor-specific detection code for hardware their authors cannot test with.

## Specification

The terms conda channel, and channel subdirectory (subdir) MUST be understood as specified by [CEP 26](./cep-0026.md).
The `repodata.json` schema is defined in [CEP 36](./cep-0036.md).
Virtual packages are defined by [CEP 30](./cep-0030.md).

### Registering plugins in `info`

A `repodata.json` file MAY include a `virtual_package_plugins` key in its `info` dictionary.
If present, it MUST be a dictionary mapping a **package name** to a **non-empty array of virtual package names**:

```json
{
  "info": {
    "subdir": "linux-64",
    "virtual_package_plugins": {
      "rocm-detect": ["__rocm"],
      "cuda-detect": ["__cuda", "__cuda_arch"]
    }
  }
}
```

- Each key MUST be the name of a package the declaring channel serves.
  It names the package that provides the plugin, and it also names the executable to run (see [Running a plugin](#running-a-plugin)).
  It MUST therefore be a valid *package* name and MUST NOT be a virtual package name: nothing serves
  a virtual package, so a key carrying the `__` prefix cannot name the package a client would install.
  A key that is not a valid package name is an error, and a client encountering one MUST treat it as
  such rather than ignoring the entry: the key names code the client is being asked to run, and a
  channel that got it wrong has not said what it meant.
- Each value MUST be the array of virtual package names that plugin speaks for.
  One plugin MAY speak for several virtual package names.
  This is useful when an expensive query returns a set of replies.
  We only need to run that query once and return all information in one go instead of duplicating the query into a set of similar plugins, that all throw away information.
  Values that are not valid virtual package names MUST be ignored.
  Plugins left speaking for an empty set of virtual packages, because every name they declared was
  ignored, MUST themselves be ignored.
- One plugin MUST register between 1 and 16 (inclusive on both ends) virtual packages.
  This limits the amount of data one plugin can feed into a client.
  The count is over the names the plugin declares, before any invalid name is ignored.
  A plugin declaring a number of virtual packages outside that range is an error, and a client
  encountering one MUST treat it as such.
- Every name in every array MUST be a valid virtual package name (see [Virtual package names](#virtual-package-names)).
  The virtual package name SHOULD contain the channel name, to make it less likely other channels will end up using the same virtual package name.
- Additional keys in `info` beyond those CEP 36 and its extensions define are, per CEP 36, to be ignored by clients that do not recognize them.
  A client that does not implement this CEP therefore ignores `virtual_package_plugins` and behaves exactly as it does today.
- If `virtual_package_plugins` is absent or empty, the channel registers no plugins.
- A `virtual_package_plugins` that is present but is not a map of registrations, including an
  explicit `null`, is an error.
  Absence already says "no plugins", so a channel that wrote something else meant something it failed
  to express, and a client MUST NOT read that as a channel with nothing to register.

Declarations are **per subdir**, like CEP 42's `channel_relations`.
A client MUST treat the registrations of all subdirs of one channel as a single set, taking their union: a plugin registered in `linux-64` and in `noarch` is one registration, not two.
A channel MAY register a plugin in only some of its subdirs, which is how a plugin relevant to one platform is kept off the others.

A channel MUST NOT register the same (normalized) package name under two keys, MUST NOT register two
plugins for the same (normalized) virtual package name, and MUST NOT let one plugin register the same
(normalized) virtual package name twice.
All three hold over the union of the channel's subdirs, so registrations that are each valid on their
own MAY still collide once merged.
The registrations of one channel are a single set with nothing to order them by, so a client
encountering any of the three MUST treat it as an error, and MUST NOT resolve it by picking one of
the colliding registrations or by silently collapsing them into one.

Where this section makes a registration an error, a client MUST report it to the user and MUST then
ignore `info.virtual_package_plugins` in its entirety, behaving as though the channel had registered
no plugins at all.
A client MUST NOT reject the surrounding `repodata.json`: a channel whose registrations a client
cannot make sense of is still a channel whose packages it can install, and failing the document would
take every package in the subdir down with one malformed entry.
Ignoring the section as a whole rather than the offending entry is deliberate.
The errors above are all cases where the channel contradicted itself, so a client cannot tell which
part of the set was meant, and acting on the remainder would be acting on a registration set whose
meaning is not established.
This is distinct from an invalid *name*, which is ignored on its own and leaves the rest of the
registrations standing (see [Virtual package names](#virtual-package-names)).

Two **different** channels MAY register different plugins for the same name.
This is resolved the way anything served by two channels is resolved: the registration of the channel that comes first in the resolved channel order of [CEP 42](./cep-0042.md) wins.
It shadows the other channels virtual packages of the same name.

Shadowing settles which plugin answers for a name.
It does not settle whether the two channels meant the same capability by it, which is a question no client can answer: see [Naming](#naming).

- A plugin all of whose names are shadowed MUST NOT be run.
  A client SHOULD report that the registration was skipped and which channel took each name, rather than silently omitting it.
- A plugin shadowed for only some of its names MUST still be run, and MUST still be held to the full [contract](#the-contract): the contract is between a plugin and its channel.
  Verdicts for shadowed names MUST be discarded.

#### Sharded repodata

When a channel serves sharded repodata as defined by [CEP 16](./cep-0016.md), the `virtual_package_plugins` field MAY also appear in the `info` dictionary of the shard index.
Its schema and semantics there are identical.
If a channel serves both `repodata.json` and sharded repodata, the registrations declared in both MUST be consistent.

### Virtual package names

A virtual package name in a registration MUST satisfy the package name rules of CEP 26 and MUST begin with two underscores.
Concretely it MUST match:

```re
^__[a-z0-9][._-]?([a-z0-9]+(\.|-|_|$))*$
```

and MUST NOT exceed 64 characters.

A registration naming something else MUST be dropped rather than carried into the solve, where it would fail later as an unusable dependency specification.
Dropping an invalid name MUST NOT invalidate the rest of the `repodata.json`, and MUST NOT invalidate the other names of the same plugin: a client MUST parse registrations leniently and discard only what is invalid.
A client SHOULD report what it discarded.

#### Naming

A virtual package name means one thing per solve (see [Verdicts in the solve](#verdicts-in-the-solve)), so a name this mechanism introduces is a name taken from the whole ecosystem.
Channel priority decides which plugin answers for a contested name, and that is a mechanical answer to a mechanical question: it does not make two channels that meant different capabilities by one name mean the same thing, it just picks one of them and hides the other.

A channel registering a plugin for a name that no CEP standardizes SHOULD therefore make that name distinctive by building its own channel name into it: `__acme_rocm` rather than `__rocm`, for a channel named `acme`.
The resulting name MUST still satisfy the rules above.

The packages that depend on such a name are built by the party that registers the plugin, so no one outside that channel has to know the name, and nothing about a distinctive name makes it harder to depend on.
What it buys is that a channel never has to coordinate with a channel it has never heard of, and that a user configuring two channels never has one channel's answer about its own hardware quietly replaced by another channel's answer about different hardware that happens to share a name.

Names that CEP 30 or a later CEP standardizes are the deliberate exception: they are shared on purpose, and a channel registering a plugin for one is asking to answer for it.
Channels SHOULD NOT do so unless they intend to override the client's own detection; see [Interaction with client-detected virtual packages](#interaction-with-client-detected-virtual-packages).

### The plugin package

A plugin is an ordinary conda package.
It MUST be resolvable from the channel that registered it, for the platform detection is being performed on.
It MAY have dependencies, which MUST be resolved and installed with it.
A plugin MUST NOT depend on virtual packages not in the set of builtin virtual packages defined in CEP 30 (and its extensions).

A client MUST resolve a plugin's dependencies from the channel that registered it together with the channels related to it by [CEP 42](./cep-0042.md) declarations, ordered as CEP 42 specifies, and MUST NOT resolve them from other configured channels.
A channel's registration therefore reaches only code that channel's own relations reach.
Resolving a plugin's dependencies against whatever channels the user happens to have configured would make the plugin's supply chain a property of the user's configuration rather than of the registering channel, and would let one channel's registration pull code out of an unrelated one.

A client MUST install a plugin into an environment used for nothing else, following the environment lifecycle defined by CEP 32 and the package linking behavior defined by CEP 34.
It MUST NOT install a plugin into the environment being solved for, and MUST NOT make a plugin a dependency of it: the plugin's purpose is to inform the solve, and a solve that had to contain its own detection tooling would be circular.

Installing and using that environment is what executes code, and the executable named by the registration is not the only part of it that runs.
Dependencies contribute the libraries the detector loads, packages MAY carry link scripts that run at install time, and activation runs the environment's activation scripts before the detector is executed (see [Running a plugin](#running-a-plugin)).
**The unit a user extends trust to is therefore the whole detector environment, not the registered package**, and everything this CEP says about trust and opt-in applies to that closure.
See [Security considerations](#security-considerations).

Clients SHOULD cache these environments and SHOULD key that cache on a digest covering the plugin package *and every package installed alongside it*, so that a change to any dependency produces a different environment rather than reusing a stale one.
That digest names the closure, which is what makes it usable as the identity an opt-in or an allow-list is expressed over.

### Running a plugin

To obtain verdicts from a plugin, a client:

1. MUST run the environment's activation as it would for any conda environment, so that a plugin relying on activation scripts, `LD_LIBRARY_PATH`, or similar behaves as it would when used normally.
   This executes the activation scripts of every package in the environment, which is part of why the trusted unit is the environment and not the registered package; see [Security considerations](#security-considerations).
2. MUST place the environment's binary directories ahead of the inherited `PATH`, so the plugin finds its own helpers before anything on the host.
3. MUST execute the entry point named by the registration key.
   This is the executable whose name equals the plugin package name, looked up in the environment's binary directories.
   On Windows a client MUST also consider the `.exe`, `.bat` and `.cmd` extensions.
   If no such executable exists, the client MUST treat the registration as failed.
4. MUST capture standard output, which carries the report, separately from standard error, which carries diagnostics. Both streams count against the same output bound.

A plugin MUST exit with status `0` on success.
A non-zero exit MUST be treated as a failure.
A plugin that exits `0` having written nothing to standard output MUST also be treated as a failure: writing the report to standard error by mistake is common enough to be worth naming rather than reading as "nothing detected".

A client MUST bound a plugin run:

- **Time.** A client MUST apply a timeout and MUST terminate a plugin that exceeds it.
  The timeout SHOULD default to **5 seconds**.
  A client MAY let a user raise it, but MUST NOT allow any timeout longer than **60 seconds**: detection happens before a solve can begin, and an unbounded plugin is an unbounded hang in a tool a user is waiting on.
- **Output.** A client MUST bound the combined amount of standard output and standard error it will read, and MUST treat exceeding that bound as a failure.
  The bound SHOULD scale with the number of virtual packages the plugin was registered for rather than being a single fixed number.

Diagnostics a plugin wrote to standard error before the output bound was exceeded MUST be reported when a run fails.
This is to enable users to diagnose and report issues they run into, while still preventing an unbounded diagnostic stream from exhausting client memory.

A failed plugin MUST NOT abort the solve on its own.
The names it was registered for are simply not available, which the solver then reports in the ordinary way for an unsatisfiable dependency.
A client MUST report the failure.

### The report

A plugin MUST write one JSON object to standard output:

A plugin registered for `__cuda`, `__cuda_arch` and `__cuda_mps` reports:

```json
{
  "version": 1,
  "virtual_packages": {
    "__cuda": { "version": "12.4" },
    "__cuda_arch": { "version": "8.9", "build_string": "0" },
    "__cuda_mps": null
  },
  "cache": {
    "ttl_seconds": 86400,
    "watch_paths": ["/sys/module/amdgpu/version"],
    "watch_env": ["CUDA_VISIBLE_DEVICES"]
  }
}
```

- `version: int`.
  Required.
  The version of the report format.
  MUST be `1` at this time.
  A report without it, or carrying a version the client does not implement, MUST be treated as a
  failure of that plugin: the client cannot know what the remaining keys mean.
- `virtual_packages: dict[str, dict | null]`.
  Required.
  One entry per virtual package the plugin gives a verdict about, keyed by name.
  - A **dictionary** value means the virtual package is present.
    It MUST contain `version: str`, a version string as defined by [CEP 33](./cep-0033.md), and MAY contain `build_string: str`.
    Where a name's information belongs in the version and where in the build string is decided by the CEP standardizing that name; for a name this CEP does not standardize, it is the channel's choice, and channels SHOULD put a version in the version.
  - A **`null`** value means the virtual package is **not present on this system**.
    This is a verdict, and distinct from saying nothing at all.
- `cache: dict`.
  Optional.
  See [Caching](#caching).

Keys other than these MUST be ignored, at both the top level and inside a `virtual_packages` entry.
A plugin written against a later revision of this protocol MUST remain usable for the part the client understands.
Rejecting unknown keys would buy no safety: the plugin is arbitrary code the client has already run.

Because the report is keyed by name, a duplicate verdict cannot be expressed, and clients therefore need no rule for one.

### The contract

The registration is a promise in both directions, and a client MUST check it before anything reaches the solver:

- A plugin MUST give a verdict for **every** name its channel registered it for.
  A name registered but absent from `virtual_packages` is a **contract violation**, not an absent capability — that is what `null` is for.
- A plugin MUST NOT report a name its channel did **not** register it for.
  Doing so is a contract violation, and the client MUST NOT let the undeclared name reach the solve.

A client MUST treat a contract violation as a failure of that plugin and MUST report it.
This check stops plugins from registering virtual packages the channel did not advertise.

### Verdicts in the solve

Once channel priority has resolved any contested registration, a virtual package name is answered by at most one plugin (see [Registering plugins in `info`](#registering-plugins-in-info)), and it means the same thing for every record in the solve.
A verdict is therefore a single value for a single name, and it enters the solve exactly as a client-detected virtual package does:

- A **dictionary** verdict contributes one virtual package record, with that name, version and build string, to the candidate pool.
- A **`null`** verdict contributes no record, and the name is absent for the whole solve.

Nothing else changes.

A MatchSpec on a plugin-provided name is matched by name against that one record, as [CEP 29](./cep-0029.md) already specifies: one candidate per name, ordinary matching, no change to MatchSpec and no new capability required of any solver.
A spec the user wrote on a command line or in a manifest needs no special treatment either, because there is nothing for it to be ambiguous between.

A record served by any channel sees the same verdict, whether or not the channel that served it registered the plugin.
Channel relations bring a registration into a solve — resolving a channel resolves the channels it is related to by [CEP 42](./cep-0042.md), and their registrations along with them — but they do not scope a verdict once it is there.
A channel that wants a name only its own packages use makes the *name* distinctive; see [Naming](#naming).

A plugin registered by a channel taking part in the solve is eligible to run unless every one of its names was shadowed, subject to [Which plugins have to run](#which-plugins-have-to-run) and [Overrides](#overrides).

### Interaction with client-detected virtual packages

CEP 30 makes the standardized virtual packages an obligation of the **client**.
This CEP does not change that: a client MUST continue to offer them, however the channels are configured.

Where a plugin reports a name the client also detects:

- The plugin's value MUST take precedence.
  CEP 30 requires such a name to be *present* and does not dictate that the client's own detection is what fills it, so a channel that knows better about a capability may say so.
- A plugin MUST NOT be able to make such a name **disappear**.
  If a plugin registered for a standardized name reports it `null`, the client's own value MUST remain.
  Otherwise a channel's faulty detection could remove a name CEP 30 requires to be present, and a client MUST NOT be argued out of an obligation the CEP places on it.

A client MUST NOT attribute a plugin-reported virtual package to its own detection, and vice versa, in anything it records for later (lockfiles, provenance, diagnostics).

### Caching

Running a plugin can mean solving an environment, installing it, and querying hardware.
Clients SHOULD cache verdicts.
This CEP constrains how.

The `cache` object of a report MAY contain:

- `ttl_seconds: int | "REBOOT"`.
  How long the verdicts may be reused.
  The special value `"REBOOT"` means the verdicts may be reused until the next system reboot.
- `watch_paths: list[str]`.
  Paths whose existence or modification time invalidates the verdicts.
- `watch_env: list[str]`.
  Environment variable names whose value invalidates the verdicts.

A client that caches:

- MUST give every cache entry an expiry.
  "Cache this forever" MUST NOT be expressible: a driver upgrade would otherwise go unnoticed until someone cleared a cache by hand.
- SHOULD apply a default expiry of **1 hour** when a plugin specifies no `ttl_seconds`.
- MUST NOT honor an integer `ttl_seconds` longer than **30 days**, clamping to that maximum.
- MUST treat `"REBOOT"` as expiring no later than the next system reboot.
- MUST fall back to a short duration when it cannot support reboot-bounded cache entries.
  This fallback SHOULD be **1 hour**.
- MUST treat `watch_paths` and `watch_env` as able to expire an entry **sooner** than its TTL, never later.
- MUST treat an integer `ttl_seconds` of `0` as "do not reuse", which is how a plugin whose answer can change at any moment declares itself.

A client MUST key a cache entry on the plugin *environment* as well as the plugin, so that a change in any package installed alongside the plugin produces a new entry.

### Which plugins have to run

A client SHOULD NOT run a plugin whose virtual packages cannot affect the solve.
A client MAY determine the set of virtual package names that anything in the solve could reference by looking at the `depends` and `constrains` fields of the records under consideration and skip any plugin none of whose names appear in it.

This is an optimization with user-visible effect (a plugin that does not run cannot prompt, fail, or take time), so:

- A client MUST NOT skip a plugin whose names the solve could reference.
- A client MUST NOT rely on skipping for correctness: the set is a bound, not an oracle.

### Overrides

CEP 30 lets `CONDA_OVERRIDE_<NAME>` stand in for a virtual package the client detects, with `<NAME>` the uppercase name without leading underscores.
A client implementing this CEP MUST extend the same mechanism to plugin-provided virtual packages.
`CONDA_OVERRIDE_ACME_ROCM` overrides `__acme_rocm`, and there is nothing further to qualify: the name identifies the verdict on its own, because only one plugin answers for it.

- The value MUST be read as a version string, optionally followed by `=` and a build string.
- An **empty** value MUST mean the virtual package is **absent**, the sense [CEP 46](./cep-0046.md) gives an empty `CONDA_OVERRIDE_CUDA_ARCH`.
  This is the only way to ask a client to behave as though hardware were missing.
- A value that cannot be read MUST be an error rather than a warning.
  Continuing with a detected value would look to the user like the override took effect.

When every virtual package a plugin is on offer for is overridden, the client MUST NOT run that plugin.
Rewriting the answer after paying for it would defeat the purpose: Being able to avoid running a plugin at all is what makes overrides useful on a machine that lacks the hardware, or in CI, or when reproducing a bug report.

When only some of them are overridden, the client MUST still run the plugin, and MUST hold it to the
full [contract](#the-contract): the contract is between a plugin and its channel, and an override the
user set is not something the plugin can be expected to know about.
The override wins for every name it names, and the plugin's verdicts fill in the names left over.
A verdict for an overridden name MUST be discarded rather than merged with the override, so a plugin
cannot contribute a build string to a version the user supplied, or the reverse.

A client MUST NOT record an overridden value as though a plugin had produced it.

## Examples

### A channel detecting ROCm

`https://example.org/rocm-channel` builds packages against ROCm and ships the detector for it.

`linux-64/repodata.json`:

```json
{
  "info": {
    "subdir": "linux-64",
    "virtual_package_plugins": { "rocm-detect": ["__rocm"] }
  },
  "packages.conda": {
    "rocm-detect-1.0.0-h1234567_0.conda": { "name": "rocm-detect", "version": "1.0.0", "...": "..." },
    "mytool-2.0.0-h1234567_0.conda": {
      "name": "mytool", "version": "2.0.0", "depends": ["__rocm >=6.0"], "...": "..."
    }
  }
}
```

`rocm-detect` contains an executable named `rocm-detect` which prints:

```json
{ "version": 1,
  "virtual_packages": { "__rocm": { "version": "6.2.1" } },
  "cache": { "ttl_seconds": 86400, "watch_paths": ["/sys/module/amdgpu/version"] } }
```

Solving `mytool` against this channel: the client installs `rocm-detect` into an isolated environment, runs it, obtains `__rocm 6.2.1`, and `mytool 2.0.0` becomes installable.
`mytool`'s `__rocm >=6.0` is matched against `6.2.1` like any other dependency, against the one `__rocm` record the verdict contributed.
On a machine without ROCm the same plugin prints `{"version": 1, "virtual_packages": {"__rocm": null}}` and `mytool` is correctly reported as unsatisfiable rather than installing and failing at runtime.

### One plugin, several virtual packages

```json
{ "virtual_package_plugins": { "cuda-detect": ["__cuda", "__cuda_arch"] } }
```

```json
{ "version": 1,
  "virtual_packages": {
    "__cuda": { "version": "12.4" },
    "__cuda_arch": { "version": "8.9", "build_string": "0" } } }
```

One process answers for both, which is why registrations are keyed by plugin rather than by virtual package: the client runs it once.

### A name of one's own

`https://example.org/acme` builds against an in-house accelerator and registers a detector for it:

```json
{ "virtual_package_plugins": { "acme-detect": ["__acme_gpu"] } }
```

Nothing else in the ecosystem is likely to use `__acme_gpu`, so no other channel can contradict it, and `acme` can ship packages depending on it without coordinating with anyone.
Had `acme` registered `__gpu` instead, it would have taken a name any other channel (or the conda community) might reasonably want for its own virtual packages.

### Availability through a CEP 42 relation

`https://example.org/derived` declares `"channel_relations": {"base": "../rocm-channel"}` and registers nothing itself.
Resolving `derived` resolves `rocm-channel` too ([CEP 42](./cep-0042.md)), so `rocm-channel`'s registration takes part in the solve and `rocm-detect` runs.
A package from `derived` with `depends: ["__rocm >=6.0"]` is matched against the verdict, exactly as a package from `rocm-channel` is.

The relation is what brought the registration into the solve; it does not scope the verdict.
`__rocm` has one value here, and both channels' packages see it.

### Two channels, one name

`https://a.example/chan-a` and `https://b.example/chan-b` both register a plugin — different packages — for `__rocm`.

A user configuring both gets one `__rocm`: whichever of the two channels comes first in the resolved channel order supplies the plugin, and the other channel's `rocm-detect` is shadowed for that name and not run.
Every package in the solve is matched against the winning verdict, including packages from the channel that lost.
Nothing fails, and nothing has to be ranked that CEP 42 does not already rank.

That is the right outcome when both channels meant ROCm, and the wrong one when they did not: a channel that meant its own accelerator by `__rocm` has just had its detection replaced by a detector for someone else's hardware, and the packages depending on it will be resolved against an answer to a different question.
This is what [Naming](#naming) is for.
Had they registered `__chan_a_rocm` and `__chan_b_rocm`, both plugins would run, both names would be available, and each channel's packages would depend on the one they meant.

## Compatibility

- **Clients that do not implement this CEP** ignore `info.virtual_package_plugins`, as CEP 36 requires for unrecognized `info` keys, and behave exactly as before.
  They will fail to solve packages that depend on a plugin-provided virtual package — correctly, since they cannot determine whether the capability is present.
- **`repodata_version` is not bumped.** The field is additive and ignorable, which is the condition CEP 36 sets for unrecognized keys.
  Bumping it would force every client to reject repodata it can otherwise use.
- **Existing channels are unaffected.** A channel that registers nothing behaves identically.
- **Existing packages are unaffected.** No package's metadata changes; a plugin is an ordinary package and requires no new fields in `index.json`.
- **The CEP 30 names keep their meaning.** A client's obligation to provide them is unchanged, and a plugin cannot remove one.

## Security considerations

**This CEP describes a mechanism by which configuring a channel causes code from that channel to be executed on the user's machine, before any solve completes and before any package is installed.** That is a material change to the trust model of a conda channel.

### The trusted unit is the environment, not the package

A registration names one package, and it is tempting to read the exposure as that package.
It is not.
A client extends trust to the **transitive closure of the detector environment**, because more than the registered executable gets to run or to decide what runs:

- **Dependencies.** A plugin's dependencies are resolved and installed with it, and the detector loads their libraries and calls their helpers.
  A one-line detector that shells out to a vendor tool is trusting that tool, not merely shipping it.
- **Post-link scripts.** Packages MAY carry scripts that run when they are linked into an environment.
  Such a script in *any* package of the closure runs before the detector is started, and runs whether or not the detector is ever executed.
- **Activation.** [Running a plugin](#running-a-plugin) requires the environment's activation to run, which executes the activation scripts of every package that ships one.
  This is deliberate, a detector that needs `LD_LIBRARY_PATH` set has no other way to get it, and it is also code execution that precedes the detector.
- **Updates.** A dependency specified as a range brings in whatever satisfies it later.
  The closure a user approved once is not the closure that runs next month unless something pins it.

Consequences for the requirements this CEP does make:

- An opt-in, an allow-list, or a signature requirement MUST be understood as applying to the whole closure.
  Approving the name `rocm-detect` while its dependencies are unconstrained approves considerably more than a reviewer of that name would expect, and a client SHOULD NOT present it as though it did not.
- The environment digest of [The plugin package](#the-plugin-package) is the identity that actually corresponds to what runs, and is what a client wanting to pin or re-confirm an approval SHOULD use.
- Scoping dependency resolution to the registering channel and its relations is a supply-chain bound, not only a determinism one: it is what keeps the closure to code the registering channel's own declarations reach.

PEP 817 reaches the same conclusion for variant providers, treating the provider and its dependencies together as the supply-chain risk; see [Related work](#pep-817-wheel-variants).

### What is and is not bounded

What limits the exposure:

- The environment is installed from the registering channel and the channels related to it, and is used for detection only, never for the environment being solved.
- Detector execution is bounded in wall-clock time and output size.
- A plugin can only contribute names its channel advertised in public repodata, and the contract check is performed by the client.
- A plugin's effect on the solve is limited to adding, changing or withholding virtual packages.
- The combined stdout and stderr stream is bounded, so a plugin cannot make diagnostics unbounded just because stderr is not part of the report.

What does **not** limit it: Everything in the closure is arbitrary code running with the user's privileges.
It can read the user's files, make network requests, and persist.
The bounds above constrain what the detector can *report*, not what any of it can *do*, and the time and output bounds constrain the detector process only, not a link script or an activation script.

Consequently:

- A client MUST NOT run channel-provided plugins without the user having opted in.
  This CEP does not standardize the opt-in process, see [Open questions](#open-questions).
- Clients SHOULD make it visible which plugins ran, from which channel, and what they reported, and SHOULD be able to show the full contents of a detector environment on request.
  A user cannot review a closure a client will not name.
- Channels SHOULD treat a detection plugin as security-relevant code and SHOULD sign it where the ecosystem's signing mechanisms permit (see [CEP 27](./cep-0027.md)).
  Signing the registered package alone leaves its dependencies unattested, so channels SHOULD prefer detectors with few dependencies, and SHOULD pin the ones they have.

## Open questions

1. **The trust model.** The most important unresolved question.
   Options include: an explicit per-channel opt-in in client configuration; an allow-list of plugin packages; a prompt on first use; signature requirements, or hard-coded allow-lists shipped with the client itself.

Whatever is chosen has to be expressible over the detector environment rather than the registered package name, for the reasons in [The trusted unit is the environment, not the package](#the-trusted-unit-is-the-environment-not-the-package).
An allow-list of package names is the cheapest to specify and the weakest, since the closure it approves is not fixed; approving an environment digest is exact but re-prompts on every dependency update.
Where between those the ecosystem wants to sit is part of this question, not separate from it.

This CEP intentionally does not choose.
**A client MUST require opt-in in some form**, but which form is deferred.
2. **Lockfile representation.** A locked environment records the virtual packages it was solved against.
   Whether a plugin-provided one should be recorded differently from a client-detected one, and whether the plugin's identity and environment digest belong in the lockfile, wants resolving alongside [CEP 37](./cep-0037.md).
3. **Server-side validation.** Whether a channel serving a registration should be required to serve the corresponding package, and whether a registry should validate that at upload time.
4. **Cross-platform detection.** Detection is inherently about the running machine.
   Solving for a platform other than the host cannot use plugins, and today falls back to overrides.
   Whether that should be an error, a warning, or silent is unresolved.
5. **Enforcing name uniqueness.** This CEP assumes names are unique and recommends a convention for keeping them so ([Naming](#naming)), but nothing enforces it.
   Where two channels claim one name, channel priority silently picks one, which is right when they meant the same capability and wrong when they did not — and a client cannot tell the two cases apart.
   Whether the ecosystem wants a reserved-prefix rule a registry can check at upload time, a registry of the names channels have introduced, a client warning when a registration is shadowed, or nothing at all, is worth settling before this is widely used.

## Future work

- A standard way for a plugin to report *why* it decided what it did, for diagnostics, without turning the report into a log.
- Reusing one plugin environment across several channels that register the same plugin package.

## Rejected ideas

### A separate metadata file for registrations

A `virtual-package-plugins.json` alongside `repodata.json` would avoid touching `info`.
Rejected: it is an extra request on every channel for a field that is almost always absent, and it would need its own caching, validation and versioning.
CEP 42 made the same call for `channel_relations`, and consistency with it is worth more than the isolation.

### Keying registrations by virtual package rather than by plugin

`{"__cuda": "cuda-detect", "__cuda_arch": "cuda-detect"}` reads more naturally.
Rejected: it hides that one process answers for both names, and a client would have to invert the map to avoid running the plugin twice.

### Letting a plugin report any virtual package it likes

Dropping the contract check would simplify clients.
Rejected: the registration is the only part of the arrangement a user can inspect *before* code runs, and a plugin that can report anything makes it worthless.

### Letting a plugin remove a CEP 30 virtual package

Treating a `null` verdict for a standardized name as authoritative.
Rejected: CEP 30 places the obligation on the client, and a channel's faulty detection would otherwise be able to discharge an obligation that is not the channel's to discharge.

### Per-channel views of a virtual package name

An earlier draft of this CEP let a name mean different things to different channels.
A channel answered for a name over the packages it serves and over the packages of channels below it in the [CEP 42](./cep-0042.md) relation graph; the channel that answered was called the *authority*, and it was a function of the name and the channel that served the record.
Two unrelated channels could then each register `__rocm`, and each be right for its own packages.

Rejected as too expensive for what it buys.
A MatchSpec is matched by name and carries nothing about the channel of the record that declared it ([CEP 29](./cep-0029.md)), and solvers keep one candidate set per name, so `depends: ["__rocm >=6.0"]` cannot find "the right `__rocm`" on its own.
Implementing views therefore meant qualifying names internally while the candidate pool was built, rewriting every dependency on such a name to a name derived from its authority, and then keeping those internal names out of diagnostics, out of user-written specs and out of lockfiles — a whole layer of machinery in every client, in service of a case that mostly does not arise.
It also left a case that no channel had decided — two channels overriding one shared channel, neither ranking above the other — for which it had no answer better than refusing to solve.

Assuming names are unique removes all of it.
One candidate per name, no rewriting, no internal names, and no new ordering relation over channels: a name claimed twice is settled by the channel priority CEP 42 already produces, the way a package served twice is.
The cost is that two channels choosing one name for two different capabilities is no longer harmless — one of them wins for everyone — which [Naming](#naming) addresses by convention and [Open questions](#open-questions) leaves open to address by enforcement.

### Executing plugins during `get_candidates`

Resolving a virtual package at the moment the solver first needs it would be narrower than any demand scan.
Rejected as a requirement: it forces every implementation's solver to be able to await arbitrary work mid-solve, which not all can, and the gain over a demand scan is small.

### A fixed maximum output size

A single byte limit for all plugins.
Rejected in favor of a bound scaling with the number of registered names, so that a plugin answering for ten names is not held to the same limit as one answering for one.

### Bounding only standard output

Applying the output bound only to standard output would match the fact that only stdout carries the report.
Rejected because stderr is still data the client has to buffer if it wants to preserve diagnostics for failures. Counting stdout and stderr together keeps diagnostics useful without letting a plugin exhaust client memory by writing an unbounded diagnostic stream.

## Rationale

### Why the channel and not the client

The party that builds packages against a capability is the party that knows how to detect it, and is already shipping conda packages.
Every alternative puts that knowledge somewhere it has to be duplicated: in each client, or in each user's configuration.

### Why an executable and not a declarative check

A declarative language for "is this hardware present" would avoid arbitrary code execution.
It was considered and set aside because real detection is `ioctl`s, library probes, and vendor tools.
The useful cases are exactly the ones a declarative form would not cover, and a form expressive enough to cover them would be a programming language with extra steps.

This CEP trades safety for capability, and mitigates rather than removes the cost.

### Why absence is `null` rather than omission

A plugin must be able to say "not here", and a client must be able to tell that from "this plugin is broken".
Making absence explicit turns a whole class of plugin bugs (early return, a swallowed error) into a reported contract violation instead of a silently missing capability.

### Why a mandatory cache expiry

A cache without an expiry turns a one-off detection into a permanent fact about a machine.
`"REBOOT"` is still an expiry: it covers facts that are expected to stay true for a boot session but may change after hardware, driver, kernel, or daemon state is reinitialized.
Clients that cannot observe reboot boundaries fall back to a short duration rather than treating the value as permanent.
`watch_paths` and `watch_env` make an entry expire sooner, which is the safe direction.

### Why names are assumed unique

A virtual package name is global in every client today, and this CEP keeps it that way.
The alternative was drafted and rejected; see [Per-channel views of a virtual package name](#per-channel-views-of-a-virtual-package-name).

### Why the timeout ceiling is fixed

Detection blocks a solve, which blocks a user.
A configurable timeout with no ceiling is a configurable hang; the ceiling is what keeps "my channel's plugin is slow" from becoming "conda hung".

### Why not WASM

WASM is sandboxed by default, so that would indeed be a good fit.
The challenge would be to foresee and support all the APIs plugin writers might need so we can make them available to the WASM runtime (and log access).
WASM requires a language that gets compiled down to WASM binaries.
We expect many detection plugins to be short shell or python scripts, which are easier for the "normal user" to examine in an environment.

The proposed approach is less secure as it runs code without any sandbox, but also does not place any limits on what can be done to extract information from a system.
We hope the opt-in mechanism is secure enough for use without a sandbox.

## Related work

### PEP 817, wheel variants

The Python packaging ecosystem is designing a mechanism of the same shape.
[PEP 817](https://peps.python.org/pep-0817/), *Wheel Variants: Beyond Platform Tags*, lets a package declare a **variant provider**: metadata advertises a provider package, and an installer may resolve that provider into an isolated environment and run it to detect system capabilities before it selects an artifact.
Advertise a plugin in index metadata, install it apart from the environment being built, run it to read the machine, use the answer to choose packages: that is the arrangement this CEP proposes, arrived at independently.

The two differ in how much the plugin decides.
A PEP 817 provider owns a property namespace: it defines the vocabulary (properties serialize as `{namespace} :: {feature} :: {value}`), it says which properties are compatible with the running system, and it supplies the priority order used to rank variants against one another.
The provider is part of the selection algorithm.

A plugin in this CEP defines none of that.
It reports virtual packages, which have a name, a version and an optional build string like any other package, and everything downstream is [CEP 29](./cep-0029.md) MatchSpec and the ordinary solver.
There is no new vocabulary, no plugin-supplied compatibility predicate, and no plugin-supplied ordering; a channel that wants one build preferred over another expresses it the way it already does, in `depends` and `constrains`.
The narrow scope is what keeps the mechanism reviewable: a plugin's entire influence on a solve is a set of `name`/`version`/`build_string` triples, which is also why the [contract](#the-contract) can be checked mechanically.

Neither answers what happens when two sources describe the same thing differently.
PEP 817 requires consistency only within one release on one index: "All variants published on a single index for a specific package version MUST use the same provider for a given namespace."
It does not say which index's provider is authoritative when two indexes describe the same namespace differently, and namespace ownership is left to later work.
This CEP is in the same position and says so: names are assumed unique, channels are asked to keep them so by construction ([Naming](#naming)), and a name claimed by two channels falls back to channel priority.
That priority answers which channel a user prefers, not about which channel owns the name.
Whether either ecosystem eventually wants that ownership written down somewhere is the same open question on both sides.

PEP 817 cites conda's virtual packages as prior art for injecting system detection into resolution, while noting that the detection logic is tool-specific and diverges between implementations, naming rattler and mamba.
That is the limitation this CEP addresses: it moves detection out of the client and into the channel that knows the capability, so the answer stops depending on which client the user happens to run.

Both proposals make resolution depend on running third-party code, and both treat that as a security-relevant step rather than an implementation detail.
PEP 817 also draws the supply-chain boundary around the provider *and its dependencies* rather than the provider alone, which is the same conclusion this CEP reaches in [The trusted unit is the environment, not the package](#the-trusted-unit-is-the-environment-not-the-package).
The trust model is unsettled on both sides, see [Open questions](#open-questions).

## References

- [CEP 16 - Sharded Repodata](./cep-0016.md)
- [CEP 26 - Identifying Packages and Channels in the conda Ecosystem](./cep-0026.md)
- [CEP 27 - Standardizing a publish attestation for the conda ecosystem](./cep-0027.md)
- [CEP 29 - The `MatchSpec` query language](./cep-0029.md)
- [CEP 30 - Virtual packages](./cep-0030.md)
- [CEP 33 - Version literals and their ordering](./cep-0033.md)
- [CEP 34 - Contents of conda packages](./cep-0034.md)
- [CEP 36 - Package metadata files served by conda channels](./cep-0036.md)
- [CEP 37 - `conda-lock.yml` lockfiles](./cep-0037.md)
- [CEP 42 - Channel relations in repodata](./cep-0042.md)
- [CEP 46 - The `__cuda_arch` virtual package](./cep-0046.md)
- [PEP 817 - Wheel Variants: Beyond Platform Tags](https://peps.python.org/pep-0817/)

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
