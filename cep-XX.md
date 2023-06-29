<table>
<tr><td> Title </td><td> Conda shell plugins </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Katherine Abrikian &lt;kabrikian@anaconda.com&gt;</td></tr>
<tr><td> Created </td><td> June 12, 2023</td></tr>
<tr><td> Updated </td><td> June 29, 2023</td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td><li>conda/conda PR <a href="https://github.com/conda/conda/pull/12821">#12821</a>: proposed hook and plugin architecture<br /><li> conda/conda PR <a href="https://github.com/conda/conda/pull/12721">#12721</a>: alternative plugin specs &mdash; 3 posix prototypes</td></tr>
</table>

## Abstract

This CEP proposes a potential template for a plugin hook ("shell plugin hook") and associated plugin architecture ("conda shell plugin") that can carry out the process of activating and deactivating conda environments. Extracting this logic to plugins will enable the conda community to support activation and deactivation processes for a wider variety of shells. In addition, the use of plugins for activation will reduce the present burden on conda's maintainers in managing requests for expansion of conda's environment activation and deactivation logic to additional shells.

Please check what is currently on the CEP and use this pull request as a forum to discuss changes or points of opposition to the proposal.

## Specification

### Shell Plugin Hook
The proposed shell plugin hook will facilitate the process of providing shell-specific syntax to the plugin-specific version of the `_Activator` class, `PluginActivator`. Plugins will declare the required shell-specific syntax as field values in the hook's named tuple. Plugins should only yield the hook's named tuple if the plugin is compatible with the shell currently in use. The hook's fields are then used by `PluginActivator` to create class properties, via a method defined in the `CondaPluginManager` class. This allows the hook to carry out the syntax-definition function previously carried out by `_Activator`'s child classes, freeing plugin authors from the restrictions of class inheritance.

The proposed hook can be used both with plugins that rely on `os.execve` to activate the desired conda environment (as proposed) and with plugins that rely on the current method of conda environment activation, in which activation takes place within the same shell process, but requires an external method of evaluating the returned shell commands. (See [Shell Plugin Architecture](#shell-plugin-architecture) and [Alternatives](#alternatives) for more details.) For plugins using the current method to work, additional methods (currently present in `_Activator`) would have to be added to `PluginActivator`.

### Shell Plugin Architecture
The proposed shell plugin architecture allows for the creation of plugins that carry out `activate`, `deactivate` and `reactivate` processes for conda environments.

Plugin authors will be expected to:
- provide the syntax needed for interacting with the relevant shell through the fields in the shell hook;
- provide an appropriate shell script that can be used to evaluate the package activation and deactivation scripts associated with the environment(s) being activated and deactivated; and
- provide logic that allows the plugin to confirm that the current shell is compatible with the plugin prior to yielding the plugin hook.

To allow for a consistent and smooth activation process, functions that cover argument parsing and a class `PluginActivator` with all the methods needed for activation have been included in `conda/conda/plugins/shells`, so that plugin authors need not rewrite these. All elements of the activation and deactivation logic are easily surfaceable, so that if plugin authors wish to make changes to the process or augment it, they can do so.

The pre-written functions and class support:
  - consistent CLI argument parsing, using the subcommand plugin hook;
  - formatting of shell commands that will allow the relevant package activation/deactivation scripts to be run;
  - creating the environment mapping that defines the relevant environment variables for activation/reactivation/ deactivation; and
  - using Python's `os.execve` function to:
    - exit conda's Python executable;
    - replace the existing environment with the environment defined through the prepared environment mapping;
    - pass through arguments to allow for running any relevant package deactivation scripts, followed by any relevant package activation scripts;
    - execute an associated shell script that will evaluate the provided arguments and open a new subshell that will inherit the new environment, with updated environment variables resulting from any changes made by the package deactivation and activation scripts.

#### Comparison to current activation methodology
The proposed "conda shell plugin" architecture will maintain key elements of the existing logic currently being used to manage `activate`, `deactivate`, `reactivate`, `hook` and `command` processes in conda. It will, however, deviate from the current logic by using `os.execve` to initiate the activation logic from within the conda Python executable, rather than from a fowarding function in a shell script that all conda subcommands must pass through. Although both methodologies

The use of `os.execve` results in two significant departures from a UX perspective:
- The process of setting the prompt to display the name of the currently active conda environment would have to be carried out as a separate step (see proposal in [Prompt Setting](#prompt-setting), below).
- The newly activated conda environment would take place in a new shell process, rather than in the same shell. This means that only exported environment variables will be carried forward to the new environment. Currently, all environment activation and deactivation takes place within the original shell process. 

In addition, rather than having each class be a child class of `_Activator` they will instead be designed to be passed into the `PluginActivator` class via the proposed plugin hook, so that the relationship between the syntax class in the plugin and `PluginActivator` will be one of composition, rather than inheritance.

Although the original `_Activator` class handles 5 processes (`activate`, `deactivate`, `reactivate`, `hook`, and `commands`), the proposed plugin design currently only handles three processes: `activate`, `deactivate` and `reactivate`. In addition, `reactivate` has historically been limited to being called internally by other conda functions, but the plugins allow for a CLI command.

#### Prompt Setting
The current environment activation / deactivation process sets the user prompt as part of the process. This is possible because environment activation and deactivation takes place within the original shell process. In contrast, the proposed plugin activation / deactivation process starts a new interactive shell. As a result, any prompt setting during the process is overriden by the prompt setting carried out by the user's shell profile. This CEP proposes that plugin authors should advise user to include a prompt modifier command in their shell profile as part of the instructions for using the plugin.

Example prompt modifier command for POSIX shells:<br>
`PS1="$CONDA_PROMPT_MODIFIER "$PS1`

**Alternative options for prompt modification**
  - plugin authors write a shell-dependent init script to automatically set the prompt with plugin use
  - encouragement of a third-party tool for prompt setting (e.g., starship)
  - users manually run a extra script after activation/deactivation (like Python virtual environment UX)

## Sample Implementation

An example containing the proposed plugin architecture and hook in use can be seen in conda/conda PR [#12821](https://github.com/conda/conda/pull/12821); the example plugin with plugin hook is duplicated below for ease of reference:
```
from __future__ import annotations

import os
from pathlib import PurePath

import psutil

from conda.activate import native_path_to_unix
from conda.plugins import CondaShellPlugins, hookimpl

POSIX_SHELLS = {"ash", "bash", "dash", "ksh", "sh", "zsh"}


def determine_posix_shell() -> bool:
    """
    Determine whether the final path component of the shell process executable is in
    the set of compatible shells.
    """
    shell_process = psutil.Process(psutil.Process().ppid()).exe()

    return PurePath(shell_process).name in POSIX_SHELLS


@hookimpl
def conda_shell_plugins():
    if determine_posix_shell():
        yield CondaShellPlugins(
            name="posixp",
            summary="Plugin for POSIX shells used for activate, deactivate, and reactivate",
            script_path=os.path.abspath(
                "conda/plugins/shells/shell_scripts/posix_os_exec_shell.sh"
            ),
            pathsep_join=":".join,
            sep="/",
            path_conversion=native_path_to_unix,
            script_extension=".sh",
            tempfile_extension=None,
            command_join="\n",
            run_script_tmpl='. "%s"',
        )
```

## Rationale

As described in conda issue [#12451](https://github.com/conda/conda/issues/12451):

> Shell interfaces are difficult to support as they differ widely, and the development team has limited experience with many of the exotic shells supported to offer meaningful support.
Let's rely on the plugin infrastructure to allow plugins that extend the supported shell interfaces. This means that most of the shells supported out of the box today will be moved into standalone plugins, and we will request community support for future development efforts.


## Backwards Compatibility

The proposed `PluginActivator` class contains only the logic for `activate`, `deactivate` and `reactivate`. A proposal for what should happen to `_Activator`, `hook` and `commands` is outside of the scope of this CEP.

The proposed architectural template for the conda shell plugins will not interfere with any of conda's existing behavior. Until `_Activator`, its child classes, and the shell scripts that ship with conda by default are deprecated, users can continue to use these commands alongside any installed conda shell plugins, provided that they are using them for a shell that conda already supports.

Even so, it is important to note that <mark>the method used by the proposed plugin architecture opens a new shell process to complete environment activation/deactivation</mark>. This represents a significant departure from the current user experience, where activation/deactivation takes place in the same shell. Any shell environment variables that have been set by the user but not exported will be lost during the shift to the new shell process. Users who are less experienced and are unaccustomed to exporting environment variables are likely to be surprised by this behavior.

## Alternatives
Three alternatives are discussed in this section:
- [Plugin hook: Alternative to yielding logic based on current shell](#alternative-to-yielding-hook-logic-based-on-current-shell)
### Alternative to yielding hook logic based on current shell
The proposal to yield plugin logic based on the current shell is currently most easily completed through the use of `psutil`, a singly-maintained library. On Macs, `subprocess.run` uses `/bin/sh` by default to run shell commands, which makes it difficult to identify the actual shell currently being used to run conda without resorting to more complicated methods.

There are two known concerns with the current proposal:
- The current proposed method of determining the shell assumes that the shell executable is named correctly &ndash; or, that a POSIX shell has been substituted for the Bourne shell (`sh`). If a user were to use `/bin/sh` to point to a shell that requires different logic (e.g., `csh`), then a more complicated method will be needed to determine the current shell. However, plugin authors are welcome to come up with secondary methods of determining the shell and yielding the logic.
- On Oct 8, 2022, the maintainer of `psutil` noted difficulties in keeping up with bug reports and other maintenance concerns. However, `psutil` is widely used, so we might expect that if maintenance falls through, someone else might take up the burden.

An alternative to the proposal of yielding logic based on the current shell being used is to have users specify the desired shell plugin to be used in `.condarc` and access that setting via conda's `context`. This alternative will make the process of determining which plugin to use more straightforward but would also worsen the user experience for users who use multiple shells (e.g., on work computer vs. on home computer), as the desired plugin for each shell would have to be explicitly specified each time the user switches shells.

### Alternative plugin prototype: `os.exec` without shell script
Example: [Posix_os_exec.py](https://github.com/kalawac/conda/blob/shell-plugins-dev/conda/plugins/shells/posix/posix_os_exec.py)

dev/conda/plugins/shells/posix/posix_os_exec.py)<br />

#### Notes
1. Currently, this scenario activates an environment but fails to run any associated package activation and deactivation scripts.
2. SHLVL increments by 1 with each activation/deactivation. CONDA_SHLVL increments and decrements as per usual. 

#### S2 Benefits
- Frees conda from the use of shell scripts for activation and any associated security concerns.
- Using an `os.exec` function allows the Python code to be the entry point, rather than a shell fowarding function.

#### S2 Drawbacks
- Further exploration needed to determine if package activation and deactivation scripts can be run without an associated shell script; at the moment, this does not seem possible.
- PS1 cannot be exported to the final shell environment as part of the environment mapping that creates the new environment. Users may have to carry out an extra step to update the prompt to show the current environment's name (or this feature may have to be abandoned).
- Conda's users are used to activation/deactivation processes taking place in the same shell. Shell variables that have not been exported will be lost during the shift to a new subshell. Users who are less experienced and are unaccustomed to exporting environment variables are likely to be surprised by this behavior.

### Alternative plugin prototype: classic logic
Example: [Posix_activate.py](https://github.com/kalawac/conda/blob/shell-plugins-dev/conda/plugins/shells/posix/posix_activate.py)

#### Benefits
- Completely in line with current process.
- Shell activation and deactivation takes place in the current shell.

#### Drawbacks
- The current version uses an updated version of a shell script attached to conda to evaluate the logic printed by the plugin. However, since we would not expect shell scripts for all shells served by plugins to be shipped with conda by default, a final version of this plugin would require either automatic evaluation logic to be run via the user's shell profile or the user would have to manually run a shell script containing the evaluation logic. 
- If a shell script is used to evaluate printed commands, a shell script will have to be included with plugin or otherwise attached to conda. Security considerations associated with shell scripts would still have to be taken into account.
- A shell script might remain the entry point for all conda processes that are initiated with a CLI command.

## Other sections

Other relevant sections of the proposal.  Common sections include:

    * Specification -- The technical details of the proposed change.
    * Motivation -- Why the proposed change is needed.
    * Rationale -- Why particular decisions were made in the proposal.
    * Backwards Compatibility -- Will the proposed change break existing
      packages or workflows.
    * Alternatives -- Any alternatives considered during the design.
    * Sample Implementation -- Links to prototype or a sample implementation of
      the proposed change.
    * FAQ -- Frequently asked questions (and answers to them).
    * Resolution -- A short summary of the decision made by the community.
    * Reference -- Any references used in the design of the CEP.

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
