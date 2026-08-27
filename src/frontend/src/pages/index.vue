<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, SwitchButton } from '@element-plus/icons-vue'
import { useUserStore } from '../store/user'
import { logoutAPI } from '../apis/auth'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const current = ref('homepage')

const handleMenuSelect = (index: string) => {
  current.value = index
  goCurrent(index)
}

const goCurrent = (name: string) => {
  router.push(`/${name === 'homepage' ? 'homepage' : name}`)
}

const godefault = () => {
  router.push('/homepage')
}

const handleUserCommand = async (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'logout':
      await handleLogout()
      break
  }
}

const handleLogout = async () => {
  try {
    await logoutAPI()
  } catch (error) {
    console.error('调用登出接口失败:', error)
  }
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}

// 头像加载错误处理
const handleAvatarError = (event: Event) => {
  const target = event.target as HTMLImageElement
  if (target) {
    target.src = '/src/assets/user.svg'
  }
}

watch(
  route,
  (val) => {
    current.value = route.meta.current
  },
  {
    immediate: true
  }
)
</script>

<template>
  <div class="app-shell">
    <!-- 侧边栏 -->
    <aside class="side-nav">
      <div class="side-brand" @click="godefault" title="应用中心">
        <div class="brand-mark">KB</div>
        <div class="brand-text">
          <span class="brand-name">KBQA</span>
          <span class="brand-sub">企业知识库智能问答</span>
        </div>
      </div>

      <el-menu
        class="side-menu"
        :default-active="current"
        background-color="transparent"
        text-color="#a3a9b3"
        active-text-color="#5b9dff"
        @select="handleMenuSelect"
      >
        <el-menu-item index="workspace">
          <span>工作台</span>
        </el-menu-item>
        <el-menu-item index="homepage">
          <span>应用中心</span>
        </el-menu-item>
        <el-menu-item index="conversation">
          <span>会话</span>
        </el-menu-item>
        <el-menu-item index="agent">
          <span>智能体</span>
        </el-menu-item>
        <el-menu-item index="knowledge">
          <span>知识库</span>
        </el-menu-item>
        <el-menu-item index="tool">
          <span>工具</span>
        </el-menu-item>
        <el-menu-item index="model">
          <span>模型</span>
        </el-menu-item>
      </el-menu>

      <div class="side-footer">
        <el-dropdown @command="handleUserCommand" trigger="click">
          <div class="side-user">
            <img
              :src="userStore.userInfo?.avatar || '/src/assets/user.svg'"
              alt="用户头像"
              @error="handleAvatarError"
              referrerpolicy="no-referrer"
            />
            <span class="side-user-name">
              {{ userStore.userInfo?.username || '用户' }}
            </span>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile" :icon="User">个人资料</el-dropdown-item>
              <el-dropdown-item divided command="logout" :icon="SwitchButton">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <a
          href="https://github.com/Run-HaJi/enterprise-kb-qa-agent"
          target="_blank"
          class="side-github"
          title="GitHub 仓库"
        >
          GitHub
        </a>
      </div>
    </aside>

    <!-- 内容区 -->
    <main class="app-content">
      <router-view></router-view>
    </main>
  </div>
</template>

<style lang="scss" scoped>
.app-shell {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--color-bg);
}

.side-nav {
  display: flex;
  flex-direction: column;
  width: 216px;
  flex-shrink: 0;
  background: var(--color-panel);
  border-right: 1px solid var(--color-edge);
}

.side-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 14px;
  cursor: pointer;

  .brand-mark {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 30px;
    height: 30px;
    border-radius: 8px;
    background: rgba(91, 157, 255, 0.14);
    border: 1px solid rgba(91, 157, 255, 0.3);
    font-family: var(--font-mono);
    font-size: 12px;
    font-weight: 700;
    color: var(--color-brand);
  }

  .brand-text {
    display: flex;
    flex-direction: column;
    line-height: 1.25;
  }

  .brand-name {
    font-family: var(--font-mono);
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 1px;
    color: var(--color-ink);
  }

  .brand-sub {
    font-size: 10px;
    color: var(--color-ink-3);
  }
}

.side-menu {
  flex: 1;
  border-right: none;
  padding: 6px;

  :deep(.el-menu-item) {
    height: 38px;
    margin: 2px 0;
    border-radius: 8px;
    font-size: 13px;
    line-height: 38px;

    &:hover {
      background: var(--color-hover);
    }

    &.is-active {
      background: var(--color-hover);
      box-shadow: inset 2px 0 0 var(--color-brand);
      font-weight: 500;
      color: var(--color-brand);
    }
  }
}

.side-footer {
  padding: 12px;
  border-top: 1px solid var(--color-edge-soft);
}

.side-user {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 6px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.12s ease;

  &:hover {
    background: var(--color-hover);
  }

  img {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    object-fit: cover;
    border: 1px solid var(--color-edge);
  }
}

.side-user-name {
  font-size: 13px;
  color: var(--color-ink-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.side-github {
  display: block;
  margin-top: 6px;
  padding: 0 6px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--color-ink-3);
  text-decoration: none;

  &:hover {
    color: var(--color-ink-2);
  }
}

.app-content {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  background: var(--color-bg);
}
</style>
