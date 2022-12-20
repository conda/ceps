<table>
    <tr><td> Title </td><td> Conda Session Plugin Hook </td>
    <tr><td> Status </td><td> Draft </td></tr>
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

## Abstract

This CEP introduces a new a plugin hook that will enable customization
of all network traffic in conda. The way we intend to do this is by
allowing plugin authors to essentially replace the [`CondaSession`][conda-session]
class by using what we are calling the "conda session class" hook.
Plugin authors can either subclass our existing session class or
write a new class that conforms to the 
[`requests.Session`][requests-session] API. 

Overriding this session class can either be done for all network 
requests or on a channel-by-channel basis. The primary
use case driving this forward is support for better authentication
handling. In this CEP, we also link to a prototype implementation 
of a basic HTTP authentication plugin to make our case for such 
a plugin hook more compelling. We believe that this hook not only
serves for better support of various authentication schemes but is 
flexible enough to handle other use cases in the future.

## Specification

This new plugin hook will allow plugin authors to completely replace the
[`CondaSession`][conda-session] class currently defined in conda to handle all network 
traffic. This can either be done on a per channel basis or for all
network requests. Plugin authors will have the ability to either define
a completely new class as long as it conforms to the 
[`requests.Session`][requests-session]
API or simply subclass the existing [`CondaSession`][conda-session] class to make any
desired customizations.

Below is an example of how a plugin author would use this new hook
to create their own custom [`CondaSession`][conda-session] class:

```python
from conda.gateways.connection.session import CondaSession
from conda.plugins import hookimpl, CondaSessionClass


PLUGIN_NAME = "custom_conda_session"


class CustomCondaSession(CondaSession):
    """
    Our custom CondaSession class which defines an additional class
    property
    """
    def __init__(self):
        super().__init__()
        self.custom_property = 'custom_property'


@hookimpl
def conda_session_classes(): 
    """
    Register our custom CondaSession class
    """
    yield CondaSessionClass(
        name=PLUGIN_NAME, 
        session_class=CustomCondaSession
    )
```

In order to configure this new plugin, users will either configure it
globally for conda (i.e. all network requests go through this class):

```yaml
network_session_class: custom_conda_session
```

or on a per channel basis:

```yaml
channels:
    - https://my-custom-conda-packages.com:
        network_session_class: custom_conda_session
```

In the latter example, the custom session class will only be used for
network requests to the configured channel. All other requests will
use the standard [`CondaSession`][conda-session] class.


## Motivation

The primary motivation behind adding this new plugin hook to conda is
giving plugin authors the ability to support a variety of authentication
schemes. For example, creating a plugin to handle HTTP basic
authentication can be created once this plugin is in place.
Currently, we rely on mechanisms that force users to store their
credentials in plain text which is undesirable in many environments.
Additionally, support for more complicated schemes such as OAuth also
becomes possible with the addition of this plugin hook.

Those are just a few examples of authentication schemes this plugin
would enable conda to support. Because there are many more, it would be
unfeasible and difficult to maintain each and every one if we decided to
add these all as custom authentication schemes to conda itself. This is
the primary reason why we want to create this plugin hook. Furthermore,
some users may be using non-standard authentication schemes and having
this plugin hook available to them enables us to support that use case.

## Rationale

The [`CondaSession`][conda-session] class in conda gives us a convenient bottle neck to
target where all network requests go through. This is the main reason why 
we have chosen this class to be replaceable by a plugin hook. We realize
that by doing so we are forcing plugin authors to comply with implementing
their own `requests`-like API if they wish to replace it, but we feel that
given this library's widespread use and good documentation, it is not
an unfair ask. Furthermore, the only public method of the 
[`requests.Session`][requests-session] class in use in conda is `get`,
which reduces the complexity of implementing a drop in replacement.

Another reason why we think it is reasonable to target this class
as being replaceable by a plugin hook is the precedent set by the
solver hook. The solver hook essentially operates under the same
principle that if a plugin author wants to override or modify behavior, all
they have to do is either extend or replace the `Solver` class.

## Sample Implementation

A prototype for what a fully functioning version of this plugin hook
would look like is available here:

- https://github.com/conda/conda/pull/12139

The prototype includes the following:

- "conda session class" plugin hook
- "conda before action" plugin hook*
- Working HTTP basic authentication example

_*This plugin hook is necessary for making the HTTP basic authentication 
example work and will be introduced in a separate CEP._

You are invited to browse the pull request to get a better picture of how
this will look and function if added to conda.

## FAQs

_Any FAQs will go here. Plus add any in the comments of the pull request!_

## Resolution

_TBD_

## References

- https://requests.readthedocs.io/en/latest/api/#requests.Session

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

