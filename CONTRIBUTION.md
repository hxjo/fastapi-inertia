# Contribution guide

First of all, thank you for checking this out.
I appreciate everyone's work and everyone's effort to make this package better.

## Documentation

### Code documentation
Every function and class must be properly documented.
All parameters should be documented, as well as the return type.

In addition to this, you should always use type annotation and 
avoid `Any` types as much as possible.

### User documentation
If a new exposed behaviour is being introduced, you should update the README.md
accordingly.
You must also update the examples folder accordingly, both for classic and SSR if relevant.


If a breaking change is introduced, it must be introduced in two steps:
1. Deprecation
  In this step, you must ensure the app remain completely functional, and mark the 
  usage as deprecated.
2. Removal
  In this step, you must remove the previous implementation, and write a guide in the 
  DEPRECATION_AND_MIGRATION_GUIDE.md

### Changes documentation
Once you're done with your work, you must add an entry to the CHANGELOG.md, describing 
your changes.


## Tests

Every new code must be thoroughly tested, both on the happy and unhappy path, 
if no test covers it already.
The code coverage limit is set to 98%.


## Versioning

This repository adheres to semantic versioning. 
It is vital to respect it, and to not introduce a breaking change without a major update.
Every pull request must come with a bump of the version specified in the `pyproject.toml`,
so a new version can properly be deployed.

## Tools

This project uses [poetry](https://python-poetry.org/docs/) to handle dependencies and local environment.
This project uses [poethepoet](https://poethepoet.natn.io/index.html) to define some useful tasks for the project.
You can use them, after having activated your environment, through `poe ${command_name}`
If you find yourself missing a command, feel free to add and document it.
