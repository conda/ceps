<table>
<tr><td> Title </td><td> Conda shell plugins </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Katherine Abrikian &lt;kabrikian@anaconda.com&gt;</td></tr>
<tr><td> Created </td><td> June 12, 2023</td></tr>
<tr><td> Updated </td><td> June 12, 2023</td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> conda/conda PR <a href="https://github.com/conda/conda/pull/12721">#12721</a> </td></tr>
</table>

## Abstract

This CEP proposes a potential template for a plugin ("conda shell plugin") and hook ("shell plugin hook") that can carry out the process of activating and deactivating conda environments. Extracting this logic to plugins will enable the conda community to support activation and deactivation processes for a wider variety of shells. In addition, the use of plugins for activation will reduce the present burden on conda's maintainers in managing requests for expansion of conda's environment activation and deactivation logic to additional shells.

Although the original `_Activator` class  For simplicity, the proposed plugin only handles three commands: `activate`, `reactivate` and `deactivate`.

Please check what is currently on the CEP and use this pull request as a forum to discuss changes or points of opposition to the proposal.

## Specification

### Shell Plugin Architecture
The proposed "conda shell plugin" architecture will maintain key elements of the existing structure of the `_Activator` class and child classes that are currently being used to manage `activate`, `deactivate`, `reactivate`, `hook` and `command` processes in conda. It will, however, deviate from the current logic by using `os.execve` to initiate the activation logic from within the conda Python executable, rather than from a fowarding function in a shell script that all conda subcommands must pass through. In addition, rather than having each class be a child class of `_Activator` they will instead be designed to be passed into the `PluginActivator` class in the proposed plugin hook, so that the relationship between the syntax class in the plugin and `PluginActivator` will be one of composition, rather than inheritance.

Plugin authors will be expected to:
- define a new class that provides the syntax needed for interacting with the relevant shell;
- provide an appropriate shell script that can be used to evaluate the package activation and deactivation scripts associated with the environment(s) being activated and deactivated;
- define an appropriate subcommand and create a CLI argument parser using Python's `argparse` module;
- import and call pre-written functions and `PluginActivator` methods that support:
  - consistent CLI argument parsing,
  - formatting of shell commands that will allow the relevant package activation/deactivation scripts to be run,
  - creating the environment mapping that defines the relevant environment variables for activation/reactivation/ deactivation; and
- use Python's `os.execve` function to:
  - exit conda's Python executabl;
  - replace the existing environment with the environment defined through the prepared environment mapping;
  - pass through arguments to allow for running any relevant package deactivation scripts, followed by any relevant package activation scripts;
  - execute an associated shell script that will evaluate the provided arguments and open a new subshell that will inherit the new environment, with updated environment variables resulting from any changes made by the package deactivation and activation scripts.
- provide plugin hook implementations for both the subcommand plugin hook and the proposed shell plugin hook.

### Shell Plugin Hook
The proposed shell plugin hook will facilitate the process of interfacing between the syntax class defined in the plugin and `PluginActivator`.

## Sample Implementation

A posix prototype that provides an example of the proposed plugin template and associated hook can be reviewed [here](TODO: LINK TO CONDA PR).

## Rationale

As described in conda issue [#12451](https://github.com/conda/conda/issues/12451):

> Shell interfaces are difficult to support as they differ widely, and the development team has limited experience with many of the exotic shells supported to offer meaningful support.
Let's rely on the plugin infrastructure to allow plugins that extend the supported shell interfaces. This means that most of the shells supported out of the box today will be moved into standalone plugins, and we will request community support for future development efforts.




## Backwards Compatibility

The proposed `PluginActivator` class contains only the logic for `activate`, `deactivate` and `reactivate`. A proposal for what should happen to `_Activator`, `hook` and `commands` is outside of the scope of this CEP.

The proposed architectural template for the conda shell plugins will not interfere with any of conda's existing behavior. Until `_Activator`, its child classes, and the shell scripts that ship with conda by default are deprecated, users can continue to use these commands alongside any installed conda shell plugins, provided that they are using them for a shell that conda already supports.

Even so, it is important to note that <mark>the method used by the proposed plugin architecture opens a new subshell to complete environment activation/deactivation</mark>. This represents a significant departure from the current user experience, where activation/deactivation takes place in the same subshell. Any shell environment variables that have been set by the user but not exported will be lost during the shift to a new subshell. Users who are less experienced and are unaccustomed to exporting environment variables are likely to be surprised by this behavior.



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
