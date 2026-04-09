<!-- 统一车标图标组件：把原始 SVG 当作文本注入，保证菜单/卡片图标风格一致 -->
<template>
  <span class="sedan-icon" aria-hidden="true" v-html="carLineSvg" />
</template>

<script setup>
// 使用 ?raw 直接拿到 SVG 字符串，避免额外的网络请求与图标闪烁。
import carLineSvg from '../../assets/icons/car-line.svg?raw';
</script>

<style scoped>
.sedan-icon {
  width: 1em;
  height: 1em;
  display: block;
}

.sedan-icon :deep(svg) {
  width: 100%;
  height: 100%;
}
</style>
