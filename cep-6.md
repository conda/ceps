<table>
    <tr><td> Title </td><td>Add Channel Notices to conda</td>
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
- Announcements for planned security releases

## Specification

The specification is described below via a question-answer format.

### When will this message be shown?

The notification message will appear while running the following commands:

- `create`
- `env create`
- `env update`
- `install`
- `update`

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


Channel "defaults" has the following notices:
  [info] -- Tue May 10 11:50:34 2022
  This is a test message. It is not very long, and could have a link to a longer post:
  https://example.com/short-link
  
```

### How else can our users access this message?

Additionally, because our users may wish to see this message on demand, we will add a new sub-command called `notices`. 
The following are a couple examples to show exactly how it would function:

**Basic usage:** grabs notices for all current channels:

```
$ conda notices

Retrieving notices: done

Channel "defaults" has the following notices:
  [info] -- Tue May 10 11:50:34 2022
  This is a test message. It is not very long, and could have a link to a longer post:
  https://example.com/short-link

Channel "conda-forge" has the following notices:
  [info] -- Tue May 10 11:50:34 2022
  Here is another message. It could have info about the latest happenings or blog posts from conda-forge:
  https://conda-forge.org/
```

**Show a single channel:** grabs notices for a single channel:

```
$ conda notices -c defaults

Channel "defaults" has the following notices:
  [info] -- Tue May 10 11:50:34 2022
  This is a test message. It is not very long, and could have a link to a longer post:
  https://example.com/short-link
```

### What file format will this message have, and what will it contain?

The notification message will be in the JSON file format. This will allow us to not only store the message itself but 
also metadata about the message, including information about how often the client should display the message (more on 
this in the next section).

Here's an example of the `notices.json` file which will be stored in the root of the channel directory structure.

```json
{
  "notices": [
    {
      "id": "1cd1d8e5-d96c-42d1-9c29-e8120ad80823",
      "message": "Here is an example message that will be displayed to users",
      "level": "info",
      "created_at": "2022-04-26T11:50:34+00:00",
      "expiry": 604800,
    }
  ]
}
```

Detailed overview of the JSON fields:

- **notices** [Array] holds zero or more notices that will be displayed to the client.
  - **id** [String] unique ID for the message itself. UUIDs are preferred, but there is no required format.
  - **message** [String] message that gets displayed to users.
  - **level** [String] one of (info|warning|critical). These will let our users know the category of the message
    and will also allow the client to apply different formatting rules (e.g. text color).
  - **created_at** [String] ISO 8601 formatted timestamp showing the creation time of the message.
  - **expiry** [Number] starting at `created_at`, a number specifying how long in seconds the message is valid for.

### How often will these messages appear?

How often the messages appear will be configurable by the channel owners and the client. This will be accomplished by 
the expiry field in the `notices.json` file itself, but the client will the have ultimate say over whether this
message is displayed. We will provide clients with a setting to permanently disable these messages in their `.condarc`
files:

```yaml
# Zero messages will be displayed while running commands such as "install", "update", etc.
number_channel_notices: 0
```

## Motivation

The motivation for this CEP came about as channel owners (Anaconda specifically) needed a way to broadcast messages to
users of their channels. These messages may contain specific notices for particular users (e.g. identified by
IP address) or general messages for the wider audience of a particular channel.

Additionally, this new notification space can also provide a place for us to relocate `conda update conda` reminders 
to a more visible spot (at the end of command output versus in the middle of the output). On top of this, other channels
can use these notices as a way to share news with their users or requests for help in maintaining their channels.


## Rationale

TBD


## Backwards Compatibility

We do not expect any backwards compatibility issues for this new feature.


## Alternatives

- **Show notices at the beginning of environment activation:** This was deemed too intrusive/annoying.
- **Show notices at the beginning of command output:** Users may miss this if placed here, especially for commands
  with lots of output
- **Message in an HTTP header when retrieving any file from the repository:** This would be a better option for some kinds 
  of messages, like download rate limiting or other blocks due to abuse, since it could be turned on by a rule in a CDN.
  However, this use case is probably better addressed by having a standard way for `conda` to display errors on the 
  console from HTTP status codes like 429 (Too Many Requests) and 403 (Forbidden). Additionally, serving custom headers
  is challenging unless the repository owner has more control over the web server than is usually given by services 
  like Github Pages.
- **Add notices to the repodata.json file:** The repodata.json file is already being fetched, so adding some
  notices would reduce the number of requests. However, the repodata.json file is way too big already, so it 
  would require clients to download a fairly large file before even being able to show the notification.
- **Create a generic metadata.json file containing a notices key:** This could be appealing for
  creating a space for other kinds of channel metadata, but in order to keep things as simple as possible at the moment
  it makes more sense to put these in their own file. Plus, it allows more flexibility for dynamic routing options
  to this file if that becomes necessary in the future.


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

## Implementation

Pull request to the full implementation:

https://github.com/conda/conda/pull/11462

Please add any implementation related suggestions for improvements to this pull request.

## FAQ

### How often will I see notices?

Notices will be shown however often channel owners would like. Users will also be able to disable channel
notices completely in order to never see them during normal operation.

### Is this opt-in or opt-out?

Users will automatically be opted in to these feature. They will have the ability to turn it off via
a configuration parameter.


## Resolution

TBD

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
