import {fileURLToPath, URL} from 'node:url'
import { dirname } from 'path';

import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'

const projectRoot = dirname(fileURLToPath(import.meta.url));
// https://vitejs.dev/config/
export default defineConfig(({isSsrBuild}) => ({
    plugins: [
        vue({
            template: {
                transformAssetUrls: {
                    base: null,
                    includeAbsolute: false,
                },
            },
        }),
    ],
    resolve: {
        alias: {
            '@': `${projectRoot}/src`,
        }
    },
    build: {
        manifest: isSsrBuild ? false : 'manifest.json',
        outDir: isSsrBuild ? 'dist/ssr' : 'dist/client',
        rollupOptions: {
            input: isSsrBuild ? 'src/ssr.js' : 'src/main.js',
        },
        assetsInlineLimit: 0
    },
    ssr: {
        noExternal: false
    }
}))
