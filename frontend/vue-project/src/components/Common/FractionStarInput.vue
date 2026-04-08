<template>
  <div class="fraction-star-input" @mouseleave="hoverValue = null">
    <button
      v-for="index in maxStars"
      :key="index"
      type="button"
      class="star-btn"
      @mousemove="preview(index - 1, $event)"
      @click="pick(index - 1, $event)"
    >
      <svg class="star" :width="size" :height="size" viewBox="0 0 24 24" aria-hidden="true">
        <defs>
          <clipPath :id="clipId(index)">
            <rect x="0" y="0" :width="starFill(index - 1) * 24" height="24" />
          </clipPath>
        </defs>
        <path :d="starPath" fill="#d6dbc9" />
        <path :d="starPath" fill="#f0b31a" :clip-path="`url(#${clipId(index)})`" />
      </svg>
    </button>
    <span class="score-text">{{ currentValue.toFixed(2) }} 分</span>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';

const props = defineProps({
  modelValue: {
    type: Number,
    default: 5
  },
  max: {
    type: Number,
    default: 5
  },
  size: {
    type: Number,
    default: 28
  },
  step: {
    type: Number,
    default: 0.25
  }
});

const emit = defineEmits(['update:modelValue', 'change']);

const hoverValue = ref(null);
const uid = Math.random().toString(36).slice(2, 10);
const starPath = 'M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z';

const maxStars = computed(() => {
  const value = Number(props.max);
  if (!Number.isFinite(value) || value <= 0) return 5;
  return Math.floor(value);
});

const normalizedStep = computed(() => {
  const value = Number(props.step);
  if (!Number.isFinite(value) || value <= 0) return 0.25;
  return value;
});

const normalizedModel = computed(() => {
  const value = Number(props.modelValue);
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(maxStars.value, value));
});

const currentValue = computed(() => {
  if (hoverValue.value === null) return normalizedModel.value;
  return hoverValue.value;
});

const clipId = (index) => `fraction-input-${uid}-${index}`;

const normalizeByStep = (rawValue) => {
  const step = normalizedStep.value;
  const snapped = Math.ceil(rawValue / step) * step;
  return Math.max(0, Math.min(maxStars.value, Number(snapped.toFixed(2))));
};

const calcFromPointer = (starIndex, event) => {
  const target = event.currentTarget;
  const rect = target.getBoundingClientRect();
  const ratio = Math.max(0, Math.min(1, (event.clientX - rect.left) / Math.max(rect.width, 1)));
  return normalizeByStep(starIndex + ratio);
};

const preview = (starIndex, event) => {
  hoverValue.value = calcFromPointer(starIndex, event);
};

const pick = (starIndex, event) => {
  const next = calcFromPointer(starIndex, event);
  emit('update:modelValue', next);
  emit('change', next);
};

const starFill = (index) => {
  const remain = currentValue.value - index;
  return Math.max(0, Math.min(1, remain));
};
</script>

<style scoped>
.fraction-star-input {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.star-btn {
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  line-height: 1;
}

.star {
  display: block;
}

.score-text {
  margin-left: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #2d3436;
}
</style>
