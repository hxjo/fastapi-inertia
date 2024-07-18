# Deprecated features and migration guide

- [Deprecated features and migration guide](#deprecated-features-and-migration-guide)
  - [`use_typescript` configuration option](#use_typescript-configuration-option)
    - [Migration guide](#migration-guide)
  - [`requests` package for SSR](#requests-package-for-ssr)
    - [Migration guide](#migration-guide-1)
  - [Use Jinja2 Template instead of a raw HTML string](#use-jinja2-template-instead-of-a-raw-html-string)
    - [Migration guide](#migration-guide-2)

> [!WARNING]  
> The items mentioned in this part are deprecated and will be removed in a future version.

## `use_typescript` configuration option

The `use_typescript` configuration option has been deprecated in favour of `entrypoint_filename`.  
It has been done for the following reason(s):

- To ensure library users are not restricted to the `main.{ext}` pattern when it comes to the entrypoint

### Migration guide

- Remove the `use_typescript` from your configuration options
- Add the `entrypoint_filename` option to the configuration ; the value would be `main.ts` if it is your webapp entrypoint's filename.

## `requests` package for SSR

The `requests` package requirement has been changed for a `httpx` package requirement.  
It has been done for the following reason(s):

- To leverage the async capabilities of httpx.AsyncClient

### Migration guide

- Install the `httpx` package
- (Optionally, if not used elsewhere in your application) Remove the `requests` package

## Use Jinja2 Template instead of a raw HTML string

Remove the usage of raw HTML strings in favour of Jinja2Templates.  
It has been done for the following reason(s):

- So that library users can customize the HTML more easily, without having to override the Inertia object.

### Migration guide

- Create a Jinja2Templates instance, for example one from `fastapi.templating.Jinja2Templates`. Ensure you have a valid inertia template in the directory given to the instance.
- Pass this instance to the InertiaConfig, under the `templates` key
- Pass the inertia template filename to the InertiaConfig, under the `root_template_filename` key
