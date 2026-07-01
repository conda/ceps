<table>
<tr><td> Title </td><td> Authentication support in conda </td>
<tr><td> Status </td><td> Proposed </td></tr>
<tr><td> Author(s) </td><td> Steve Croce &lt;scroce@anaconda.com&gt;</td></tr>
<tr><td> Created </td><td> Dec 29, 2021</td></tr>
<tr><td> Updated </td><td> Jan 12, 2022</td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> To be implemented </td></tr>
</table>

## Abstract

An integrated and pluggable authentication mechanism should be added to conda that allows conda to handle login/authentication with a repo, securely store any keys/tokens/secrets, then provide credentials with repo requests. Though a reference implementation (e.g. HTTP basic authentication) should be created as part of the initial work, the authentication system should be pluggable to support other authentication mechanisms.

## Motivation

The need for authenticated access to a repository is well established and numerous products from Anaconda alone provide this feature today. However, each product handles authenticated access to repos slightly differently (see references 1-4), so there are numerous additional commands and tools used to handle the login, token management, and repo access portions.

The ability to send credentials along with repo requests is also a common request within conda's Github issues (see references 5-7). There are workarounds for basic auth (credentials in repo URL, .netrc file), but no complete and secure solution that enables conda users to connect to protected repos.

Finally, there is no common mechanism for users to create their own secure repos, outside of anaconda.org. Built-in authentication in conda would lower the bar and enable more users to create a protected repository.

## Specification

Initial implementation should focus on a ubiquitous standard that's straightforward to implement, like HTTP basic authentication. However, the solution should be pluggable/expandable to support other standards like OAuth2 and SAML.

This enhancement should focus on three main capabilities:

1. **Authenticated repo requests:** conda should be able to provide authentication credentials/tokens/session information along with all repo requests (generally via HTTP headers).
2. **Authenticated repo configuration and management:** conda should provide a secure mechanism to store/retrieve credentials so they only need to be provided when a channel/repo is added. Users should be able to provide credentials per channel and conda should be able to determine the appropriate credentials to provide for each repo request.
3. **Session Management:** For authentication mechanisms that require it, conda should handle any kind of session management that would be required to keep a user logged in and securely store secrets/keys/tokens in such a way that a local user can extract them.

In the case of basic auth, an example flow would be:

1. User adds a new channel along with the credentials to access it. Proposed options for providing credentials:
    - retrieved from environment variables
    - set in a configuration file, like `.condarc`, or separate new file that specifies auth type and credentials per channel.
    - a new conda command that adds a channel (e.g. `conda login <channel>`) with a prompt for credentials when trying to log in.
2. Credentials are stored along with channel configuration in a secure way such that the user only needs to enter credentials again if the credentials change, or the user has logged out/removed the credentials from conda.
3. User performs a conda command (e.g. `conda install`) the command proceed without user intervention to provide credentials.
    - When performing a conda command that connects to an authenticated repo, conda determines whether credentials have been provided for that repo and attaches them to the request
    - If auth fails, retries/reenter credentials could be attempted
4. Command completes and conda reports back any auth issues in the process

### Design Goals

1. **Pluggability:** Any solution here should be pluggable and expandable.
2. **Credentials stored securely:** Any entered credentials are able to be stored securely such that someone with non-privileged access on the machine cannot retrieve them, and we steer away from bad practices (passwords in plaintext config files, etc.)
3. **No credentials in logs:** No credentials are leaked into logs as well, even if provided in the URL.
4. **Credentials per channel:** A user can configure credentials per channel and conda is able to manage those credentials and provide the right credentials to each repo when making requests.

### Assumptions

1. **Server handles authorization:** Simply stated, conda authenticates with the server and per repo request, the server is responsible for determining what the user can and cannot do.


## Reference

    1. https://docs.anaconda.com/anaconda-commercial/quickstart/#auth-ce
    2. https://team-docs.anaconda.com/en/latest/user/cli.html#logging-in
    3. https://docs.anaconda.com/anacondaorg/user-guide/tasks/work-with-accounts/#creating-access-tokens
    4. https://enterprise-docs.anaconda.com/en/latest/install/ae-cli.html
    5. https://github.com/conda/conda/issues/6969
    6. https://github.com/conda/conda/issues/9973
    7. https://github.com/conda/conda/issues/1784


## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
