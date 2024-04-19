# For Vue
## Init vue project

```bash
npm create vue@latest
```
(Of course, don't install vue-router)

## Edit the vite config so the generated assets on build are consistent and we can properly use those with inertia
```js
export default defineConfig({
    // ...
    build: {
        rollupOptions: {
            output: {
                entryFileNames: `assets/[name].js`,
                chunkFileNames: `assets/[name].js`,
                assetFileNames: `assets/[name].[ext]`
            }
        }
    }
})
```
And rename the `src/assets/main.css` to `src/assets/index.css`

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
## Edit settings
> Note:
> Those settings are read from the environment.
> Therefore, feel free to add a load_dotenv and set those in your .env file.

Edit `inertia/settings.py` to your needs:
```python
from typing import Type
from pydantic_settings import BaseSettings
from .utils import InertiaJsonEncoder  # type: ignore
from jinja2 import Environment, PackageLoader

class InertiaSettings(BaseSettings):
    INERTIA_VERSION: str = "1.0"
    INERTIA_JSON_ENCODER: Type[InertiaJsonEncoder] = InertiaJsonEncoder
    INERTIA_URL: str = "http://localhost:5173"  # Replace with your VUE dev server URL
    INERTIA_ENV: str = "dev"
    INERTIA_TEMPLATE_DIR: str = "inertia/templates"  # Replace with your template directory if you have one

    @property
    def INERTIA_TEMPLATE_ENV(self) -> Environment:
        # Replace `backend` with your project name
        env = Environment(loader=PackageLoader("backend", self.INERTIA_TEMPLATE_DIR))
        env.globals["script_url"] = (
            f"{self.INERTIA_URL}/src/main.js"  # Optionally, replace with a main.ts
            if self.INERTIA_ENV == "dev"
            else "/src/assets/index.js"
        )
        return env
```

## Setup and use Inertia in the FastAPI app

```python
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from .inertia import inertia, settings as inertia_settings, InertiaMiddleware, share  # type: ignore

app = FastAPI()
app.add_middleware(InertiaMiddleware)
assets_dir = (
    os.path.join(os.path.dirname(__file__), "..", "vue", "src")
    if inertia_settings.ENV == 'dev'
    else os.path.join(os.path.dirname(__file__), "..", "vue", "dist")
)

app.mount("/src", StaticFiles(directory=assets_dir), name="static")


@app.get("/")
@inertia('Index')
async def index(request: Request):
    share(request, name="John Doe")
    return {"message": "Hello, World!"}
```
