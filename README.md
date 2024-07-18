# Inertia.js FastAPI Adapter

<!-- TOC -->

- [Inertia.js FastAPI Adapter](#inertiajs-fastapi-adapter)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Examples](#examples)
  - [Usage](#usage)
    - [Create a Jinja2Template](#create-a-jinja2template)
    - [Set up the dependency](#set-up-the-dependency)
    - [Rendering a page](#rendering-a-page)
    - [Rendering assets](#rendering-assets)
    - [Sharing data](#sharing-data)
    - [Flash messages](#flash-messages)
    - [Flash errors](#flash-errors)
    - [Redirect to an external URL](#redirect-to-an-external-url)
    - [Redirect back](#redirect-back)
    - [Enable SSR](#enable-ssr)
  - [Frontend documentation](#frontend-documentation)
    - [For a classic build](#for-a-classic-build)
    - [For a SSR build](#for-a-ssr-build)
    - [Performance note](#performance-note)

## Installation

You can install the package via pip:

```bash
pip install fastapi-inertia
```

## Configuration

You can configure the adapter by passing a `InertiaConfig` object to the `Inertia` class.
The following options are available:

| key                    | default                | options                                 | description                                                                                                                                  |
| ---------------------- | ---------------------- | --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| environment            | development            | development,production                  | The environment to use                                                                                                                       |
| version                | 1.0.0                  | Any valid string                        | The version of your server                                                                                                                   |
| json_encoder           | InertiaJsonEncoder     | Any class that extends json.JSONEncoder | The JSON encoder used to encode page data when HTML is returned                                                                              |
| manifest_json_path     | ""                     | Any valid path                          | The path to the manifest.json file. Needed in production                                                                                     |
| dev_url                | http://localhost:5173  | Any valid url                           | The URL to the development server                                                                                                            |
| ssr_url                | http://localhost:13714 | Any valid url                           | The URL to the SSR server                                                                                                                    |
| ssr_enabled            | False                  | True,False                              | Whether to [enable SSR](#enable-ssr). You need to install the `httpx` package, to have set the manifest_json_path and started the SSR server |
| root_directory         | src                    | Any valid path                          | The directory in which is located the javascript code in your frontend. Will be used to find the relevant files in your manifest.json.       |
| entrypoint_filename    | main.js                | Any valid file                          | The entrypoint for you frontend. Will be used to find the relevant files in your manifest.json.                                              |
| assets_prefix          | ""                     | Any valid string                        | An optional prefix for your assets. Will prefix the links generated from the assets mentioned in manifest.json.                              |
| use_flash_messages     | False                  | True,False                              | Whether to use [flash messages](#flash-messages). You need to use Starlette's SessionMiddleware to use this feature                          |
| flash_message_key      | messages               | Any valid string                        | The key to use for [flash errors](#flash-errors)                                                                                             |
| use_flash_errors       | False                  | True,False                              | Whether to use flash errors                                                                                                                  |
| flash_error_key        | errors                 | Any valid string                        | The key to use for flash errors                                                                                                              |
| templates              | None                   | A Jinja2Templates instance              | The templates instance in which Inertia will look for the `root_template_filename` template                                                  |
| root_template_filename | index.html             | Any valid jinja2 template file          | The file which will be used to render your inertia application                                                                               |

## Examples

You can see different full examples in the `examples` directory

## Usage

### Create a Jinja2Template

In order to use the Inertia.js adapter, you have to create a Jinja2Template that the library will use.

It **must** have both an `inertia_head` and an `inertia_body` tag in it.

- `inertia_head` is where the library will place the code that supposedly goes inside the HTML `head` tag
- `inertia_body` is where the library will place the code that supposedly goes inside the HTML `body` tag

You can find the simplest example in `inertia/tests/templates/index.html`.  
You should then register the folder in which you put this file as the directory of your Jinja2Templates

```python
templates = Jinja2Templates(directory=template_dir)
```

This option should be passed to the InertiaConfig class presented below, under the `templates` key.
If you choose a different template file name than `index.html`, you can also pass the `root_template_filename` key with, as value, your template file name.

### Set up the dependency

This Inertia.js adapter has been developed to be used as a FastAPI dependency.
To use it, you first need to set up the dependency, with your desired configuration.

`inertia_dependency.py`

```python
from fastapi import Depends
from typing import Annotated
from inertia import InertiaConfig, inertia_dependency_factory, Inertia

inertia_config = InertiaConfig(
        # Your desired configuration
    )

inertia_dependency = inertia_dependency_factory(
    inertia_config
)

InertiaDependency = Annotated[Inertia, Depends(inertia_dependency)]
```

You can then access the `InertiaDependency` in your route functions, and use it to render your pages.

### Rendering a page

To render a page, you can use the `render` method of the `Inertia` class. It takes two arguments:

- The name of the page
- The data to pass to the page

`main.py`

```python
from fastapi import FastAPI, Depends
from inertia import InertiaResponse, InertiaVersionConflictException, inertia_version_conflict_exception_handler
from inertia_dependency import InertiaDependency

app = FastAPI()

app.add_exception_handler(InertiaVersionConflictException, inertia_version_conflict_exception_handler)

@app.get('/', response_model=None)
async def index(inertia: InertiaDependency) -> InertiaResponse:
     return inertia.render('Index', {
          'name': 'John Doe'
     })
```

### Rendering assets

As your front-end framework likely references assets that are not served by FastAPI,
you need to mount a static directory to serve these assets.

`main.py`

```python
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from inertia_dependency import inertia_config


app = FastAPI()
webapp_dir = (
    os.path.join(os.path.dirname(__file__), "..", "webapp", "dist")
    if inertia_config.environment != "development"
    else os.path.join(os.path.dirname(__file__), "..", "webapp", "src")
)

app.mount("/src", StaticFiles(directory=webapp_dir), name="src")
app.mount(
    "/assets", StaticFiles(directory=os.path.join(webapp_dir, "assets")), name="assets"
)
```

### Sharing data

To share data, in Inertia, is basically to add data before even entering your route.
This is useful, for example, to add a user to all your pages that expects your user to be logged in.

`main.py`

```python
from fastapi import FastAPI, Depends
from inertia import InertiaResponse, InertiaVersionConflictException, inertia_version_conflict_exception_handler
from inertia_dependency import InertiaDependency

app = FastAPI()

app.add_exception_handler(InertiaVersionConflictException, inertia_version_conflict_exception_handler)

def current_user(inertia: InertiaDependency):
    inertia.share(user={
        'name': 'John Doe'
    })

@app.get('/', response_model=None, dependencies=[Depends(current_user)])
async def index(inertia: InertiaDependency) -> InertiaResponse:
    """
    Because of the dependency, and as we are sharing the user data, the user data will be available in the page.
    """
    return inertia.render('Index')
```

### Flash messages

With the inertia dependency, you have access to a `flash` helper method that allows you to add flash messages to your pages.
This is useful to display messages to the user after a form submission, for example.
Those messages are called `flash` messages as they are only displayed once.  
You need to have set `use_flash_messages` to `True` in your configuration to use this feature.
You need to have the `SessionMiddleware` enabled in your application to use this feature.

`main.py`

```python
from fastapi import FastAPI, Depends
from starlette.middleware.sessions import SessionMiddleware
from inertia import InertiaResponse, InertiaVersionConflictException, inertia_version_conflict_exception_handler
from inertia_dependency import InertiaDependency

app = FastAPI()

app.add_exception_handler(InertiaVersionConflictException, inertia_version_conflict_exception_handler)
app.add_middleware(SessionMiddleware, secret_key="secret")


@app.get('/', response_model=None)
async def index(inertia: InertiaDependency) -> InertiaResponse:
    inertia.flash('Index was reached successfully', category='success')
    return inertia.render('Index')
```

### Flash errors

If you handle form submissions in your application, and if you do all validation at the pydantic level,
a malformed payload will raise a `RequestValidationError` exception.
You can use the `inertia_request_validation_exception_handler` to handle this exception and display the errors to the user.
It supports error bags, so you can display multiple errors at once.
If the request is not from Inertia, it will fallback to FastAPI's default error handling.  
In order to use this feature, you need to have set `use_flash_errors` to `True` in your configuration.
You also need to have the `SessionMiddleware` enabled in your application to use this feature.

`main.py`

```python
from fastapi import FastAPI, Depends
from pydantic import BaseModel, model_validator
from typing import Any
from fastapi.exceptions import RequestValidationError
from starlette.middleware.sessions import SessionMiddleware
from inertia import InertiaResponse, InertiaVersionConflictException, inertia_version_conflict_exception_handler, inertia_request_validation_exception_handler
from inertia_dependency import InertiaDependency

app = FastAPI()

app.add_exception_handler(InertiaVersionConflictException, inertia_version_conflict_exception_handler)
app.add_exception_handler(RequestValidationError, inertia_request_validation_exception_handler)
app.add_middleware(SessionMiddleware, secret_key="secret")


class Form(BaseModel):
    name: str

    @model_validator(mode="before")
    @classmethod
    def name_must_contain_doe(cls, data: Any):
        if 'Doe' not in data.name:
            raise ValueError('Name must contain Doe')

@app.post('/', response_model=None)
async def index(data: Form, inertia: InertiaDependency) -> InertiaResponse:
    return inertia.render('Index')
```

### Redirect to an external URL

If you want to redirect the user to an external URL, you can use the `location` method of the `Inertia` class.
It takes one argument: the URL to redirect to.

`main.py`

```python
from fastapi import FastAPI, Depends
from inertia import InertiaResponse, InertiaVersionConflictException, inertia_version_conflict_exception_handler
from inertia_dependency import InertiaDependency

app = FastAPI()
app.add_exception_handler(InertiaVersionConflictException, inertia_version_conflict_exception_handler)

@app.get('/', response_model=None)
async def index(inertia: InertiaDependency) -> InertiaResponse:
    return inertia.location('https://google.fr')
```

### Redirect back

If you want to redirect the user back (for example, after a form submission), you can use the `back` method of the `Inertia` class.
It will use the `Referer` header to redirect the user back.
If you're on a `GET` request, the status code will be `307`. Otherwise, it will be `303`.
That ways, it will trigger a new GET request to the referer URL.

`main.py`

```python
from fastapi import FastAPI, Depends
from inertia import InertiaResponse, InertiaVersionConflictException, inertia_version_conflict_exception_handler
from inertia_dependency import InertiaDependency

app = FastAPI()
app.add_exception_handler(InertiaVersionConflictException, inertia_version_conflict_exception_handler)

@app.get('/', response_model=None)
async def index(inertia: InertiaDependency) -> InertiaResponse:
    return inertia.back()
```

### Enable SSR

To enable SSR, you need to set `ssr_enabled` to `True` in your configuration.
You also need to have set the `manifest_json_path` to the path of your `manifest.json` file.
You need to have the `httpx` package installed to use this feature.
This can be done through the following command:

```bash
pip install httpx
```

## Frontend documentation

There is no particular caveats to keep in mind when using this adapter.
However, here's an example of how you would set up your frontend to work with this adapter.

### For a classic build

> [!NOTE]  
> To build the project, you can run the `vite build` command

`vite.config.js`

```javascript
import { fileURLToPath } from "node:url";
import { dirname } from "path";

import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

const projectRoot = dirname(fileURLToPath(import.meta.url));
// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": `${projectRoot}/src`,
    },
  },
  build: {
    manifest: "manifest.json",
    outDir: "dist",
    rollupOptions: {
      input: "src/main.js",
    },
  },
});
```

`main.js`

```javascript
import { createApp, h } from "vue";
import { createInertiaApp } from "@inertiajs/vue3";

createInertiaApp({
  resolve: (name) => {
    const pages = import.meta.glob("./Pages/**/*.vue", { eager: true });
    return pages[`./Pages/${name}.vue`];
  },
  setup({ el, App, props, plugin }) {
    createApp({ render: () => h(App, props) })
      .use(plugin)
      .mount(el);
  },
});
```

### For a SSR build

> [!NOTE]  
> To build the project, you can run the `vite build` and `vite build --ssr` commands  
> To serve the Inertia SSR server, you can run the `node dist/ssr/ssr.js` command

`vite.config.js`

```javascript
import { fileURLToPath } from "node:url";
import { dirname } from "path";

import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

const projectRoot = dirname(fileURLToPath(import.meta.url));
// https://vitejs.dev/config/
export default defineConfig(({ isSsrBuild }) => ({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": `${projectRoot}/src`,
    },
  },
  build: {
    manifest: isSsrBuild ? false : "manifest.json",
    outDir: isSsrBuild ? "dist/ssr" : "dist/client",
    rollupOptions: {
      input: isSsrBuild ? "src/ssr.js" : "src/main.js",
    },
  },
}));
```

`main.js`

```javascript
import { createSSRApp, h } from "vue";
import { createInertiaApp } from "@inertiajs/vue3";

createInertiaApp({
  resolve: (name) => {
    const pages = import.meta.glob("./Pages/**/*.vue", { eager: true });
    return pages[`./Pages/${name}.vue`];
  },
  setup({ el, App, props, plugin }) {
    createSSRApp({ render: () => h(App, props) })
      .use(plugin)
      .mount(el);
  },
});
```

`ssr.js`

```javascript
import { createInertiaApp } from "@inertiajs/vue3";
import createServer from "@inertiajs/vue3/server";
import { renderToString } from "@vue/server-renderer";
import { createSSRApp, h } from "vue";

createServer((page) =>
  createInertiaApp({
    page,
    render: renderToString,
    resolve: (name) => {
      const pages = import.meta.glob("./Pages/**/*.vue", { eager: true });
      return pages[`./Pages/${name}.vue`];
    },
    setup({ App, props, plugin }) {
      return createSSRApp({
        render: () => h(App, props),
      }).use(plugin);
    },
  })
);
```

### Performance note

With the implementation proposed above, you'll be loading the whole page on the first load.
This is because everything will be bundled in the same file.
If you want to split your code, you can use the following implementation.

`helper.js` (taken from [laravel vite plugin inertia helpers](https://github.com/laravel/vite-plugin/blob/1.x/src/inertia-helpers/index.ts))

```javascript
export async function resolvePageComponent<T>(
  path: string | string[],
  pages: Record<string, Promise<T> | (() => Promise<T>)>
): Promise<T> {
  for (const p of Array.isArray(path) ? path : [path]) {
    const page = pages[p];

    if (typeof page === "undefined") {
      continue;
    }

    return typeof page === "function" ? page() : page;
  }

  throw new Error(`Page not found: ${path}`);
}
```

`main.js`

```javascript
import { createApp, h } from "vue";
import { createInertiaApp } from "@inertiajs/vue3";
import { resolvePageComponent } from "@/helper.js";

createInertiaApp({
  resolve: (name) => {
    return resolvePageComponent(
      `./Pages/${name}.vue`,
      import.meta.glob("./Pages/**/*.vue")
    );
  },
  setup({ el, App, props, plugin }) {
    createApp({ render: () => h(App, props) })
      .use(plugin)
      .mount(el);
  },
});
```
