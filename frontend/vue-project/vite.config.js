import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  base: './',
  plugins: [
    vue(),
    // 自动按需注册 Element Plus 组件，避免入口处全量引入。
    Components({
      resolvers: [
        ElementPlusResolver({
          importStyle: 'css'
        })
      ]
    }),
    // 开发工具仅在本地启用，避免进入生产包体。
    mode === 'development' ? vueDevTools() : null,
  ].filter(Boolean),
  build: {
    rollupOptions: {
      output: {
        // 按依赖族拆分 vendor chunk，降低首包并提升浏览器缓存命中。
        manualChunks(id) {
          if (!id.includes('node_modules')) return;
          if (id.includes('echarts')) {
            if (id.includes('echarts/charts')) return 'vendor-echarts-charts';
            if (id.includes('echarts/components')) return 'vendor-echarts-components';
            if (id.includes('echarts/renderers')) return 'vendor-echarts-renderers';
            return 'vendor-echarts-core';
          }
          if (id.includes('@element-plus/icons-vue')) return 'vendor-ep-icons';
          if (id.includes('element-plus/es/components/')) {
            const section = id.split('element-plus/es/components/')[1] || '';
            const componentName = section.split('/')[0] || 'shared';
            const firstChar = componentName[0] || 'a';
            return firstChar < 'n' ? 'vendor-element-plus-components-a-m' : 'vendor-element-plus-components-n-z';
          }
          if (id.includes('element-plus')) return 'vendor-element-plus-core';
          if (id.includes('vue-router')) return 'vendor-router';
          if (id.includes('pinia')) return 'vendor-pinia';
          if (id.includes('axios')) return 'vendor-axios';
          if (id.includes('vue')) return 'vendor-vue';
          return 'vendor';
        }
      }
    }
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
}))
