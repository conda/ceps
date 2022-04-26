<table>
    <tr><td> Title </td><td>Add Channel Notifications to conda</td>
    <tr><td> Status </td><td>Draft</td></tr>
    <tr><td> Author(s) </td><td>Travis Hathaway &lt;thathaway@anaconda.com&gt;</td></tr>
    <tr><td> Created </td><td> Apr 21, 2022</td></tr>
    <tr><td> Updated </td><td> Aug 21, 2022</td></tr>
    <tr><td> Discussion </td><td>NA</td></tr>
    <tr><td> Implementation </td><td>NA</td></tr>
</table>


## Abstract

In order to facilitate better communication between users of `conda` and channel owners, we want to 
implement a notification feature.
Specifically, this feature will give channel owners the ability to send users a small message (about the size 
of a single Twitter post). How often this message displays will be set by channel owners
and will be displayed for each channel a user is actively using (i.e. everything under "channels" in a
user's `.condarc`).

The messages may contain but are not limited to the following use cases:

- News about the latest package additions to the channel
- How to sponsor, volunteer or help out a particular channel
- Warnings about a breach of TOS while using a particular channel
- Status updates about the stability of the channel


## Specification

The specification is described below via a question-answer format.

### When will this message be shown?

The notification message will appear while running the following commands:

- `create`
- `env create`
- `install`
- `update`
- `env update`
- `search`

The reasoning behind this decision is that the above commands all retrieve `repodata.json` from the configured
channels. Simply adding another file request (which is very small and immediately cached) would not add much more
overhead to the execution of these commands. Additionally, these are commands where our users already expect network
traffic to occur, so the requirement for having an active internet connection is assumed.

Here's an example of how a notification message may appear while running the `conda create` command:

```
$ conda create -n geopandas geopandas
Collecting package metadata (repodata.json): done
Solving environment: done

## Package Plan ##

  environment location: /Users/username/opt/conda_x86_64/envs/geopandas

  added / updated specs:
    - geopandas

... (output truncated)

Notice [info]:
> Here is a message to the user
> Here is a link they could click: https://example.com/link-name
> To see the message again, run `conda motd`

```

### How else can our users access this message?

Additionally, because our users may wish to see this message on demand, we will add a new sub-command called `motd` or
`notices` or `alerts` (exact name is yet to be determined) The following are a couple examples to show exactly how 
it would function:

**Basic usage:** grabs notifications for all current channels:

```
$ conda alerts

Channel: defaults

Notice [info]:
This is a test message. It is not very long, and could have a link to a longer post:
https://example.com/short-link

Channel: conda-forge

Notice [info]:
Here is another message. It could have info about the latest happenings or blog posts from conda-forge:
https://conda-forge.org/
```

**Show a single channel:** grabs notifications for a single channel:

```
$ conda alerts -c default

Notice [info]:
This is a test message. It is not very long, and could have a link to a longer post:
https://example.com/short-link
```

### What file format will this message have, and what will it contain?

The notification message will be in the JSON file format. This will allow us to not only store the message itself but 
also metadata about the message, including information about how often the client should display the message (more on 
this in the next section).

Here's an example of the `notifications.json` file which will be stored in the root of the channel directory structure.

```json
{
  "notifications": [
    {
      "id": "1cd1d8e5-d96c-42d1-9c29-e8120ad80823",
      "message": "Here is an example message that will be displayed to users",
      "level": "info",
      "created_at": "2022-04-26T11:50:34+00:00",
      "expiry": 604800
    }
  ]
}
```

Detailed overview of the JSON fields:

- **notifications** [Array] holds zero or more notifications that will be displayed to the client.
  - **id** [String] unique ID for the message itself. UUIDs are preferred, but there is no required format.
  - **message** [String] message that gets displayed to users.
  - **level** [String] one of (info|warning|error). These will let our users know the category of the message
    and will also allow the client to apply different formatting rules (e.g. text color).
  - **created_at** [String] ISO 8601 formatted timestamp showing the creation time of the message.
  - **expiry** [Number] a number specifying how long in seconds the message is valid for.

### How often will these messages appear?

How often the messages appears will be configurable by the channel owners and the client. This will be accomplished by 
the expiry field in the `notifications.json` file itself, but the client will the have ultimate say over whether this
message is displayed. We will provide clients with a setting to permanently disable these messages in their `.condarc`
files:

```yaml
display_notifications: false
```

## Motivation

The motivation for this CEP came about as channel owners (Anaconda specifically) needed a way to broadcast messages to
users of their channels. These messages may contain specific notices for particular users (e.g. identified by
IP address) or general messages for the wider audience of a particular channel.

Additionally, this new notification space can also provide a place for us to relocate `conda update conda` reminders 
to a more visible spot (at the end of command output versus in the middle of the output). On top of this, other channels
can use these notifications as a way to share news with their users or "calls for help" in maintaining their channels.


## Rationale

TBD

## Backwards Compatibility

We do not expect any backwards compatibility issues for this new feature.


## Alternatives

- **Show MOTD at the beginning of environment activation** This was deemed a little too intrusive/annoying.
- **Show MOTD at the beginning of command output** Users may miss this if placed here, especially for commands
  with lots of output


## References

This implementation is similar to the way that `npm` handles version update reminders:

```
npm install                                                                                                                   travishathaway@thath-work-laptop

up to date, audited 365 packages in 3s

34 packages are looking for funding
  run `npm fund` for details

5 vulnerabilities (1 moderate, 4 high)

To address all issues (including breaking changes), run:
  npm audit fix --force

Run `npm audit` for details.
npm notice
npm notice New minor version of npm available! 8.5.5 -> 8.7.0
npm notice Changelog: https://github.com/npm/cli/releases/tag/v8.7.0
npm notice Run npm install -g npm@8.7.0 to update!
npm notice
```

## Sample Implementation

*PR Coming soon!*

## FAQ

TBD

## Resolution

TBD

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
