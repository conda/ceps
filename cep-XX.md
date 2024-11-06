<table>
<tr><td> Title </td><td> Conda shell plugins </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Katherine Abrikian &lt;kabrikian@anaconda.com&gt;</td></tr>
<tr><td> Created </td><td> June 29, 2023</td></tr>
<tr><td> Updated </td><td> June 29, 2023</td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td><li>conda/conda PR <a href="https://github.com/conda/conda/pull/12821">#12821</a>: proposed hook and plugin architecture<br /><li> conda/conda PR <a href="https://github.com/conda/conda/pull/12721">#12721</a>: alternative plugin specs &mdash; 3 posix prototypes</td></tr>
</table>

## Contents
1. [Abstract](#abstract)
2. [Motivation](#motivation)
3. [Background](#background)
4. [Specification](#specification)
5. [Sample Implementation](#sample-implementation)
6. [Rationale](#rationale)
7. [Backwards Compatibility](#backwards-compatibility)
8. [Alternatives](#alternatives)
9. [FAQ](#faq) - *Currently empty: will be completed as questions are received*
10. [Resolution](#resolution)
11. [References](#references)
12. [Copyright](#copyright)

## Abstract

This CEP proposes a potential template for a plugin hook ("shell plugin hook") and associated plugin architecture ("conda shell plugin") that can carry out the process of activating and deactivating conda environments. Extracting this logic to plugins will enable the conda community to support activation and deactivation processes for a wider variety of shells. In addition, the use of plugins for activation will reduce the present burden on conda's maintainers in managing requests for expansion of conda's environment activation and deactivation logic to additional shells.

Please check what is currently on the CEP and use this pull request as a forum to discuss changes or points of opposition to the proposal.

## Motivation
Conda must interface with the shell to carry out environment activation and deactivation. Conda currently supports six types of shell interfaces by default, which places a burden on maintainers to be familiar with all six shell types (plus related shells with similar syntax). In addition, conda has historically received requests to expand support to other shells.

The proposed plugin hook and plugin template would:
- increase community autonomy and agency in determining which shells are able to interface with conda,
- support the community in expanding the number of shells that can interface with conda, to potentially include niche shells,
- reduce maintainer burden by reducing the number of feature requests associated with new shell support, and
- potentially reduce maintainer burden around support for existing shells if the number of shells supported by default using the current process is reduced through code deprecation.

## Background
### Existing Conda Environment Activation Process
- [Deep dive: `conda activate`](https://docs.conda.io/projects/conda/en/latest/dev-guide/deep-dives/activation.html#conda-activate): An overview of the existing conda environment activation process. 
- [Flowcharts](https://github.com/kalawac/conda/blob/activate-flow/conda/shell/README.md): Flowcharts of the existing conda environment activation process.

## Specification

### Shell Plugin Hook
The proposed shell plugin hook will facilitate the process of defining the shell-specific syntax required for conda environment activation. Plugins will declare the required shell-specific syntax as field values in the hook's named tuple. Plugins should only yield the hook's named tuple if the plugin is compatible with the shell currently in use. A new method in  `CondaPluginManager` raises an error if no plugin hooks are yielded or if multiple hooks have been yielded.

The hook's fields are then used by [`PluginActivator`](https://github.com/kalawac/conda/blob/sp-cep/conda/plugins/shells/shell_plugins.py), the plugin-specific version of the `_Activator` class, to create class properties. This allows the hook to carry out the syntax-definition function previously carried out by `_Activator`'s child classes. As a result, plugin authors are not required to write a child class or rely on class inheritance.

The proposed hook can be used both with plugins that rely on `os.execve` to activate the desired conda environment and with plugins that rely on the current method of conda environment activation, in which activation takes place within the same shell process, but requires an external method of evaluating the returned shell commands. (See [Shell Plugin Architecture](#shell-plugin-architecture) and [Alternatives](#alternatives) for more details.)

### Shell Plugin Architecture
The proposed shell plugin architecture allows for the creation of plugins that carry out `activate`, `deactivate` and `reactivate` processes for conda environments.

Plugin authors will be expected to:
- provide the syntax needed for interacting with the relevant shell through the fields in the shell hook;
- provide an appropriate shell script that can be used to evaluate the package activation and deactivation scripts associated with the environment(s) being activated and deactivated; and
- provide logic that allows the plugin to confirm that the current shell is compatible with the plugin prior to yielding the plugin hook.

To allow for a consistent and smooth environment activation process, functions that cover argument parsing are provided in [shell_cli.py](https://github.com/kalawac/conda/blob/sp-cep/conda/plugins/shells/shell_cli.py): all shell plugins can be run using the `conda shell` command, via the subcommand plugin hook. CLI argument parsing supports the following subcommands: `conda shell activate`, `conda shell deactivate`, and `conda shell reactivate`.

The logic carrying out environment activation is handled by the `PluginActivator` class and the proposed shell plugin hook. All elements of the activation and deactivation logic are easily surfaceable, so that if plugin authors wish to make changes to the process or augment it, they can do so. Currently, the `PluginActivator` class has been designed to support conda environment activation using `os.execve`, as per the proposed plugin architecture outlined below. To facilitate plugins using logic consistent with the existing environment activation process, additional methods (currently present in `_Activator`) would have to be added to `PluginActivator`.

In summary, the pre-written functions and class outlined above support:
  - consistent CLI argument parsing, using the subcommand plugin hook;
  - formatting of shell commands that will allow the relevant package activation/deactivation scripts to be run;
  - creating the environment mapping that defines the relevant environment variables for activation/reactivation/ deactivation; and
  - using Python's `os.execve` function to:
    - exit conda's Python executable;
    - replace the existing environment with the environment defined through the prepared environment mapping;
    - pass through arguments to allow for running any relevant package deactivation scripts, followed by any relevant package activation scripts;
    - execute an associated shell script that will evaluate the provided arguments and open a new subshell that will inherit the new environment, with updated environment variables resulting from any changes made by the package deactivation and activation scripts.

#### Comparison to current activation methodology
1. The proposed "conda shell plugin" architecture will maintain key elements of the existing logic currently being used to manage `activate`, `deactivate`, `reactivate`, `hook` and `command` processes in conda. It will, however, deviate from the current logic by using `os.execve` to initiate the activation logic from within the conda Python executable, rather than from a fowarding function in a shell script that all conda commands must pass through.

2. The use of `os.execve` results in two significant departures from a UX perspective:
    - The process of setting the prompt to display the name of the currently active conda environment would have to be carried out as a separate step (see proposal in [Prompt Setting](#prompt-setting), below).
    - The newly activated conda environment would take place in a new shell process, rather than in the same shell. This means that only exported environment variables will be carried forward to the new environment. Environment variables that have been set but not exported and user-defined shell functions declared directly in the terminal will be lost during an  environment activation/deactivation process using `os.execve`.

3. Although the original `_Activator` class handles 5 processes (`activate`, `deactivate`, `reactivate`, `hook`, and `commands`), the proposed plugin design currently only handles three processes: `activate`, `deactivate` and `reactivate`. In addition, `reactivate` has historically been limited to being called internally by other conda functions, but the plugins allow `reactivate` to be run from the CLI.

4. Shell-specific syntax used in the environment activation and deactivation process will be provided through the proposed shell hook rather than through a child class of `_Activator`.
5. In the current activation method, if users modify their PATH in their shell profile after the conda init block, this can cause issues for the conda PATH. In the proposed method, if users change the PATH in their shell profile, this may also have an effect on the PATH 

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
Considerations given special weight during the development of these plugins include:
- the role of shell scripts in conda's current activation process
- benefits of providing an alternative approach to conda environment activation
- the scope of deviation of the proposed approach from the existing approach
- developer and user experience
- separation of functionality associated environment activation from `_Activator's` processes for carrying out `commands` and `hook`

The following sub-headings provide additional details on the considerations outlined above.

### Use of shell scripts as conda's entry point
-  The current process of environment activation prints commands to `stdout` or to a temporary file and relies on a shell script to evaluate the commands. The use of a shell script as conda's entry point: (i) restricts the number of shells that can be supported by default (as each new shell requires a compatible shell script); (ii) causes all conda commands, including those that do not require a shell script for activation, to pass through an additional layer, slowing down the process of CLI parsing; and (iii) results in `which conda` pointing to the shell script's forwarder function rather than to the PATH of the conda executable.
-  Early plugin prototypes determined that plugins that used the existing method of environment activation &ndash; that is, printing commands for external evaluation &ndash; either needed the shell script associated with the plugin to become the new entry point for conda's executable (e.g., by manually executing the plugin shell script at the beginning of each session) or by directly adding evaluation logic into the user's shell profile (through injection or by the user copying and pasting this logic into the shell profile). The former method is burdensome and the latter method may either be easily corrupted by an unsophisticated user (with errors in placing the necessary code in the shell profile) or generate concerns about reproducing anti-patterns of deep integration (especially if the user is unaware of the function of the code in their shell profile).
-  The proposed process does not need to use a method of external evaluation to carry out conda environment activation. The shell script required by the process is for the execution of package activation and deactivation scripts. As a result, the plugin shell scripts are significantly less complex than conda's default shell scripts and do not function as the plugin's entry point.
### Benefits of providing an alternative approach to conda environment activation
-  The approach to conda environment activation proposed in this CEP opens opportunities for new uses of conda environments that are activated in a separate shell process.
-  The process of exploring whether a Python `os.exec` function could be used for conda environment activation/deactivation has uncovered important knowledge about the points of deviation caused by this approach, as documented in this CEP. If this method is used in the future for other functionality, conda's maintainers will have a better understanding of potential considerations to look out for.
-  One of the alternative plugin designs explored in this CEP provides a means for environment activation to be carried out [without the use of a shell script](#alternative-plugin-design-osexec-without-shell-script). Unfortunately, the alternative design does not run package activation and deactivation scripts.
### Scope of deviation from the current approach to activation/deactivation
- In designing the proposed approach, weight was given to the use of existing processes, as they might act as a set of guardrails against the many issues that users might face, as previous maintainers would have already worked protections for known issues into the code.
- As the proposed approach includes significant points of deviation from the existing environment activation process, care was taken to research the proposed design and seek broader input from conda's maintainers and the conda community, with the goal of reducing unexpected impacts on conda's varied user base.

### Developer experience
- Proposals in this CEP aim to provide a smooth and straightforward experience for plugin developers. This consideration influenced the decision to minimize the required elements of the plugin architecture.
- The proposed method favors composition over inheritance, which simplifies the process of defining syntax and also grants more flexibility for working directly with the `PluginActivator` class. 
### User experience
- The proposed approaches aim to provide a straightforward and smooth user experience.
- The use of the `shell` subcommand will help to alert users to potential user experience deviations between the existing approach and the proposed approach.
- The retention of the `activate` and `deactivate` subcommands and all associated flags will allow users to more easily transition to plugin use for conda environment activation and deactivation.

### Separation of functionality associated with environment activation and deactivation from `commands` and `hook`
-  Currently, `_Activator` handles five processes: `activate`, `deactivate`, `reactivate`, `hook` and `commands`. The logic for `hook` and `commands` is completely separate from the logic for `activate`, `deactivate` and `reactivate`. The separation of this functionality reduces complexity and makes the discrete nature of these processes more clear.


## Backwards Compatibility

The proposed `PluginActivator` class contains only the logic for `activate`, `deactivate` and `reactivate`. A proposal for what should happen to `_Activator`, `hook` and `commands` is outside of the scope of this CEP.

The proposed architectural template for the conda shell plugins will not interfere with any of conda's existing behavior. Until `_Activator`, its child classes, and the shell scripts that ship with conda by default are deprecated, users can continue to use the existing `activate` and `deactivate` commands alongside any installed conda shell plugins, provided that they are using a shell that conda already supports. (If the shell is unsupported by conda, `activate` and `deactivate` will not work.)

Even so, it is important to note that the method used by the proposed plugin architecture opens a new shell process to complete environment activation/deactivation. This represents a significant departure from the current user experience, where activation/deactivation takes place in the same shell. Any shell environment variables that have been set by the user but not exported will be lost during the shift to the new shell process. Users who are less experienced and are unaccustomed to exporting environment variables are likely to be surprised by this behavior.

## Alternatives
Three alternatives are discussed in this section:
- Plugin hook: [Alternative to yielding logic based on current shell](#plugin-hook-alternative-to-yielding-hook-logic-based-on-current-shell)
- Alternative plugin design: [`os.exec` without shell script](#alternative-plugin-design-osexec-without-shell-script)
- Alternative plugin design: [current activation/deactivation logic](#alternative-plugin-design-current-activationdeactivation-logic)
### Plugin hook: Alternative to yielding hook logic based on current shell
The proposal to yield plugin logic based on the current shell is currently most easily completed through the use of `psutil`, a singly-maintained library. On Macs, `subprocess.run` uses `/bin/sh` by default to run shell commands, which makes it difficult to identify the actual shell currently being used to run conda without resorting to more complicated methods.

There are two known concerns with the current proposal:
- Each plugin hook contains syntax specific to a shell or group of shells. The current proposed method of determining the shell assumes the shell executable is not aliased. If an alias is used &ndash; for example, if `/bin/sh` is aliased to point to `csh` &ndash; then a more complicated method will be needed to determine the current shell. However, plugin authors are welcome to come up with secondary methods of determining the shell and yielding the logic.
-  `psutil` is maintained by one person who has noted difficulties in keeping up with bug reports and other maintenance concerns (Oct 8, 2022). If `psutil` stops being maintained, plugin developers may have to resort to more difficult methods to determine the shell process being run. That being said, `psutil` is widely used, so we might expect that if maintenance falls through, someone else might take up the burden.

An alternative to the proposal of yielding logic based on the current shell being used is to have users specify the desired shell plugin to be used in `.condarc` and access that setting via conda's `context`. This alternative will make the process of determining which plugin to use more straightforward but would also worsen the user experience for users who use multiple shells (e.g., on work computer vs. on home computer), as the desired plugin for each shell would have to be explicitly specified each time the user switches shells.

### Alternative plugin design: `os.exec` without shell script
Example: [Posix_os_exec.py](https://github.com/kalawac/conda/blob/shell-plugins-dev/conda/plugins/shells/posix/posix_os_exec.py)<br />

#### Notes
1. Currently, this scenario activates an environment but fails to run any associated package activation and deactivation scripts.
2. SHLVL increments by 1 with each activation/deactivation. CONDA_SHLVL increments and decrements as per usual. 

#### Benefits
- Frees conda from the use of shell scripts for activation and any associated security concerns.
- Using an `os.exec` function allows the Python code to be the entry point, rather than a shell fowarding function.

#### Drawbacks
- At the moment, it does not seem possible to run package activation and deactivation scripts using this method without an associated shell script.
- The shell prompt cannot be set as part of the environment mapping that creates the new environment. (See [Prompt Setting](#prompt-setting) for  proposed alternatives.)
- Conda's users are used to activation/deactivation processes taking place in the same shell. Shell variables that have not been exported will be lost during the shift to a new shell. User-defined shell functions declared directly in the terminal will also be lost during the activation/deactivation process.

### Alternative plugin design: current activation/deactivation logic
Example: [Posix_activate.py](https://github.com/kalawac/conda/blob/shell-plugins-dev/conda/plugins/shells/posix/posix_activate.py)

#### Benefits
- Completely in line with current process.
- Shell activation and deactivation takes place in the pre-existing shell process.

#### Drawbacks
- The example prototype uses an updated version of the [conda shell script entry point for POSIX shells](https://github.com/kalawac/conda/blob/shell-plugins-dev/conda/shell/etc/profile.d/conda.sh) to evaluate the logic printed by the plugin. However, since we cannot expect shell scripts for all shells served by plugins to be shipped with conda by default, a final version of this plugin would require either automatic evaluation logic to be run via the user's shell profile or the user would have to manually run a shell script containing the evaluation logic. 
- If a shell script is used to evaluate printed commands, a shell script will have to be included with plugin or otherwise attached to conda. Security considerations associated with shell scripts would still have to be taken into account.


## FAQ

No questions yet: this section will be completed in response to discussion associated with this draft CEP.


## Resolution
This CEP is being created to facilitate the collection of feedback around the proposed plugin hook and plugin architecture. No official decision is expected on this CEP.

## References
- [Shell Plugin Architecture Gist](https://gist.github.com/kalawac/8a05141237a59f0f4e9830096704eb4f)
- conda/conda issue [#12451](https://github.com/conda/conda/issues/12451): Add plugin hook for shell interfaces  
- Conda Fetch Plugin Hook: CEP PR [#44](https://github.com/conda-incubator/ceps/pull/44/)

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
