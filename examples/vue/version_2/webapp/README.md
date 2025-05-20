# frontend

This template should help get you started developing with Vue 3 in Vite.

## Recommended IDE Setup

[VSCode](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Customize configuration

See [Vite Configuration Reference](https://vitejs.dev/config/).

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Compile and Minify for Production

```sh
npm run build
```


# Inertia.js v2.0: A Major Leap Forward

Inertia.js v2.0 is a significant evolution of the library, completely rewritten to support asynchronous requests at its core. This architectural overhaul unlocks a powerful set of new features including:

## Deferred Props

Inertia.js v2.0 introduces **Deferred Props**, allowing you to defer the fetching of specific props until after the initial page render. This builds on the concept of `Lazy Props` from v1.0 but offers a more seamless experience. With v2.0, you no longer need to manually trigger deferred prop fetches on the frontend. Instead, Inertia provides the `<Deferred>` component, which automatically fetches deferred props after the page loads, simplifying the process and improving performance.

For detailed guidance, see the [Deferred Props documentation](https://inertiajs.com/deferred-props).

### Server-Side Implementation

To mark props as deferred on the server side, use the `defer` function provided by the Inertia library. This function receives a callable (sync or async) or a value to be evaluated. <br>
Below is an example of how to implement deferred props in a FastAPI application:

```python
from inertia import defer, InertiaDep, InertiaResponse
from fastapi import FastAPI, Depends

app = FastAPI()

@app.get("/example", response_model=None, dependencies=[Depends(some_dependency)])
async def example_page(inertia: InertiaDep) -> InertiaResponse:
    props = {
        "permissions": defer(lambda: ["read", "write", "delete"]),
        "usersData": defer(lambda: {"user1": "John Doe", "user2": "Jane Doe"}, group="attributes"),
        "teams": defer(["team1", "team2", "team3"], group="attributes"),
    }
    inertia.flash("Welcome to the example page!", category="message")
    return await inertia.render("ExamplePage", props)

```

In the example above, the `usersData` and `teams` props belonging to the `attributes` group will be fetched in one request, while the `permissions` prop will be fetched in a separate request in parallel. Group names are `optional` but recommended arbitrary strings and can be anything you choose.