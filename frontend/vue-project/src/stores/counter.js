/** counter：Pinia示例计数器 */
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useCounterStore = defineStore('counter', () => {
  const count = ref(0)
  const doubleCount = computed(() => count.value * 2)
  // 计数值加一
  function increment() {
    count.value++
  }

  return { count, doubleCount, increment }
})
