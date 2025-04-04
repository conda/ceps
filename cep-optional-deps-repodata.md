CEP Optional Dependencies
=========================

I am proposing to add a way to specify conditional / optional dependencies as part of the next iteration of repodata.json.

This is useful for two scenarios:

- noarch packages that depend on some platform specific packages
- easily install additional optional dependencies 

My proposal enhances repodata.json with a syntax as follows:

Noarch packages with platform specific deps
-------------------------------------------

Sometimes noarch packages need platform specific packages (win / unix).
One often seen example is `pywin32` which is only needed on Windows.

A workaround has been to create an empty "shim" package for the other platforms.

There is a similar issue with python dependencies like `dataclasses` that were only necessary 
up to a certain python version. However, in that case it's more difficult to know the python version
before solving, so I am refraining from adding a `[py<37]` syntax.
This could be done with a two stage solve, though.

```json
depends: [
	"xtensor >=0.21.2",
	"[win]pywin32 >=0.5",
	"[unix]pyunix >=2"
]
```

Optional dependencies
---------------------

Having this ability in repodata.json could enable us to create packages with optional dependencies.
For example, we could have the quetz package server in multiple "variants" that are only different
by dependencies.

```json
depends: [
...
	"sqlite >=3.2",
	"[postgres]postgresql 5.*"
	"[postgres]psycopg",
	"[gcs]gcsfs >=2021.10.1",
	"[azure]adlfs >=2021.10.0",
	"[s3]s3fs >=2021.10.1"
]
```

A user could then install the desired variants by calling `install quetz[postgres, gcs]`.
This would be even more useful if a variant is dependent on a set of additional packages.

