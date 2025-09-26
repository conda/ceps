Implicit pin metadata in repodata
---------------------------------

It may be good to specify additional metadata as part of the repodata.json file or the channel specification.

Currently, Python has a special "auto-pinning" behavior where the Python version is pinned to the minor version if it is already present in the environment. This is useful because users usually don't want to move the Python version to frequently and when mixing Python and pip, updating the Python version would break packages previously installed with pip. 
The pip installed packages are ending up in the `lib/python3.X/site-packages` folder (which is python minor version specific).

This behavior is also relevant for `ruby` and potentially other programming languages with language specific package managers that offer compatibility across the minor version. 

Thus it would be good to specify this pinning as part of the metadata of a channel. This could be part of the `repodata.json` file or in another file.