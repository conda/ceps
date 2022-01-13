<table>
<tr><td> Title </td><td> Constructor creates signed installers </td>
<tr><td> Status </td><td> Draft </td></tr>
<tr><td> Author(s) </td><td> Steve Croce &lt;scroce@anaconda.com&gt;</td></tr>
<tr><td> Created </td><td> Dec 21, 2021</td></tr>
<tr><td> Updated </td><td> Jan 12, 2022</td></tr>
<tr><td> Discussion </td><td> NA </td></tr>
<tr><td> Implementation </td><td> To be implemented </td></tr>
</table>

## Abstract

A standard practice (among many) to provide secure software executables and installers is code signing. Both Microsoft and Apple have solutions to this for the Windows and MacOS operating systems, respectively, and in both cases the default operating system behavior is to enforce that only signed/trusted applications can run. To address this requirement for conda-based installers, Anaconda, and others use a post-processing step to sign the installers they distribute. However, it would be beneficial to software security worldwide if Constructor had the ability to automate the signing process for Windows and MacOS, using a provided certificate.

## Motivation

Most modern operating systems require installers and executables to be cryptographically signed. Adding this feature would enable Constructor to be used in more scenarios without requiring a separate, manual step.

Automating this step of the process would enable more users to create signed installers, improving the security of the conda community overall.

## Specification

This change would add the following functionality to Constructor:

    * Add field(s) to the construct.yaml file that accept the paths to the appropriate certificates per platform
    * Add command line options and/or contruct.yaml settings to determine whether created installers are signed
    * Add any metadata or format changes expected by the operating system to the created installer to recognize the package signature
    * Wrap, call externally, import as a module, or implement internally the function to sign the package in accordance with the operating system's requirements.

An ideal solution here, though perhaps not technically feasible, would also enable the creation of signed installers for all platforms from any platform (i.e. A linux user can create signed Windows/MacOS installers. A MacOS user can create signed Windows installers in addition to MacOS installers).

### MacOS Specifics

**Certificates:** Constructor should be able to accept a path to an Apple developer certificate (.p12) as an input, or (optionally) a keychain location for the developer certificate

**Notarization:** Though notarizing the installer in addition to signing it would be a great enhancement, it is out of scope for this CEP

**Signing Format:** Installers should comply with and only need to support Apple’s current signature format with Distinguished Encoding Rules (DER). Supporting older formats should be out of scope.

### Windows Specifics

**Certificates:** Constructor should be able to accept a path to a certificate in Personal Information Exchange (.pfx) format as an input as well as the password for that certificate, if password protected. Optionally, a certificate stored in the certificate store and identified by Subject Name or SHA1 hash could be supported, but not required.

**Hash Algorithm:** Constructor should handle determination and management of hash algorithm for building the installer and using in the signing process.

### Prerequisites

In order to sign packages, it is acceptable for constructor to require:

    * That the user has already acquired the certificate and/or developer account required to sign the installer per target platform
    * The user is able to provide links/access to properly signed certificates in the appropriate formats (p12/pfx)
    * The user has access to the machine type that an installer is being signed for (i.e. a MacOS machine for signed MacOS installers). Ideally, we can remove this restriction, but that’s to be determined.

## Reference

    * https://developer.apple.com/documentation/xcode/using-the-latest-code-signature-format
    * https://docs.microsoft.com/en-us/windows/msix/package/sign-app-package-using-signtool

## Copyright

All CEPs are explicitly [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
