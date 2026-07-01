CEP 2 | Renaming packages
-- | --
Authors | Michael Sarahan
Status | WIP
Discussion | #TODO
Implementation |  

In transitioning to Conda-forge recipes for the Anaconda distribution, we have needed to resolve several package name differences between the conda-forge and defaults channels. There are instances of old defaults names being replaced by conda-forge names, and also instances of conda-forge names being replaced by defaults names.

### Maintaining connections:
Generally, it is sufficient to use metapackages to point from one package name to another. For example, conda-forge uses the boost-cpp name for the boost package, while defaults prefers libboost. The defaults recipe can provide both in one recipe with the {{ pin_subpackage() }} jinja2 function:

```
outputs:
  - name: libboost
    script: install-libboost.sh   # [unix]
    script: install-libboost.bat  # [win]
    requirements:
      build:
        - {{ compiler('c') }}
        - {{ compiler('cxx') }}
      host:
        - icu               # [unix]
        - bzip2             # [unix]
        - zlib

  # Metapackages to mirror conda-forge's name. It is my goal to deprecate
  # these names and eventually stop providing the packages.
  # TODO :: Aim to remove these by Oct 10th 2018.
  - name: boost-cpp
    requirements:
      run:
        - {{ pin_subpackage('libboost', exact=True) }}
```

### Removing metapackages
This CEP is more about what to do after that, though. From the boost example above, Ray left a comment that he'd like to stop providing the boost-cpp metapackage by Oct 10th 2018. Out of concern for reducing workload and freeing up old names that may be desirable, we need a way to deprecate package names, and communicate to people that packages may either go away or change behavior in the future. If they have pins to old versions, they'll be fine. If they are not pinned, their installations or builds may break.

### Proposal:
Add new metadata in meta.yaml:
```
build:
  end_of_life:
    date: YYYY-MM-DD
    reason: split into devel and lib packages; users should choose appropriately
    alternate_packages:
      - somepkg-devel
      - libsomepkg
```
Teach conda about that metadata, and have it show warnings when it is installing a package marked with end_of_life. These warnings should also show up when conda-build is using conda to create environments.

as a general rule, provide 12 months from the date of adding end_of_life metadata until actually replacing that package with something that has different functionality.