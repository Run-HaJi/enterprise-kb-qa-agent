<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { loginAPI, getUserInfoAPI } from '../../apis/auth'
import { useUserStore } from '../../store/user'

const router = useRouter()
const userStore = useUserStore()

const loginForm = reactive({
  username: '',
  password: ''
})

const loading = ref(false)

const handleLogin = async () => {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }

  try {
    loading.value = true
    const response = await loginAPI(loginForm)

    // response.data结构可能是{status_code: number, data: {...}}
    const responseData = response.data
    if (responseData.status_code === 200) {
      ElMessage.success('登录成功')

      // 使用store管理用户状态
      const userData = responseData.data || {}
      if (userData.access_token && userData.user_id) {
        // 先保存基础用户信息
        userStore.setUserInfo(userData.access_token, {
          id: userData.user_id,
          username: loginForm.username
        })

        // 立即获取完整的用户信息（包括头像等）
        try {
          const userInfoResponse = await getUserInfoAPI(userData.user_id)
          const userInfoData = userInfoResponse.data
          if (userInfoData.status_code === 200) {
            const completeUserData = userInfoData.data || {}
            // 更新用户信息，包含头像
            userStore.updateUserInfo({
              avatar: completeUserData.user_avatar || completeUserData.avatar,
              description: completeUserData.user_description || completeUserData.description
            })
          }
        } catch (error) {
          console.error('获取用户详细信息失败:', error)
        }
      }

      // 跳转到主页
      router.push('/')
    } else {
      ElMessage.error(responseData.status_message || '登录失败')
    }
  } catch (error: any) {
    console.error('登录错误:', error)
    if (error.response?.data?.message) {
      ElMessage.error(error.response.data.status_message)
    } else if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('登录失败，请检查网络连接')
    }
  } finally {
    loading.value = false
  }
}

const goToRegister = () => {
  router.push('/register')
}
</script>

<template>
  <div class="flex h-full min-h-screen bg-bg">
    <!-- 左侧品牌区 -->
    <div class="relative hidden w-[46%] flex-col justify-between overflow-hidden border-r border-edge p-12 lg:flex">
      <!-- 网格纹理背景 -->
      <div
        class="pointer-events-none absolute inset-0 opacity-40"
        style="background-image: linear-gradient(#1c1f24 1px, transparent 1px), linear-gradient(90deg, #1c1f24 1px, transparent 1px); background-size: 44px 44px;"
      />
      <!-- 顶部光晕 -->
      <div
        class="pointer-events-none absolute -top-40 -left-24 h-[420px] w-[420px] rounded-full opacity-20 blur-3xl"
        style="background: radial-gradient(circle, var(--color-brand) 0%, transparent 65%);"
      />

      <div class="relative flex items-center gap-3">
        <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-brand/15 font-mono text-sm font-bold text-brand ring-1 ring-brand/30">
          KB
        </div>
        <span class="font-mono text-sm tracking-widest text-ink-2">KBQA PLATFORM</span>
      </div>

      <div class="relative">
        <h1 class="text-4xl leading-tight font-semibold text-ink">
          企业知识库<br />智能问答平台
        </h1>
        <p class="mt-5 max-w-md text-sm leading-6 text-ink-2">
          基于检索增强生成与多 Agent 协作，让每一次回答都有据可查。
        </p>

        <ul class="mt-10 space-y-4 text-sm text-ink-2">
          <li class="flex items-center gap-3">
            <span class="h-1.5 w-1.5 rounded-full bg-brand" />
            文档解析 · 语义检索 · 引用溯源
          </li>
          <li class="flex items-center gap-3">
            <span class="h-1.5 w-1.5 rounded-full bg-brand" />
            多 Agent 协作与插件工具调用
          </li>
          <li class="flex items-center gap-3">
            <span class="h-1.5 w-1.5 rounded-full bg-brand" />
            本地向量化，数据不出内网
          </li>
        </ul>
      </div>

      <div class="relative font-mono text-xs text-ink-3">
        RAG · Multi-Agent · SSE Streaming · ChromaDB
      </div>
    </div>

    <!-- 右侧表单区 -->
    <div class="flex flex-1 items-center justify-center px-6">
      <div class="w-full max-w-sm">
        <!-- 移动端 Logo -->
        <div class="mb-10 flex items-center gap-3 lg:hidden">
          <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-brand/15 font-mono text-sm font-bold text-brand ring-1 ring-brand/30">
            KB
          </div>
          <span class="text-lg font-semibold text-ink">企业知识库智能问答</span>
        </div>

        <h2 class="text-2xl font-semibold text-ink">登录</h2>
        <p class="mt-2 text-sm text-ink-3">欢迎回来，请使用平台账号继续</p>

        <form class="mt-8 space-y-5" @submit.prevent="handleLogin">
          <div>
            <label class="mb-2 block text-xs font-medium tracking-wide text-ink-2">账号</label>
            <el-input
              v-model="loginForm.username"
              placeholder="请输入账号"
              size="large"
              autocomplete="username"
            />
          </div>

          <div>
            <label class="mb-2 block text-xs font-medium tracking-wide text-ink-2">密码</label>
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              size="large"
              show-password
              autocomplete="current-password"
              @keyup.enter="handleLogin"
            />
          </div>

          <el-button
            type="primary"
            size="large"
            class="!w-full"
            :loading="loading"
            @click="handleLogin"
          >
            {{ loading ? '登录中…' : '登 录' }}
          </el-button>
        </form>

        <div class="mt-8 flex items-center justify-between text-sm">
          <span class="text-ink-3">还没有账号？</span>
          <button
            class="text-brand transition-colors hover:text-brand-dim"
            @click="goToRegister"
          >
            注册新账号 →
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
