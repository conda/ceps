<table>
<tr><td> Title </td><td> Language-Independent Plugins</td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Matthew R. Becker &lt;becker.mr@gmail.com&gt;</td></tr>
<tr><td> Created </td><td> May 31, 2024</td></tr>
<tr><td> Updated </td><td> May 31, 2024</td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> NA </td></tr>
</table>

## Abstract

This CEP proposes a standard for language-independent plugins for `conda` and `conda`-like tools (e.g., `pixi`, `mamba`, `rattler`). 
The goal is to generalize the existing work on plugins in `conda` via `pluggy` to something that can be implemented 
by more parties in the ecosystem. The standard below augments the existing `pluggy` plugins by defining an additional 
source of plugin information that `conda` can use to generate plugins for `pluggy`. Other `conda`-compliant package managers 
can use the same information to take appropriate actions (e.g., add a virtual package to the repodata) in order to achieve 
the same effects. The primary target of this CEP is virtual packages. Other possible cross-language plugins can be added in future 
CEPS as the need arises.

## Specification

To generate plugins, a `conda`-compliant tool will 

1. Look for the `conda-plugins` executable on the current PATH.
2. If `conda-plugins` is found, execute it.
3. If `conda-plugins` executes successfully, parse `stdout` as JSON and take the appropriate action as defined below.
4. If `conda-plugins` executes non-successfully, display an error to `stderr` containing any `stderr` from `conda-plugins` and continue.

The JSON output from `conda-plugins` must be formatted and interpreted as follows:

```JSON
{
  "virtual_pkgs": [
    {
      "name": "pkg1-name",
      "version": "pkg1-version",
      "build": "pkg1-build",
    },
    {
      "name": "pkg2-name",
      "version": "pkg2-version",
      "build": "pkg2-build",
    }
  ]
}
```

### `virtual_pkgs`

For every item in the `virtual_pkgs` list, a virtual package is defined with name `__<name>`, version `<version>`, and build string `<build>`. 
Any errors must be printed to `stderr` and the tool must continue. If the list is empty, no virtual packages will be defined. The `virtual_pkgs` key 
must be present at the top-level.

## Backwards Compatibility

The specification in this CEP can easily be made backwards compatible with the existing `conda` plugin architecture. 
A PR to `conda` should be made to run the `conda-plugins` executable, if it exists, and take the appropriate actions. 
In order to ensure conisstent behavior across the ecosystem, any plugins derived from `conda-plugins` should override 
any other source of plugins, including plugins implemented via `pluggy`.

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
