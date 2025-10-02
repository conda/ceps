<table>
  <tr><td> Title </td><td> Conda Generic Plugin Hooks</td>
  <tr><td> Status </td><td> Draft </td></tr>
  <tr><td> Author(s) </td><td> Full Name &lt;thathaway@anaconda.com&gt;</td></tr>
  <tr><td> Created </td><td> Dec 22, 2022</td></tr>
  <tr><td> Updated </td><td> Dec 22, 2022</td></tr>
  <tr><td> Discussion </td><td> _TBD_ </td></tr>
  <tr><td> Implementation </td><td> _TBD_ </td></tr>
</table>

[conda-pre-invoke-location]: https://github.com/conda/conda/blob/48f51e6c1d412270efbbdb1d9ff571087568b6ea/conda/cli/main.py#L69

## Abstract

In order to support a variety of use cases and extensions to conda's default
behavior, we propose a set of generic plugin hooks in this CEP. Included will 
be `pre_command` and `post_command` hooks that will allow
plugin authors to execute their plugin code before or after conda commands
run, respectively.  For each hook, we outline example use cases and
show exactly how plugin authors will define these new hooks.

## Specification

This specification calls for the creation of the following three new plugin hooks:

- `pre_command`: runs before the invoked conda command is run
- `post_command`: runs after the invoked conda command is run

Below, we discuss an example showing the use of the `pre_command` and `post_command` 
hooks together.

### `pre_command` and `post_command`

Plugin authors create the `pre_command` and `post_command` hooks by first defining a `conda.plugins.hookimpl`
decorated function called either `conda_pre_command` or `conda_post_command` which return either a `CondaPreCommand` 
or `CondaPostCommand` class, respectively. These classes will both receive the following three properties:

- `name`: unique name which identifies this plugin hook
- `action`: a callable which contains the code to be run
- `run_for`: a Python `set` of strings representing the commands this will be run on (e.g. `install` and `create`)

#### Example

```python
from conda.plugins import hookimpl, CondaPreCommand, CondaPostCommand


PLUGIN_NAME = "custom_plugin"


def custom_plugin_pre_command_action(command):
    """
    Defines our custom pre-run action which simply prints a message.
    """
    print(f"pre-run action before {command}")


@hookimpl
def conda_pre_commands():
    """
    Yields our CondaPreCommand instance which attaches our ``custom_plugin_pre_command_action``
    to the "install" and "create" command.
    """
    yield CondaPreCommand(
        name=f"{PLUGIN_NAME}_pre_command",
        action=custom_plugin_pre_command_action,
        run_for={"install", "create"}
    )


def custom_plugin_post_command_action(command):
    """
    Defines our custom post-run action which simply prints a message.
    """
    print(f"post-run action after {command}")


@hookimpl
def conda_post_commands():
    """
    Yields our CondaPostCommand instance which attaches our ``custom_plugin_post_command_action`` to
    the "install" and "create" command.
    """
    yield CondaPostCommand(
        name=f"{PLUGIN_NAME}_post_command",
        action=custom_plugin_post_command_action,
        run_for={"install", "create"}
    )
```

## Motivation

Our immediate motivations for adding these plugin hooks include:

### Better authentication handling

The `pre_command` hook will enable plugin authors to interrupt the normal start up of conda commands.
For better authentication handling, this opens the door for either asking the user directly
for their credentials or retrieving credentials from an OS keyring. These credentials can
then be stored and used for the duration of the running command and subsequent runs too.

A prototype of how this could function can be found in the following pull request:

- https://github.com/conda/conda/pull/12139

### Enabling the creativity of our community

The above use case is just one example, and we know that our users and 
community will have many more ideas for how best to utilize these generic plugin hooks.

## Rationale

By introducing a set of generic hooks like the above, we grant plugin authors with quite a bit of
flexibility for customizing how conda behaves. We believe starting out with a small set of generic
plugin hooks is best so that we do not overwhelm would-be conda plugin authors. Depending on 
how much these plugin hooks are used and whether there is a demand, we may choose add more in 
the future with a new CEP. For now though, we believe it is best to stick with this narrow 
selection as we slowly grow our plugin ecosystem.

## FAQ

- Will I have access to global variables such as `conda.base.context.context` in my plugin hook?
    - Yes, for all plugin hooks listed in this CEP, they will be placed after the global context
      object has been initialized.

- Where exactly will the `pre_command` hooks be called?
    - All registered `pre_command` hooks will be called before the `do_call` call in the
      [`conda.cli.main:main_subshell`][conda-pre-invoke-location] function.

- Where exactly will the `post_command` hooks be called?
    - All registered `post_command` hooks will be called after the `do_call` call in the
      [`conda.cli.main:main_subshell`][conda-pre-invoke-location] function.

- Will these hooks be available for `conda activate` and `conda deactivate` commands?
    - Initially, no. But, if there is demand for this we will reconsider making these generics
      available for these two commands. The reason for this is the slightly different way these
      commands are handled versus others. Their implementation is tightly coupled to the shell
      of the current user and adequately handling this use case would be more complex than what
      we are currently prepared to implement.

- Will I be able to combine the use of these hooks with others in a single plugin?
    - Yes! We want to create a rich set of plugin hooks to allow authors a variety of possibilities
      for extending conda. We believe the true power of these generics will show when they are 
      combined with existing plugin hooks.

- What is the execution order of the registered plugin hooks?
    - _TBD_


## Resolution

_TBD_

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
