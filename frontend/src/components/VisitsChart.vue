<script setup lang="ts">
import type { ShortLink } from '../types'
import { Chart, DoughnutController, ArcElement, Tooltip, Legend } from 'chart.js'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
Chart.register(DoughnutController, ArcElement, Tooltip, Legend)
const props = defineProps<{ links: ShortLink[] }>()
const canvas = ref<HTMLCanvasElement | null>(null)
const hasVisits = computed(() => props.links.some(link => link.visits > 0))
let chart: Chart<'doughnut'> | null = null
function draw() {
  if (!canvas.value || !hasVisits.value) {
    chart?.destroy(); chart = null
    return
  }
  const palette = ['#9ac9a5', '#538365', '#c1d8ae', '#6eaaa0', '#85975e', '#385e48']
  const data = { labels: props.links.map(link => link.shortUrl), datasets: [{ data: props.links.map(link => link.visits), backgroundColor: props.links.map((_, i) => palette[i % palette.length]), borderColor: '#13251b', borderWidth: 4 }] }
  if (chart) {
    chart.data = data
    chart.update('none')
    return
  }
  chart = new Chart(canvas.value, {
    type: 'doughnut',
    data,
    options: { responsive: true, maintainAspectRatio: false, cutout: '70%', plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, padding: 18, color: '#a6bbae' } } } },
  })
}
onMounted(draw)
watch(() => props.links, draw, { deep: true, flush: 'post' })
onBeforeUnmount(() => chart?.destroy())
</script>
<template>
  <div class="visits-chart">
    <div v-if="hasVisits" class="chart-container"><canvas ref="canvas" role="img" aria-label="Visits per short link"></canvas></div><p v-else class="small-note">Your chart will appear when your links receive their first visit.</p>
  </div>
</template>
<style scoped lang="scss">
.chart-container { position: relative; height: 320px; width: 100%; }
</style>
