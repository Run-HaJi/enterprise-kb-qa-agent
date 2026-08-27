<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { registerAPI } from '../../apis/auth'
import type { RegisterForm } from '../../apis/auth'

const router = useRouter()

const registerForm = reactive<RegisterForm>({
  user_name: '',
  user_email: '',
  user_password: ''
})

const confirmPassword = ref('')
const loading = ref(false)

const validateForm = () => {
  if (!registerForm.user_name) {
    ElMessage.warning('请输入用户名')
    return false
  }
  
  if (registerForm.user_name.length > 20) {
    ElMessage.warning('用户名长度不应该超过20个字符')
    return false
  }
  
  if (!registerForm.user_password) {
    ElMessage.warning('请输入密码')
    return false
  }
  
  if (registerForm.user_password.length < 6) {
    ElMessage.warning('密码长度至少6个字符')
    return false
  }
  
  if (registerForm.user_password !== confirmPassword.value) {
    ElMessage.warning('两次输入的密码不一致')
    return false
  }
  
  if (registerForm.user_email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(registerForm.user_email)) {
    ElMessage.warning('请输入有效的邮箱地址')
    return false
  }
  
  return true
}

const handleRegister = async () => {
  if (!validateForm()) return

  try {
    loading.value = true
    const response = await registerAPI(registerForm)
    if (response.data.status_code === 200) {
      ElMessage.success('注册成功，请登录')
      router.push('/login')
    } else {
      ElMessage.error(response.data.status_message || '注册失败')
    }
  } catch (error: any) {
    console.error('注册错误:', error)
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('注册失败，请检查网络连接')
    }
  } finally {
    loading.value = false
  }
}

const goToLogin = () => {
  router.push('/login')
}
</script>

<template>
  <div class="flex h-full min-h-screen items-center justify-center bg-bg px-6">
    <div class="w-full max-w-sm">
      <!-- Logo -->
      <div class="mb-10 flex items-center gap-3">
        <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-brand/15 font-mono text-sm font-bold text-brand ring-1 ring-brand/30">
          KB
        </div>
        <span class="font-mono text-sm tracking-widest text-ink-2">KBQA PLATFORM</span>
      </div>

      <h2 class="text-2xl font-semibold text-ink">创建账号</h2>
      <p class="mt-2 text-sm text-ink-3">注册后即可使用知识库问答与 Agent 能力</p>

      <form class="mt-8 space-y-5" @submit.prevent="handleRegister">
        <div>
          <label class="mb-2 block text-xs font-medium tracking-wide text-ink-2">用户名</label>
          <el-input
            v-model="registerForm.user_name"
            placeholder="最多 20 个字符"
            size="large"
            @keyup.enter="handleRegister"
          />
        </div>

        <div>
          <label class="mb-2 block text-xs font-medium tracking-wide text-ink-2">邮箱（可选）</label>
          <el-input
            v-model="registerForm.user_email"
            placeholder="用于接收通知"
            size="large"
            @keyup.enter="handleRegister"
          />
        </div>

        <div>
          <label class="mb-2 block text-xs font-medium tracking-wide text-ink-2">密码</label>
          <el-input
            v-model="registerForm.user_password"
            type="password"
            placeholder="至少 6 个字符"
            size="large"
            show-password
            @keyup.enter="handleRegister"
          />
        </div>

        <div>
          <label class="mb-2 block text-xs font-medium tracking-wide text-ink-2">确认密码</label>
          <el-input
            v-model="confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            size="large"
            show-password
            @keyup.enter="handleRegister"
          />
        </div>

        <el-button
          type="primary"
          size="large"
          class="!w-full"
          :loading="loading"
          @click="handleRegister"
        >
          {{ loading ? '注册中…' : '注 册' }}
        </el-button>
      </form>

      <div class="mt-8 flex items-center justify-between text-sm">
        <span class="text-ink-3">已有账号？</span>
        <button
          class="text-brand transition-colors hover:text-brand-dim"
          @click="goToLogin"
        >
          返回登录 →
        </button>
      </div>
    </div>
  </div>
</template>
