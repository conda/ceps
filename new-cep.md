<table>
  <tr><td> Title </td><td> Conda Generic Plugin Hooks</td>
  <tr><td> Status </td><td> Draft </td></tr>
  <tr><td> Author(s) </td><td> Full Name &lt;thathaway@anaconda.com&gt;</td></tr>
  <tr><td> Created </td><td> Dec 22, 2022</td></tr>
  <tr><td> Updated </td><td> Dec 22, 2022</td></tr>
  <tr><td> Discussion </td><td> _TBD_ </td></tr>
  <tr><td> Implementation </td><td> _TBD_ </td></tr>
</table>

## Abstract

In order to support a variety use of cases and extensions to conda's default
behavior, we propose a set of generic plugin hooks in this CEP. Included will 
be `pre_run` and `post_run` hooks that will allow
plugin authors to execute their plugin code before or after conda commands
run, respectively. Additionally, we introduce the `on_exception` plugin 
hook that will allow plugin authors to execute custom code when an exception is thrown. 
For each hook, we outline example use cases and
show exactly how plugin authors will define these new hooks.

## Specification

This specification calls for the creation of the following three new plugin hooks:

- `pre_run`: runs before the invoked conda command is run
- `post_run`: runs after the invoked conda command is run
- `on_exception`: runs when an exception is raised while a conda command is invoked

Below, we discuss an example showing the use of the `pre_run` and `post_run` hooks together
and an example of the `on_exception` hook.

### `pre_run` and `post_run`

Plugin authors create the `pre_run` and `post_run` hooks by first defining a `conda.plugins.hookimpl`
decorated function called either `conda_pre_run` or `conda_post_run` which return either a `CondaPreRun` 
or `CondaPostRun` class, respectively. These classes will both receive the following three properties:

- `name`: unique name which identifies this plugin hook
- `action`: a callable which contains the code to be run
- `run_for`: a Python `set` of strings representing the commands this will be run on (e.g. `install` and `create`)

#### Example

```python
from conda.plugins import hookimpl, CondaPreRun, CondaPostRun


PLUGIN_NAME = "custom_plugin"


def custom_plugin_pre_run_action():
    """
    Defines our custom pre-run action which simply prints a message.
    """
    print("pre-run action")


@hookimpl
def conda_pre_run():
    """
    Returns our CondaPreRun class which attaches our ``custom_plugin_pre_run_action``
    to the "install" and "create" command.
    """
    yield CondaPreRun(
        name=f"{PLUGIN_NAME}_pre_run",
        action=custom_plugin_pre_run_action,
        run_for={"install", "create"}
    )


def custom_plugin_post_run_action():
    """
    Defines our custom post-run action which simply prints a message.
    """
    print("post-run action")


@hookimpl
def conda_post_run():
    """
    Returns our CondaPreRun class which attaches our ``custom_plugin_post_run_action`` to
    the "install" and "create" command.
    """
    yield CondaPreRun(
        name=f"{PLUGIN_NAME}_post_run",
        action=custom_plugin_post_run_action,
        run_for={"install", "create"}
    )
```

### `on_exception`

For the `on_exception` hook, plugin authors begin by defining a `conda.plugins.hookimpl` decorated 
function called `conda_on_exception`. This function will return the `CondaOnException` class with the
following attributes:

- `name`: unique name which identifies this plugin hook
- `action`: a callable which contains the code to be run

#### Example

```python
from conda.plugins import hookimpl, CondaOnException


PLUGIN_NAME = "custom_plugin"


def custom_plugin_on_exception_action():
    """
    Defines our custom on_exception action which simply prints a message.
    """
    print("on_exception action")


@hookimpl
def conda_on_exception():
    """
    Returns our CondaOnException class which attaches our ``custom_plugin_on_exception_action``.
    """
    yield CondaPreRun(
        name=f"{PLUGIN_NAME}_on_exception",
        action=custom_plugin_on_exception_action
    )
```


## Motivation

Our immediate motivations for adding these plugin hooks include the following:

### Better authentication handling

The `pre_run` hook will enable plugin authors to interrupt the normal start up of conda commands.
For better authentication handling, this opens the door for either asking the user directly
for their credentials or retrieving credentials from an OS keyring. These credentials can
then be stored and used for the duration of the running command and subsequent runs too.

A prototype of how this could function can be found in the following pull request:

- https://github.com/conda/conda/pull/12139

### Better exception logging

The `on_exception` hook will enable plugin authors to provide a better experience for users and
developers when exceptions are encountered. For example, a plugin could be written to display
stacktraces in color or even drop you into a debugging console.

### Plus more

The above use cases are just a few possibilities out there. We know that our users and community will
have many more ideas for how best to utilize these generic plugin hooks.

## Rationale

By introducing a set of generic hooks like the above, we grant plugin authors with quite a bit of
flexibility for customizing how conda behaves. We believe starting out with a small set of generic
plugin hooks is best so we do not overwhelm would-be developers. Depending on how much
these plugin hooks are used and whether there is a demand, we may choose add more in the future with a 
new CEP. For now though, we believe it is best to stick with this narrow selection as we slowly grow
our plugin ecosystem.

## FAQ

_TBD_

## Resolution

_TBD_

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
