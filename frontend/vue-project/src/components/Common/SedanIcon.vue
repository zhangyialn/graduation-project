<template>
  <span class="sedan-icon" aria-hidden="true" v-html="carLineSvg" />
</template>

<script setup>
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
