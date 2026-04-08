<template>
  <span class="fraction-star-wrap">
    <span class="stars" aria-hidden="true">
      <svg
        v-for="(fillWidth, index) in starFillPercents"
        :key="index"
        class="star"
        :width="iconSize"
        :height="iconSize"
        viewBox="0 0 24 24"
      >
        <defs>
          <clipPath :id="clipId(index)">
            <rect x="0" y="0" :width="(fillWidth / 100) * 24" height="24" />
          </clipPath>
        </defs>
        <path :d="starPath" fill="#d6dbc9" />
        <path :d="starPath" fill="#f0b31a" :clip-path="`url(#${clipId(index)})`" />
      </svg>
    </span>
    <span v-if="showText" class="score-text">{{ normalizedScore.toFixed(2) }} 分</span>
  </span>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  score: {
    type: Number,
    default: 0
  },
  max: {
    type: Number,
    default: 5
  },
  size: {
    type: Number,
    default: 22
  },
  showText: {
    type: Boolean,
    default: true
  }
});

const maxScore = computed(() => {
  const value = Number(props.max);
  if (!Number.isFinite(value) || value <= 0) return 5;
  return value;
});

const normalizedScore = computed(() => {
  const value = Number(props.score);
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(maxScore.value, value));
});

const starCount = computed(() => Math.floor(maxScore.value));

// 每颗星单独计算填充比例，确保小数分值精确映射到最后一颗星。
const starFillPercents = computed(() => {
  return Array.from({ length: starCount.value }, (_item, index) => {
    const current = normalizedScore.value - index;
    const fillRatio = Math.max(0, Math.min(1, current));
    return fillRatio * 100;
  });
});

const iconSize = computed(() => {
  const value = Number(props.size);
  if (!Number.isFinite(value) || value <= 0) return 22;
  return value;
});

const starPath = 'M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z';

const uid = Math.random().toString(36).slice(2, 10);
const clipId = (index) => `fraction-star-${uid}-${index}`;

</script>

<style scoped>
.fraction-star-wrap {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.stars {
  display: inline-flex;
  gap: 3px;
}

.star {
  flex: 0 0 auto;
}

.score-text {
  font-size: 14px;
  color: #2d3436;
  font-weight: 600;
}
</style>
