# Extensions to the recipe spec

This document describes extensions to the recipe specification as merged in cep-14.

## The `build.post_process` section

We became aware that the `conda_build_config.yaml` has ways to specify post-processing steps. These are regex replacements that are performed on any new files. 

Instead of adding these instructions to the `conda_build_config.yaml`, we decided to add a new section to the recipe spec: `build.post_process`. This section is a list of dictionaries, each with the following keys:

- `files`: globs to select files to process
- `regex`: the regex to apply
- `replacement`: the replacement string

The regex specification follows Rust `regex` syntax. Most notably, the replacement string can refer to capture groups with `$1`, `$2`, etc.
This also means that replacement strings need to escape `$` with `$$`.

Internally, we use `replace_all` from the `regex` crate. This means that the regex is applied to the entire file, not line by line.

### Example

```yaml
build:
  post_process:
    - files:
        - "*.txt"
      regex: "foo"
      replacement: "bar"
    - files:
        - "*.cmake"
      regex: "/sysroot/"
      replacement: "$${PREFIX}/"
```