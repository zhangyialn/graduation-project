<!-- 首个管理员初始化页：仅在系统尚无管理员时可访问 -->
<template>
  <div class="bootstrap-container">
    <el-card class="bootstrap-card" shadow="hover">
      <template #header>
        <div class="header">
          <h2>初始化首个管理员</h2>
          <p>仅在系统尚无管理员时可用</p>
        </div>
      </template>

      <el-alert
        type="warning"
        :closable="false"
        show-icon
        title="安全提示"
        description="初始化完成后，该入口将自动失效；一次性密钥默认10分钟有效，绑定当前浏览器且仅可使用一次。"
        class="mb"
      />

      <el-card shadow="never" class="mb key-card">
        <div class="key-row">
          <el-button type="primary" plain :loading="generatingKey" @click="generateKey">一键生成初始化密钥</el-button>
          <span class="key-tip" v-if="expiresIn > 0">剩余有效期：{{ expiresIn }} 秒</span>
        </div>
        <el-input
          v-model="form.bootstrap_key"
          type="textarea"
          :rows="2"
          readonly
          placeholder="点击上方按钮生成一次性初始化密钥"
        />
      </el-card>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入管理员用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入管理员密码" />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" placeholder="可选" />
        </el-form-item>
        <el-form-item label="部门ID">
          <el-input-number v-model="form.department_id" :min="1" controls-position="right" />
        </el-form-item>
        <el-form-item label="初始化密钥">
          <el-input v-model="form.bootstrap_key" type="password" show-password placeholder="请先点击“一键生成初始化密钥”" />
        </el-form-item>
        <el-form-item label="主初始化密钥">
          <el-input v-model="form.bootstrap_master_key" type="password" show-password placeholder="可选：若后端配置 BOOTSTRAP_ADMIN_KEY 则此项必填" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="submit">初始化管理员</el-button>
          <el-button @click="goLogin">返回登录</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref, watch, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { notifyError, notifySuccess } from '../../utils/notify';

const router = useRouter();
const loading = ref(false);
const generatingKey = ref(false);
const expiresIn = ref(0);
let countdownTimer = null;
const formRef = ref(null);
const error = ref('');
const success = ref('');
const checkingStatus = ref(true);
const bootstrapEnabled = ref(true);

const form = reactive({
  username: '',
  password: '',
  name: '',
  phone: '',
  email: '',
  department_id: null,
  bootstrap_key: '',
  bootstrap_master_key: ''
});

const rules = reactive({
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [{ required: true, message: '请输入手机号', trigger: 'blur' }]
});

// 提交初始化请求：创建首个管理员账号，成功后返回登录页
const submit = async () => {
  try {
    await formRef.value.validate();
    loading.value = true;
    error.value = '';
    success.value = '';

    await axios.post('/api/auth/bootstrap-admin', {
      username: form.username,
      password: form.password,
      name: form.name,
      phone: form.phone,
      email: form.email || undefined,
      department_id: form.department_id || undefined,
      bootstrap_key: form.bootstrap_key || undefined,
      bootstrap_master_key: form.bootstrap_master_key || undefined
    });

    success.value = '初始化成功，请使用新管理员账号登录';
    notifySuccess(success.value);
    router.push('/login');
  } catch (err) {
    error.value = err.response?.data?.message || '初始化失败';
  } finally {
    loading.value = false;
  }
};

// 启动一次性密钥倒计时，过期后自动清空
const startCountdown = (seconds) => {
  if (countdownTimer) {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }
  expiresIn.value = Number(seconds || 0);
  if (expiresIn.value <= 0) return;
  countdownTimer = setInterval(() => {
    expiresIn.value -= 1;
    if (expiresIn.value <= 0) {
      clearInterval(countdownTimer);
      countdownTimer = null;
      form.bootstrap_key = '';
    }
  }, 1000);
};

// 向后端申请一次性初始化密钥并回填到表单
const generateKey = async () => {
  if (!bootstrapEnabled.value) return;
  try {
    generatingKey.value = true;
    const response = await axios.post('/api/auth/bootstrap-key');
    form.bootstrap_key = response.data?.data?.bootstrap_key || '';
    startCountdown(response.data?.data?.expires_in || 0);
    notifySuccess('初始化密钥已生成并自动填入');
  } catch (err) {
    notifyError(err.response?.data?.message || '生成初始化密钥失败');
  } finally {
    generatingKey.value = false;
  }
};

// 返回登录页
const goLogin = () => router.push('/login');

// 页面加载时检查初始化入口是否启用；若已关闭则直接跳回登录页
const checkBootstrapStatus = async () => {
  try {
    checkingStatus.value = true;
    const response = await axios.get('/api/auth/bootstrap-status');
    const enabled = !!response.data?.data?.enabled;
    bootstrapEnabled.value = enabled;
    if (!enabled) {
      notifyError(response.data?.data?.reason || '系统已存在管理员，初始化入口已关闭');
      router.replace('/login');
    }
  } catch (_err) {
    bootstrapEnabled.value = false;
    notifyError('初始化入口不可用');
    router.replace('/login');
  } finally {
    checkingStatus.value = false;
  }
};

checkBootstrapStatus();

onBeforeUnmount(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }
});

watch(error, (message) => {
  if (!message) return;
  notifyError(message);
});
</script>

<style scoped>
.bootstrap-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: #f4f7ed;
}

.bootstrap-card {
  width: 100%;
  max-width: 760px;
  border-radius: 12px;
}

.header h2 {
  margin: 0;
}

.header p {
  margin: 6px 0 0;
  color: #667459;
}

.mb {
  margin-bottom: 12px;
}

.key-card {
  border: 1px dashed #d9c7a8;
}

.key-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.key-tip {
  color: #8b7355;
  font-size: 13px;
}
</style>
