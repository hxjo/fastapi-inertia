import './assets/main.css'

import { createApp, type DefineComponent, h } from 'vue'
import { createInertiaApp } from '@inertiajs/vue3'

createInertiaApp({
  resolve: (name: string) => {
    const pages = import.meta.glob('./Pages/**/*.vue', { eager: true })
    return pages[`./Pages/${name}.vue`] as DefineComponent
  },
  setup({ el, App, props, plugin }: any) {
    createApp({ render: () => h(App, props) })
      .use(plugin)
      .mount(el)
  }
})
