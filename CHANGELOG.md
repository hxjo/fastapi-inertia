# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.0.3 - 2024-10-04
- Chore: unpin fastapi and jinja versions to allow install with latest versions -- @holandes22


## [1.0.2] - 2024-07-19

- Feat: handle serialization / encoding of prop which are of type list
  - this allows passing to inertia, as prop value, a list of models and they will be encoded as expected

## [1.0.1] - 2024-07-18

- Fix: SSR failed when the inertia server responded with an empty array
- Examples: Add examples for both SSR and non-SSR in vue language.

## [1.0.0] - 2024-07-18

- [BREAKING CHANGE] Introduce templating via Jinja2 instead of a raw HTML string
  - For migration guide, see [the migration guide](./DEPRECATION_AND_MIGRATION_GUIDE.md#use-jinja2-template-instead-of-a-raw-html-string)
- [BREAKING CHANGE] Remove deprecated use of `requests`
  - For migration guide, see [the migration guide](./DEPRECATION_AND_MIGRATION_GUIDE.md#requests-package-for-ssr)
- [BREAKING CHANGE] Remove deprecated use of `use_typescript`
  - For migration guide, see [the migration guide](./DEPRECATION_AND_MIGRATION_GUIDE.md#use_typescript-configuration-option)

## [0.1.7] - 2024-07-18

- Deprecate `requests` package for SSR in favour of `httpx` package
  - Removed in 1.0.0
  - For migration guide, see [the migration guide](./DEPRECATION_AND_MIGRATION_GUIDE.md#requests-package-for-ssr)
- Test for deprecation warning for `httpx` package and `use_typescript` configuration option

## [0.1.6] - 2024-07-17

- Cache vite manifest content
- Better type vite manifest
- Allow for multiple css files to be in the manifest file
- Deprecate `use_typescript` in favour of `entrypoint_filename` in InertiaConfig
  - Removed in 1.0.0
  - For migration guide, see [the migration guide](./DEPRECATION_AND_MIGRATION_GUIDE.md#use_typescript-configuration-option)
- Introduce root_directory to InertiaConfig instead of assuming it
- Introduce assets_prefix to InertiaConfig instead of assuming it

## [0.1.5] - 2024-07-17

- Introduce new dev dependency: BeautifulSoup
- Use it instead of manual parsing as this is more reliable and less painful

## [0.1.4] - 2024-05-31

- Handle better JSONification of Pydantic models
  - Use `json.loads(model.model_dump.json())` rather than `model.model_dump()`
    To avoid issues with some common field types (UUID, datetime, etc.)
- Expose a `_render_json` method on inertia to allow easier overriding.

## [0.1.3] - 2024-05-08

- Bump FastAPI version from 0.110.2 to 0.111.0

## [0.1.2] - 2024-04-23

- Update `README.md` and available versions

## [0.1.1] - 2024-04-23

- Initial release.
