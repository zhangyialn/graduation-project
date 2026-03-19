<template>
  <div class="application-container">
    <h2>用车申请</h2>
    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <label for="department_id">部门ID</label>
        <input type="number" id="department_id" v-model="form.department_id" required>
      </div>
      <div class="form-group">
        <label for="purpose">用车事由</label>
        <input type="text" id="purpose" v-model="form.purpose" required>
      </div>
      <div class="form-group">
        <label for="start_time">开始时间</label>
        <input type="datetime-local" id="start_time" v-model="form.start_time" required>
      </div>
      <div class="form-group">
        <label for="end_time">结束时间</label>
        <input type="datetime-local" id="end_time" v-model="form.end_time" required>
      </div>
      <div class="form-group">
        <label for="destination">目的地</label>
        <input type="text" id="destination" v-model="form.destination" required>
      </div>
      <div class="form-group">
        <label for="passengers">乘车人数</label>
        <input type="number" id="passengers" v-model="form.passengers" required>
      </div>
      <div class="form-group">
        <label for="contact_phone">联系电话</label>
        <input type="text" id="contact_phone" v-model="form.contact_phone" required>
      </div>
      <button type="submit" class="btn btn-primary">提交申请</button>
      <div class="error-message" v-if="error">{{ error }}</div>
      <div class="success-message" v-if="success">{{ success }}</div>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();
const form = ref({
  department_id: 1,
  purpose: '',
  start_time: '',
  end_time: '',
  destination: '',
  passengers: 1,
  contact_phone: ''
});
const error = ref('');
const success = ref('');

const handleSubmit = async () => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.post('http://localhost:5000/api/applications', form.value, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    success.value = '申请提交成功';
    setTimeout(() => {
      router.push('/applications');
    }, 2000);
  } catch (err) {
    error.value = err.response?.data?.message || '提交失败';
  }
};
</script>

<style scoped>
.application-container {
  padding: 2rem;
  max-width: 800px;
  margin: 0 auto;
}

form {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.form-group {
  margin-bottom: 1rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover {
  background-color: #0069d9;
}

.error-message {
  margin-top: 1rem;
  color: #dc3545;
  font-size: 0.875rem;
}

.success-message {
  margin-top: 1rem;
  color: #28a745;
  font-size: 0.875rem;
}
</style>