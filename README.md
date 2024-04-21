# Inertia.js FastAPI Adapter
## Installation
You can install the package via pip:
```bash
pip install fastapi-inertia
```


## Configuration
You can configure the adapter by passing a `InertiaConfig` object to the `Inertia` class. 
The following options are available:

| key                | default                | options                                 | description                                                                                                                      |
|--------------------|------------------------|-----------------------------------------|----------------------------------------------------------------------------------------------------------------------------------|
| environment        | development            | development,production                  | The environment to use                                                                                                           |
| version            | 1.0.0                  | Any valid string                        | The version of your server                                                                                                       |
| json_encoder       | InertiaJsonEncoder     | Any class that extends json.JSONEncoder | The JSON encoder used to encode page data when HTML is returned                                                                  |
| manifest_json_path | ""                     | Any valid path                          | The path to the manifest.json file. Needed in production                                                                         |
| dev_url            | http://localhost:5173  | Any valid url                           | The URL to the development server                                                                                                |
| ssr_url            | http://localhost:13714 | Any valid url                           | The URL to the SSR server                                                                                                        |
| ssr_enabled        | False                  | True,False                              | Whether to enable SSR. You need to install the `requests` package, to have set the manifest_json_path and started the SSR server |
| use_typescript     | False                  | True,False                              | Whether to use TypeScript                                                                                                        |
| use_flash_messages | False                  | True,False                              | Whether to use flash messages. You need to use Starlette's SessionMiddleware to use this feature                                 |
| flash_message_key  | messages               | Any valid string                        | The key to use for flash messages                                                                                                |
| use_flash_errors   | False                  | True,False                              | Whether to use flash errors                                                                                                      |
| flash_error_key    | errors                 | Any valid string                        | The key to use for flash errors                                                                                                  |

## Examples
You can see different full examples in the [following repository](https://github.com/hxjo/fastapi-inertia-examples).


## Usage
### Set up the dependency
This Inertia.js adapter has been developed to be used as a FastAPI dependency.
To use it, you first need to set up the dependency, with your desired configuration.

`inertia_dependency.py`
```python
from fastapi import Depends
from typing import Annotated
from fastapi_inertia import InertiaConfig, inertia_dependency_factory, Inertia

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
from fastapi_inertia import InertiaResponse, InertiaVersionConflictException, inertia_version_conflict_exception_handler
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
from fastapi_inertia import InertiaResponse, InertiaVersionConflictException, inertia_version_conflict_exception_handler
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
from fastapi_inertia import InertiaResponse, InertiaVersionConflictException, inertia_version_conflict_exception_handler
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
In order to use  this feature, you need to have set `use_flash_errors` to `True` in your configuration.
You also need to have the `SessionMiddleware` enabled in your application to use this feature.

`main.py`
```python
from fastapi import FastAPI, Depends
from pydantic import BaseModel, model_validator
from typing import Any
from fastapi.exceptions import RequestValidationError
from starlette.middleware.sessions import SessionMiddleware
from fastapi_inertia import InertiaResponse, InertiaVersionConflictException, inertia_version_conflict_exception_handler, inertia_request_validation_exception_handler
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
from fastapi_inertia import InertiaResponse, InertiaVersionConflictException, inertia_version_conflict_exception_handler
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
from fastapi_inertia import InertiaResponse, InertiaVersionConflictException, inertia_version_conflict_exception_handler
from inertia_dependency import InertiaDependency

app = FastAPI()
app.add_exception_handler(InertiaVersionConflictException, inertia_version_conflict_exception_handler)

@app.get('/', response_model=None)
async def index(inertia: InertiaDependency) -> InertiaResponse:
    return inertia.back()
```