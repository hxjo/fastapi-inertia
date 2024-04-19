# For Vue
## Init vue project

```bash
npm create vue@latest
```
(Of course, don't install vue-router)

## Edit the vite config so a manifest.json is generated
```js
export default defineConfig({
    // ...
    build: {
        manifest: 'manifest.json',
    }
})
```

## Install Inertia-vue
```bash
npm install @inertiajs/vue3
```

## Setup Inertia
```js
import './assets/index.css'

import { createApp, h } from 'vue'
import { createInertiaApp } from '@inertiajs/vue3'

createInertiaApp({
  resolve: name => {
    const pages = import.meta.glob('./Pages/**/*.vue', { eager: true })
    return pages[`./Pages/${name}.vue`]
  },
  setup({ el, App, props, plugin }) {
    createApp({ render: () => h(App, props) })
      .use(plugin)
      .mount(el)
  },
})
```

## Create one file in the `src/Pages` folder
```vue
<script setup>
const props = defineProps({
    message: String
})
  console.log(props.message)
</script>
<template>
    <h1>{{ message }}</h1>
    <p>My first Inertia app!</p>
</template>
```

# For FastAPI
## Setup and use Inertia in the FastAPI app

```python
import os
from fastapi import FastAPI, Depends
from typing import Annotated
from fastapi.staticfiles import StaticFiles
from .inertia import (  # noqa
    InertiaResponse,
    InertiaRenderer,
    inertia_exception_handler,
    InertiaVersionConflictException,
)  

app = FastAPI()

# Add the exception handler for the version conflict
app.add_exception_handler(InertiaVersionConflictException, inertia_exception_handler)

# Add the InertiaRenderer dependency
InertiaDep = Annotated[
    InertiaRenderer, Depends(InertiaRenderer)
]

# Mount the src and assets folders as static files
vue_dir = os.path.join(os.path.dirname(__file__), "..", "vue", "src")

app.mount("/src", StaticFiles(directory=vue_dir), name="src")
app.mount(
    "/assets", StaticFiles(directory=os.path.join(vue_dir, "assets")), name="assets"
)



@app.get("/", response_model=None)
async def index(inertia: InertiaDep) -> InertiaResponse:
    props = {
        "message": "hello from index",
    }
    return await inertia.render("Index", props)
```


## Customize the configuration
You can edit the configuration as you desire. Here's how to do it
```python
import os
from typing import Annotated, Any
from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from json import JSONEncoder
from .inertia import (  # noqa
    InertiaRenderer,
    inertia_renderer_factory,
    InertiaConfig,
)

manifest_json = os.path.join(
    os.path.dirname(__file__), "..", "vue", "dist", "client", "manifest.json"
)

class CustomJsonEncoder(JSONEncoder):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def encode(self, value: Any) -> Any:
        return jsonable_encoder(value)

    

inertia_config = InertiaConfig(
    environment="production",
    version="1.0.1",
    json_encoder=CustomJsonEncoder,
    manifest_json_path=manifest_json,
    dev_url = "http://localhost:5175",
    ssr_url = "http://localhost:12000",
    ssr_enabled = True
)

InertiaDep = Annotated[
    InertiaRenderer, Depends(inertia_renderer_factory(inertia_config))
]

```

## Ready for production
In order to serve your application in a production environment, you'll need to adjust a few things.
First, you need to build your Vue application. You can do this by running `npm run build` in the `vue` directory.
After that, you can edit the Inertia configuration as follows:
```python
import os
from typing import Annotated
from fastapi import Depends, FastAPI
from starlette.staticfiles import StaticFiles
from .inertia import (  # noqa
    InertiaRenderer,
    inertia_renderer_factory,
    inertia_exception_handler,
    InertiaVersionConflictException,
    InertiaConfig,
)

app = FastAPI()
app.add_exception_handler(InertiaVersionConflictException, inertia_exception_handler)

# Set the path to the manifest.json file
manifest_json = os.path.join(
    os.path.dirname(__file__), "..", "vue", "dist", "client", "manifest.json"
)

# Set the environment to production
inertia_config = InertiaConfig(
    manifest_json_path=manifest_json,
    environment="production",
)
InertiaDep = Annotated[
    InertiaRenderer, Depends(inertia_renderer_factory(inertia_config))
]

# Set the vue directory as the dist directory
vue_dir = os.path.join(os.path.dirname(__file__), "..", "vue", "dist", "client")

app.mount("/src", StaticFiles(directory=vue_dir), name="src")
app.mount(
    "/assets", StaticFiles(directory=os.path.join(vue_dir, "assets")), name="assets"
)
```

## Using SSR
In order to use SSR, you first need to build your vue application.
You'll need to have the inertia server running, you can do so with `node dist/ssr/ssr.js`
Finally, you just need to set the `ssr_enabled=True` parameter in the InertiaConfig object.


## Using the share method
You can use the share method to pass props to Inertia from a dependency, for example. 
Here's an example of the share method in action:
```python
from fastapi import FastAPI, Depends
from typing import Annotated
from .inertia import InertiaRenderer, InertiaResponse  #noqa

app = FastAPI()

InertiaDep = Annotated[
    InertiaRenderer, Depends(InertiaRenderer)
]


def some_dependency(inertia: InertiaDep) -> None:
    inertia.share(message="hello from dependency")

    
# Given the share method is called in the dependency, the props will be passed to the InertiaResponse
@app.get("/", response_model=None, dependencies=[Depends(some_dependency)])
async def index_with_shared_data(inertia: InertiaDep) -> InertiaResponse:
    return await inertia.render("Index")
```

## Using the flash method
You can use the flash method to pass a message to the next response. It will be deleted upon the next request.
It uses Starlette's SessionMiddleware, so you need to have it enabled.
The flash method is a simple helper which will set the message(s) in the session.
Upon rendering, inertia will read those messages and pass those as props to the InertiaResponse, under the `messages` key.

```python
from fastapi import FastAPI, Depends
from starlette.middleware.sessions import SessionMiddleware
from typing import Annotated
from .inertia import InertiaRenderer, InertiaResponse  #noqa

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="secret_key")

InertiaDep = Annotated[
    InertiaRenderer, Depends(InertiaRenderer)
]


@app.get("/", response_model=None)
async def index_with_flashed_data(inertia: InertiaDep) -> InertiaResponse:
    inertia.flash(message="hello from flash", category="primary")
    inertia.flash(message="an error happened", category="error")
    return await inertia.render("Index")
```

## Using lazy props
You can use the lazy props to pass a callable to the InertiaResponse. 
Lazy props will only be computed upon partial reloads, and not upon full page reloads. (see InertiaJS docs for more info)

```python
from fastapi import FastAPI, Depends
from typing import Annotated
from .inertia import InertiaRenderer, InertiaResponse, lazy  #noqa

app = FastAPI()

InertiaDep = Annotated[
    InertiaRenderer, Depends(InertiaRenderer)
]


@app.get("/", response_model=None)
async def index_with_shared_data(inertia: InertiaDep) -> InertiaResponse:
    props = {
        "message": lazy(lambda: "hello from lazy prop")
    }
    return await inertia.render("Index", props)
```
