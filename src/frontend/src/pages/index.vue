<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, SwitchButton } from '@element-plus/icons-vue'
import { useUserStore } from '../store/user'
import { logoutAPI } from '../apis/auth'
import {
  getWorkspaceSessionsAPI,
  deleteWorkspaceSessionAPI
} from '../apis/workspace'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const selectedSession = ref('')
const sessions = ref<any[]>([])
const loading = ref(false)

const navItems = [
  { key: 'chat', label: '对话', route: '/' },
  { key: 'knowledge', label: '知识库', route: '/knowledge' },
  { key: 'agent', label: '智能体', route: '/agent' },
  { key: 'tool', label: '工具', route: '/tool' },
  { key: 'model', label: '模型', route: '/model' }
]

// ---------- 会话历史 ----------
const formatTime = (timeStr: string) => {
  try {
    if (!timeStr) return ''
    const date = new Date(timeStr)
    if (isNaN(date.getTime())) return ''
    const diffInHours = (Date.now() - date.getTime()) / (1000 * 60 * 60)
    if (diffInHours < 1) return '刚刚'
    if (diffInHours < 24) return `${Math.floor(diffInHours)}小时前`
    if (diffInHours < 24 * 7) return `${Math.floor(diffInHours / 24)}天前`
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  } catch {
    return ''
  }
}

const fetchSessions = async () => {
  try {
    loading.value = true
    const response = await getWorkspaceSessionsAPI()
    if (response.data.status_code === 200) {
      sessions.value = (response.data.data || []).map((session: any) => ({
        sessionId: session.session_id || session.id,
        title: session.title || '未命名会话',
        createTime: session.create_time || session.created_at || '',
        agent: session.agent || 'simple'
      }))
    }
  } catch (error) {
    console.error('获取会话列表出错:', error)
  } finally {
    loading.value = false
  }
}

const selectSession = (sessionId: string) => {
  selectedSession.value = sessionId
  router.push({ path: '/', query: { session_id: sessionId } })
}

const deleteSession = async (sessionId: string, event: Event) => {
  event.stopPropagation()
  try {
    const response = await deleteWorkspaceSessionAPI(sessionId)
    if (response.data.status_code === 200) {
      ElMessage.success('会话已删除')
      await fetchSessions()
      if (selectedSession.value === sessionId) {
        selectedSession.value = ''
        router.push({ path: '/' })
      }
    } else {
      ElMessage.error('删除会话失败')
    }
  } catch (error) {
    console.error('删除会话出错:', error)
    ElMessage.error('删除会话失败')
  }
}

const newChat = () => {
  selectedSession.value = ''
  router.push({ path: '/' })
}

// 会话在聊天页产生后刷新列表（聊天页派发自定义事件）
const onSessionsRefresh = () => fetchSessions()

// ---------- 导航 ----------
const isActive = (item: { key: string; route: string }) => {
  if (item.key === 'chat') {
    return route.path === '/' || route.path === ''
  }
  return route.path.startsWith(item.route)
}

// ---------- 账号 ----------
const handleUserCommand = async (command: string) => {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'logout') {
    try {
      await logoutAPI()
    } catch (error) {
      console.error('调用登出接口失败:', error)
    }
    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  }
}

const handleAvatarError = (event: Event) => {
  const target = event.target as HTMLImageElement
  if (target) {
    target.src = '/src/assets/user.svg'
  }
}

onMounted(async () => {
  userStore.initUserState()
  await fetchSessions()
  window.addEventListener('kbqa:refresh-sessions', onSessionsRefresh)
})

onBeforeUnmount(() => {
  window.removeEventListener('kbqa:refresh-sessions', onSessionsRefresh)
})

// 会话选中态跟随路由
watch(
  () => route.query.session_id,
  (sid) => {
    if (sid) selectedSession.value = String(sid)
  },
  { immediate: true }
)
</script>

<template>
  <div class="app-shell">
    <!-- 侧边栏 -->
    <aside class="side-nav">
      <!-- 品牌 -->
      <div class="brand">
        <div class="brand-mark">KB</div>
        <span class="brand-name">KBQA</span>
      </div>

      <!-- 新建对话 -->
      <button class="new-chat-btn" @click="newChat">
        <span class="plus">＋</span> 新建对话
      </button>

      <!-- 模块导航 -->
      <nav class="nav">
        <button
          v-for="item in navItems"
          :key="item.key"
          :class="['nav-item', { active: isActive(item) }]"
          @click="router.push(item.route)"
        >
          {{ item.label }}
        </button>
      </nav>

      <!-- 会话历史 -->
      <div class="sessions">
        <div class="sessions-label">会话历史</div>
        <div v-if="loading" class="sessions-hint">加载中…</div>
        <div v-else-if="sessions.length === 0" class="sessions-empty">
          暂无会话记录
        </div>
        <div
          v-for="session in sessions"
          :key="session.sessionId"
          :class="['session-item', { active: selectedSession === session.sessionId }]"
          @click="selectSession(session.sessionId)"
        >
          <div class="session-meta">
            <div class="session-title">{{ session.title }}</div>
            <div class="session-time">{{ formatTime(session.createTime) }}</div>
          </div>
          <button
            class="session-del"
            title="删除会话"
            @click="deleteSession(session.sessionId, $event)"
          >×</button>
        </div>
      </div>

      <!-- 底部账号 -->
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
        >GitHub</a>
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

/* ---------- 侧边栏 ---------- */
.side-nav {
  display: flex;
  flex-direction: column;
  width: 232px;
  flex-shrink: 0;
  background: var(--color-panel);
  border-right: 1px solid var(--color-edge);
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 14px 12px;

  .brand-mark {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 7px;
    background: rgba(91, 157, 255, 0.14);
    border: 1px solid rgba(91, 157, 255, 0.3);
    font-family: var(--font-mono);
    font-size: 12px;
    font-weight: 700;
    color: var(--color-brand);
  }

  .brand-name {
    font-family: var(--font-mono);
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 1.5px;
    color: var(--color-ink);
  }
}

.new-chat-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0 12px 10px;
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-ink);
  background: var(--color-panel-2);
  border: 1px solid var(--color-edge);
  border-radius: 9px;
  cursor: pointer;
  transition: all 0.12s ease;

  .plus {
    color: var(--color-brand);
    font-weight: 600;
  }

  &:hover {
    border-color: var(--color-brand);
    background: var(--color-hover);
  }
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 0 12px 10px;
  border-bottom: 1px solid var(--color-edge-soft);
}

.nav-item {
  padding: 7px 10px;
  text-align: left;
  font-size: 13px;
  color: var(--color-ink-2);
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.12s ease;

  &:hover {
    color: var(--color-ink);
    background: var(--color-hover);
  }

  &.active {
    color: var(--color-brand);
    background: rgba(91, 157, 255, 0.08);
    font-weight: 500;
  }
}

/* ---------- 会话历史 ---------- */
.sessions {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 12px 12px 8px;
}

.sessions-label {
  padding: 0 8px 8px;
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 2px;
  color: var(--color-ink-3);
}

.sessions-hint,
.sessions-empty {
  padding: 8px;
  font-size: 12px;
  color: var(--color-ink-3);
}

.session-item {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 10px;
  margin-bottom: 2px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.12s ease;

  &:hover {
    background: var(--color-hover);

    .session-del {
      opacity: 1;
    }
  }

  &.active {
    background: var(--color-hover);
    box-shadow: inset 2px 0 0 var(--color-brand);
  }
}

.session-meta {
  min-width: 0;
}

.session-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  color: var(--color-ink);
}

.session-time {
  margin-top: 2px;
  font-size: 11px;
  color: var(--color-ink-3);
}

.session-del {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  line-height: 18px;
  padding: 0;
  text-align: center;
  font-size: 14px;
  color: var(--color-ink-3);
  background: transparent;
  border: none;
  border-radius: 5px;
  opacity: 0;
  cursor: pointer;
  transition: all 0.12s ease;

  &:hover {
    color: var(--color-danger);
    background: rgba(248, 113, 113, 0.1);
  }
}

/* ---------- 底部账号 ---------- */
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
  margin-top: 4px;
  padding: 0 6px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--color-ink-3);
  text-decoration: none;

  &:hover {
    color: var(--color-ink-2);
  }
}

/* ---------- 内容区 ---------- */
.app-content {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  background: var(--color-bg);
}
</style>
