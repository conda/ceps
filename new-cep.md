# Conda Release Process Proposal

| Title                | Conda Release Process                          |
| -------------------- | ---------------------------------------------- |
| Status               | Draft                                          |
| Author(s)            | Dan Meador dan@anaconda.com>                |
| Created              | April 19, 2023                                 |
| Updated              | April 19, 2023                                 |
| Discussion           | NA                                             |
| Implementation       | NA                                             |

## Abstract

This proposal aims to establish a clear and efficient release process for conda (and other conda projects) by implementing a pilot and co-pilot system, ensuring a smooth transfer of responsibilities between team members and the continuous improvement of release quality. There will also be one "jump seat" available for those that want to sit in and observe the release process, but not be responsible for any of it.

## Specification

* Each bi-monthyl (every two month) release will have a pilot and a co-pilot.(See [CEP-8](https://github.com/conda-incubator/ceps/blob/main/cep-8.md))
* The pilot is the primary person responsible for the release, while the co-pilot provides assistance and fills in for the pilot when they are absent.
* Team members will switch roles from pilot to co-pilot from one release to the next, serving for three consecutive releases.
* The pilot and co-pilot will be responsible for the release of a given conda (or another conda project) version.
* A "jump seat" will be available for those that want to sit in and observe the release process, but not be responsible for any of it. 

### Rotation

Release 1: Pilot: **Bob Ross(new)**, Co-pilot: **Jane Doe(new)**

Release 2: Pilot: Jane Doe, Co-pilot: Bob Ross

Release 3: Pilot: Jane Doe, Co-pilot: **Tobby Smith(new)**

Release 4: Pilot: Tobby Smith, Co-pilot: Jane Doe

Release 5: Pilot: Tobby Smith, Co-pilot: **Elvis Presley(new)**

[pilots_conda](https://user-images.githubusercontent.com/6708083/233211589-10bca344-141e-407a-8edc-ca39014605eb.png)

### Pilot Responsibilities

* Responsible and accountable for the release of a given conda (or another conda project) version.
* Ensure that users are able to successfully update to the latest version and that no critical bugs or issues arise as part of the release.
* Be the known go-to liaison if there is a potentially critical issue, and take point in addressing/fixing it.
* Responsible for getting the co-pilot prepared to be a pilot by being a teacher and ensuring that they will be able to take over the process next time.

### Co-pilot Responsibilities

* Responsible for certain roles or activities for a given conda (or another project) version.
* Be an extra set of eyes to help the pilot get to the correct outcome.
* Help with communication with the team and the broader community.
* Learn as an active participant in the process, not meant to simply be "on deck" for the next time.

### Jump seat Responsibilities
* None. This is simply for someone that wants to just be along for the ride and learn by observing. This is not meant to be a "backup" or "on deck" role. This is an intentional choice in order to prevent the "too many cooks in the kitchen" problem as even though there might be good intentions, it can be distracting and confusing to have too many people involved in the process. With all that said there is benefits to allowing someone to just sit in and observe, so this is a compromise as this isn't meant to be a secret process, but it is meant to be a focused process as issues can arise at any time and the pilot and co-pilot need to be able to focus on the task at hand.

### Special Note for Previous Pilots

* If you are coming from being the pilot on the previous release, then make sure to help and guide the current pilot if there are any questions that come up.

## Motivation

The proposed release process is necessary to ensure a high-quality, consistent, and efficient release cycle for conda and related projects. The pilot and co-pilot system encourages knowledge transfer, collaboration, and continuous improvement.

## Rationale

The pilot and co-pilot model has been proven to work well in other projects, ensuring that there is always at least one person with the necessary experience and knowledge to handle releases, while also providing opportunities for other team members to learn and grow. This inspiration came from seeing how PyCon US has run their conference where the same city runsthe conference twice in a row, with the second year providing an opportunity for the next years city to learn from the previous years city.

## Alternatives

1. Have a dedicated release manager role, but this would limit the opportunities for team members to learn and grow, and it may create a single point of failure if the release manager becomes unavailable.

## Sample Implementation

N/A

## FAQ

Q) Who can be a Pilot/copilot on a release?
A) Must be a core conda team member.

Q) Conda broke on a Saturday due to a late Friday release, who should fix it? 

A) The pilot is accountable for ensuring that critical conda issues due to the release are addressed. We simply have too many users that could be in an unusable state to not address this. Its recommended that we don’t release on a Friday for this reason. 

Q) How long should we wait to give the “all clear” that the release didn’t break anything?

A) 

Q) I am in the rotation but would like out, how can do that?

A) If for whatever reason you can’t be the pilot/copilot for a release, then let the respective team members (Pilot or copilot) know with as much heads up as possible so a replacement can be found.

## Resolution


