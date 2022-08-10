<table>
<tr><td> Title </td><td> Implement initial conda plugin mechanism </td>
<tr><td> Status </td><td> Draft  </td></tr>
<tr><td> Author(s) </td><td> Bianca Henderson &lt;bhenderson@anaconda.com&gt;</td></tr>
<tr><td> </td><td>Jannis Leidel &lt;jleidel@anaconda.com&gt; </td></tr>
<tr><td> Created </td><td> July 5, 2022 </td></tr>
<tr><td> Updated </td><td> July 6, 2022 </td></tr>
<tr><td> Discussion </td><td>https://github.com/conda-incubator/ceps/pull/32</td></tr>
<tr><td> Implementation </td><td>https://github.com/conda/conda/pull/11435</td></tr>
</table>

## Abstract

In order to enable customization and extra features that are compatible with and discoverable by `conda` (but do not necessarily ship as a default part of the `conda` codebase), we would like to implement an official `conda` plugin mechanism.

A plugin mechanism in `conda` would provide many benefits, including (but not limited to) the coverage of underserved use cases, the added ability to extend `conda` internals via official APIs, as well as lowering the barrier of entry for contributions from other stakeholders in the `conda` community and ecosystem.

The [initial proposal to add this plugin architecture](https://github.com/conda-incubator/ceps/blob/main/cep-2.md) has been [officially approved](https://github.com/conda-incubator/ceps/issues/23); this current CEP will discuss the specific way that the plugin mechanism will actually be implemented.

## Specification

Plugins in `conda` will integrate the "hook + entry point" structure by utilizing the [`pluggy`](https://pluggy.readthedocs.io/en/stable/index.html) Python framework. This implementation can be broken down via the following two steps:

- Define the hook(s) to be registered
- Register the plugin under the `conda` entrypoint namespace


### Hook

Below is an example of a very basic plugin "hook":

_my_plugin.py_
```python
import conda.plugins


@conda.plugins.register
def conda_subcommands():
    ...
```

### Entry point namespace utilizing a `setup.py` file

Below is an example of an entry point namespace for the custom plugin function, decorated with the plugin hook shown above:

_setup.py_
```python
from setuptools import setup

setup(
    name="my-conda-plugin",
    install_requires="conda",
    entry_points={"conda": ["my-conda-plugin = my_plugin"]},
    py_modules=["my_plugin"],
)
```

### Packaging via a `pyproject.toml` file


Below is a different packaging example that configures `setuptools` using a `pyproject.toml` file:

_setup.py_
```python
import setuptools

if __name__ == "__main__":
    setuptools.setup()
```

_pyproject.toml_
```toml
[build-system]
requires = ["setuptools", "setuptools-scm"]
build-backend = "setuptools.build_meta"

[project]
name = "my-conda-plugin"
description = "My conda plugin"
requires-python = ">=3.7"
dependencies = ["conda"]

[project.entry-points."conda"]
my-conda-plugin = "my_plugin.module:function"
```


## Rationale

This new `conda` plugin API ecosystem will bring about many benefits and possibilities, including but not limited to:

- Custom subcommands
- Support for packaging-related topics (_e.g._, virtual packages)
- Development environment integrations (_e.g._, shells)
- Alternative dependency solver backends
- Experimental features that are not currently covered by `conda`

As mentioned previously, an official plugin ecosystem will also enable contributors across the `conda` community to develop and share new features, thus bringing about more functionality and focus on the user experience.

## Backwards Compatibility

There are no expected backwards compatibility issues for this new feature.
<!-- ??? -->

## Alternatives

The following lists alternative Python frameworks, libraries, and packages that were considered for use in this proposed `conda` plugin implementation:

- [Hookman](https://github.com/ESSS/hookman)
- [`stevedore`](https://docs.openstack.org/stevedore/latest/)
- [`importlib-resources`](https://pypi.org/project/importlib-resources/)
- [`importlib-metadata`](https://pypi.org/project/importlib-metadata/)

Ultimately, `pluggy` was decided on as the ideal framework for this project due to its extensive documentation and relatively straightforward "hook + entry point" configuration.

## Implementation

The [pull request for the initial `conda` plugin mechanism implementation](https://github.com/conda/conda/pull/11435) includes extensive documentation as well as a tutorial on how to implement a basic custom subcommand. Please add any implementation-related suggestions directly to this pull request.

The method of how these plugins will be shared/distributed is currently undecided and will be discussed in a future CEP.

## Resolution

[TBD]

## Reference

- [`pluggy` Documentation](https://pluggy.readthedocs.io/en/stable/index.html)
- [CEP 2: "Add plugin architecture to conda"](https://github.com/conda-incubator/ceps/blob/main/cep-2.md)
- [`conda` Issue #11112: Introduce a Plugin System](https://github.com/conda/conda/issues/11112)

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
