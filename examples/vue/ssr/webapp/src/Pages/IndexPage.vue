<script setup>
import { Link } from "@inertiajs/vue3";
import { ref } from "vue";

defineProps({
  message: String,
});

const counter = ref(0);
</script>

<template>
  <main>
    <Link href="/2">Link to other page</Link>
    <Link href="/" :only="['lazy_prop']">Partial reload (only lazy prop)</Link>
    <button @click="counter++">
      Reactive button (clicked {{ counter }} times)
    </button>
    <div class="props">
      <h1>Props</h1>
      <span> Message: {{ message }} </span>
      <span> Flashed messages: {{ $page.props.messages }} </span>
      <span> Lazy prop: {{ $page.props.lazy_prop }} </span>
    </div>
  </main>
</template>

<style scoped>
main {
  min-height: 100dvh;
  width: 100%;
  display: flex;
  gap: 1rem;
  place-items: center;
  place-content: center;
  flex-direction: column;
  > * {
    max-width: 50%;
  }

  .props {
    display: flex;
    flex-direction: column;
    gap: 1rem;

    h1 {
      font-weight: bold;
      width: 100%;
      text-align: center;
    }
  }
}
</style>
