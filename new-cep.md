<table>
    <tr><td> Title </td><td> Conda Fetch Plugin Hook </td>
    <tr><td> Status </td><td> Proposed </td></tr>
    <tr><td> Author(s) </td><td>Travis Hathaway &lt;thathaway@anaconda.com&gt;</td></tr>
    <tr><td> Created </td><td>December 20, 2022</td></tr>
    <tr><td> Updated </td><td>December 20, 2022</td></tr>
    <tr><td> Discussion </td><td>https://github.com/conda-incubator/ceps/pull/44</td></tr>
    <tr>
        <td> Implementation </td>
        <td>
            <ul>
                <li><b>Prototype:</b> https://github.com/conda/conda/pull/12139</li>
            </ul>
        </td>
    </tr>
</table>

[conda-session]: https://github.com/conda/conda/blob/4f2f302688cae358f41e842801f724d5864b4ce7/conda/gateways/connection/session.py#L63
[requests-session]: https://requests.readthedocs.io/en/latest/api/#requests.Session
[python-requests]: https://requests.readthedocs.io/en/latest
[conda-deprecation]: https://github.com/conda-incubator/ceps/blob/main/cep-9.md
[pycurl]: http://pycurl.io

## Abstract

This CEP introduces the new "conda fetch" plugin hook that will enable customization
of all network requests in conda. The way we intend to do this is by
giving plugin authors the ability to replace the [`CondaSession`][conda-session]
class. To customize it, plugin authors can either subclass our existing session 
class or write a new class that conforms to the [`requests.Session`][requests-session] 
API. Furthermore, this can either configured on a global level or on a 
channel-by-channel basis.

Our primary motivation for creating this new plugin hook is giving conda the
ability to better support various authentication schemes (e.g. OAuth or HTTP Basic
Authentication). Included in this CEP is a link to a fully functional prototype
illustrating how we intend to enable better HTTP Basic Authentication support
in conda and to illustrate exactly how this new plugin hook is supposed to work.
We believe that this hook not only serves for better support of various authentication
schemes right now but is flexible enough to handle other use cases in the future.

## Specification

The "conda fetch" plugin hook gives plugin authors the ability to completely replace the
[`CondaSession`][conda-session] class currently defined in conda to handle all network 
traffic. This can either be done on a per channel basis or for all
network requests. Plugin authors will have the ability to define
a completely new class as long as it conforms to the 
[`requests.Session`][requests-session]
API or simply subclass the existing [`CondaSession`][conda-session] class to make any
desired customizations.

In order to make it clearer to plugin authors wishing to subclass
the current [`CondaSession`][conda-session] class, we will be renaming
it to `CondaRequestsSession` to emphasize that this belongs to the
requests library. The old name will be deprecated and follow our
[standard deprecation schedule][conda-deprecation].

Below is an example of how a plugin author would use this new hook
to create their own custom [`CondaSession`][conda-session] class:

```python
from conda.gateways.connection.session import CondaRequestsSession
from conda.plugins import hookimpl, CondaFetch


PLUGIN_NAME = "custom_fetch"


class CustomSession(CondaRequestsSession):
    """
    Our custom CondaRequestsSession class which defines an additional attribute
    """
    def __init__(self):
        super().__init__()
        self.custom_attr = "custom_attr"


@hookimpl
def conda_session_classes(): 
    """
    Register our custom CondaFetch class
    """
    yield CondaFetch(
        name=PLUGIN_NAME, 
        session=CustomSession
    )
```

### Using the plugin

#### Specifying via configuration files

In order to configure this new plugin, users will either configure it
globally for conda (i.e. all network requests go through this class):

```yaml
fetch: custom_fetch
```

or on a per channel basis:

```yaml
channels:
    - https://my-custom-conda-packages.com:
        fetch: custom_fetch
```

In the latter example, the custom session class will only be used for
network requests to the configured channel. All other requests will
use the standard [`CondaSession`][conda-session] class.

#### Specifying via command line or environment variables

This plugin hook can also be specified via the command line:

```bash
$ conda install --fetch custom_fetch pandas
```

or via environment variables:

```bash
$ export CONDA_FETCH=custom_fetch
$ conda install pandas
```

## Motivation

### Better handling for authentication

The primary motivation behind this new plugin hook is
giving plugin authors the ability to support a variety of authentication
schemes. Currently, conda only supports HTTP Basic Authentication
and a custom form of token based authentication that is highly coupled
with [anaconda.org](https://anaconda.org). By creating this plugin hook,
we want to allow for the support of more complicated authentication schemes
such as OAuth or OpenID. This plugin hook will also allow 
for the support of future authentication schemes which have not even been
created yet.

Additionally, this new plugin will allow us to deprecate current mechanisms
conda uses for storing credentials that we view as undesirable. As it
currently stands, conda only supports HTTP Basic 
Authentication and the aforementioned custom token based authentication.
In both cases, credentials or tokens either have to be embedded directly
in the URL itself or stored in plain text. Both of these approaches are
undesirable and present security risks in many types of environments. By
handling these authentication schemes in the future via plugins instead
of in the core of conda, we open up the possibility for designing a more
secure credential storage workflow that can adapt to a variety of user
demands.

We also want to leverage the power of our plugin system to shift the
maintenance burden from the conda development team to third parties
for providing a diverse ecosystem of authentication related plugins.
Supporting all of these use cases within conda itself would simply
be impossible to do given the development team's current capacities.

### Experimentation and performance improvements

Also worth mentioning is the performance improvements that may be had
by switching out the networking backend. Using this new plugin hook,
one could for example configure the usage of [PycURL][pycurl] which 
has additional features and performance benefits over a library
such as [requests][python-requests].

## Rationale

The [`CondaSession`][conda-session] class in conda gives us a convenient bottle neck to
target where all network requests go through. This is the main reason why 
we have chosen this class to be replaceable by a plugin hook. We realize
that by doing so we are forcing plugin authors to comply with implementing
their own `requests`-like API if they wish to replace it, but we feel that
given this library's widespread use and good documentation, it is not
an unfair ask. Furthermore, the only public method of the 
[`requests.Session`][requests-session] class currently in use in conda is `get`,
which reduces the complexity of implementing a drop in replacement.
Regardless, we still recommend that plugin authors support other HTTP
verbs such as `post`, `put`, `head` and `delete`.

Another reason why we think it is reasonable to target this class
as being replaceable by a plugin hook is the precedent set by the existing
solver hook. The solver hook functions very similarly to this hook.
If a plugin author wants to override or modify solver behavior, all
they have to do is either extend or replace the `Solver` class.

## Sample Implementation

A prototype for what a fully functioning version of this plugin hook
would look like is available here:

- https://github.com/conda/conda/pull/12212

The prototype includes the following:

- "conda fetch" plugin hook
- "conda before action" plugin hook*
- Working HTTP basic authentication example

_*This plugin hook is necessary for making the HTTP Basic Authentication 
example work and will be introduced in a separate CEP._

You are invited to browse the pull request to get a better picture of how
this will look and function if added to conda.

## FAQs

- Why did you choose to use requests' Session class as the basis for this plugin hook?
    - We chose this class because it is a widely used library in Python and has an API which many developers will already be familiar with and comfortable using.
- What are the expected behavior inherent 3rd party conda session classes?
    - Thread safety 🔒


## Resolution

_TBD_

## References

- https://requests.readthedocs.io/en/latest/api/#requests.Session

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

