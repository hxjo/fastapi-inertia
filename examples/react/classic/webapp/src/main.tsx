import { createInertiaApp } from '@inertiajs/react'
import ReactDOM from 'react-dom/client'
import './index.css'

createInertiaApp({
  resolve: name => {
    const pages = import.meta.glob('./Pages/**/*.tsx', { eager: true })
    return pages[`./Pages/${name}.tsx`]
  },
  id: 'app',
  setup({ el, App, props }: any) {
    ReactDOM.createRoot(el).render(<App {...props} />)
  },
})

