# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.4] - 2024-05-31

* Handle better JSONification of Pydantic models
  * Use `json.loads(model.model_dump.json())` rather than `model.model_dump()`
    To avoid issues with some common field types (UUID, datetime, etc.)
* Expose a `_render_json` method on inertia to allow easier overriding.

## [0.1.3] - 2024-05-08

* Bump FastAPI version from 0.110.2 to 0.111.0

## [0.1.2] - 2024-04-23

* Update `README.md` and available versions

## [0.1.1] - 2024-04-23

* Initial release.
