<script setup>
import {Link, useForm, Deferred} from "@inertiajs/vue3";

defineProps({
  message: String,
  permissions: Array,
  usersData: Object,
});

const form = useForm({
  email: null,
  password: null,
})

</script>

<template>
  <main>
    <div class="deferred-section">
      <h2>Permissions</h2>
      <Deferred data="permissions">
        <template #fallback>
          <div>Loading permissions...</div>
        </template>
        <div v-for="permission in permissions" :key="permission">
          {{ permission }}
        </div>
      </Deferred>

      <h2>Users Data</h2>
      <Deferred data="usersData">
        <template #fallback>
          <div>Loading users data...</div>
        </template>
        <pre>{{ usersData }}</pre>
      </Deferred>
    </div>

    <Link href="/">Link to index page</Link>
    <div class="props">
      <h1>Props</h1>
      <span> Message: {{ message }} </span>
      <span> Flashed messages: {{ $page.props.messages }} </span>
    </div>
    <form @submit.prevent="form.post('/login')">
    <input type="text" placeholder="email" v-model="form.email">
    <div v-if="form.errors.email">{{ form.errors.email }}</div>
    <input type="password" placeholder="password" v-model="form.password">
    <div v-if="form.errors.password">{{ form.errors.password }}</div>
    <button type="submit" :disabled="form.processing">Login</button>
  </form>
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
