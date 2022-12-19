<table>
    <tr><td> Title </td><td> Conda Session Plugin Hook </td>
    <tr><td> Status </td><td> Draft </td></tr>
    <tr><td> Author(s) </td><td>Travis Hathaway&lt;thathaway@anaconda.com&gt;</td></tr>
    <tr><td> Created </td><td>TBD</td></tr>
    <tr><td> Updated </td><td>TBD</td></tr>
    <tr><td> Discussion </td><td>TBD</td></tr>
    <tr><td> Implementation </td><td>TBD</td></tr>
</table>

[requests-session]: https://requests.readthedocs.io/en/latest/api/#requests.Session

## Abstract

This CEP introduces a new a plugin hook that will enable customization
of all network traffic in conda. The way we intend to do this is by
allowing plugin authors to essentially replace the `CondaSession`
class. Plugin authors will either subclass our existing session or
write a new class that conforms to the `requests.Session` API. The primary
use case driving this forward is support for better authentication
handling. In this CEP, we also provide an example in the form of basic 
HTTP authentication to make our case for such a plugin hook more 
compelling. We believe that this hook not only serves for better support 
various authentication schemes but is flexible enough to handle other use 
cases in the future.

## Specification

This new plugin hook will allow plugin authors to completely replace the
`CondaSession` class currently defined in conda to handle all network 
traffic. Plugin authors will have the ability to either define a completely
new class as long as it conforms to the `requests.Session` API or simply
subclass the existing `CondaSession` class to make any desired 
customizations.

Below is an example of how a plugin author would use this new hook
to create a their own custom `CondaSession` class:

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

## Motivation

_We will talk about the authentication use case here and possibly others_

## Rationale

_Here we will argue why we wanted to target the CondaSession class for 
replacement as a plugin hook._

## Backwards Compatibility

_Let's talk about how we intend to ensure compatibility
for new CondaSession implementations._

## Sample Implementation

_I will go over a prototype I have authored as an initial
implementation here https://github.com/conda/conda/pull/12139_ 


## FAQs

_Any FAQs will go here. Plus add any in the comments of the pull request!_

## Resolution

_TBD_

## References

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

