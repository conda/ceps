<table>
    <tr><td>Title</td><td>Conda Auth Handler Hook</td>
    <tr><td>Status</td><td>Proposed </td></tr>
    <tr><td>Author(s)</td><td>Travis Hathaway &lt;thathaway@anaconda.com&gt;</td></tr>
    <tr><td>Created</td><td>December 20, 2022</td></tr>
    <tr><td>Updated</td><td>August 4, 2023</td></tr>
    <tr><td>Discussion</td><td>https://github.com/conda-incubator/ceps/pull/44</td></tr>
    <tr>
        <td> Implementation </td>
        <td>
            <ul>
                <li><b>Proposed feature addition:</b> https://github.com/conda/conda/pull/12911</li>
            </ul>
        </td>
    </tr>
</table>

[requests]: https://requests.readthedocs.io/en/latest
[requests-session]: https://requests.readthedocs.io/en/latest/api/#requests.Session
[AuthBase]: https://requests.readthedocs.io/en/latest/api/#requests.auth.AuthBase
[channel-settings]: https://github.com/conda/conda/issues/11825

## Abstract

This CEP introduces the new "auth handler" plugin hook that will enable customization
of authentication handling in conda. The way we intend to do this is by
giving plugin authors the ability to use a subclass of [`requests.auth.AuthBase`][AuthBase]
class. The new authentication handlers can then be configured on a per-channel
basis by utilizing the [`channel_settings`][channel-settings] configuration option in
the `condarc` file.

Our primary motivation for creating this new plugin hook is giving conda the
ability to better support various authentication schemes (e.g. OAuth or HTTP Basic
Authentication). Included in this CEP are links to the pull request adding support
for this plugin hook and a link to a project showing how it can be used.

## Specification

The "auth handler" plugin hook gives plugin authors the ability to add a new
[`AuthBase`][AuthBase] class to conda. This allows plugin authors to add new authentication
scheme support, which can then be configured on a per-channel basis via
the [`channel_settings`][channel-settings] in the `condarc` file.

### Create plugins

Below is an example of how a plugin author would use this new hook
to create their own custom [`AuthBase`][AuthBase] subclass:

```python
import os
from conda import plugins
from requests.auth import AuthBase


class EnvironmentHeaderAuth(AuthBase):
    def __init__(self, *args, **kwargs):
        self.username = os.environ["EXAMPLE_CONDA_AUTH_USERNAME"]
        self.password = os.environ["EXAMPLE_CONDA_AUTH_PASSWORD"]

    def __call__(self, request):
        request.headers["X-Username"] = self.username
        request.headers["X-Password"] = self.password
        return request


@plugins.hookimpl
def conda_auth_handlers():
    yield plugins.CondaAuthHandler(
        name="environment-header-auth",
        auth_handler=EnvironmentHeaderAuth,
    )
```

### Using the plugin

To make use of this authentication handler, a user would add the following to their
`condarc` file:

```yaml
channels:
  - https://example.com/auth-channel
channel_settings:
  - channel: https://example.com/auth-channel
    auth: environment-header-auth
```

In `channel_settings`, the `auth` parameter will be used to specify the authentication backend
to use. Additional arbitrary parameters can also be added, which will allow plugin authors
the ability to add extra configuration options when necessary.

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

## Rationale

Conda's networking is tightly coupled with the [requests][requests] library,
and it seems unlikely that this will change anytime soon. Therefore, we feel
that coupling this plugin with request's [AuthBase][AuthBase] subclass approach
for creating custom authentication schemes was a good idea. The implementation of 
this particular class is simple, and it would be easy enough to copy to a new
networking library if we were ever inclined to refactor this area of conda.

## Sample Implementation

The pull request which adds support for this feature can be found here:

- https://github.com/conda/conda/pull/12911

A project showing how this can be used can be found here:

- https://github.com/conda-incubator/conda-auth

You are invited to browse the pull request to get a better picture of how
this will look and function if added to conda.

## Resolution

_TBD_

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

