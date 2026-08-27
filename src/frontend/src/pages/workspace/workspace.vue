<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, SwitchButton, Setting } from '@element-plus/icons-vue'
import workspaceIcon from '../../assets/workspace.svg'
import applicationCenterIcon from '../../assets/application-center.svg'
import dialogIcon from '../../assets/dialog.svg'
import robotIcon from '../../assets/robot.svg'
import pluginIcon from '../../assets/plugin.svg'
import knowledgeIcon from '../../assets/knowledge.svg'
import modelIcon from '../../assets/model.svg'
import { useUserStore } from '../../store/user'
import { logoutAPI, getUserInfoAPI } from '../../apis/auth'
import { 
  getWorkspaceSessionsAPI, 
  deleteWorkspaceSessionAPI 
} from '../../apis/workspace'

const router = useRouter()
import { useRoute } from 'vue-router'
const route = useRoute()
const userStore = useUserStore()
const selectedSession = ref('')
const sessions = ref<any[]>([])
const loading = ref(false)

// 格式化时间
const formatTime = (timeStr: string) => {
  try {
    if (!timeStr) return '未知时间'
    
    const date = new Date(timeStr)
    if (isNaN(date.getTime())) {
      return '未知时间'
    }
    
    const now = new Date()
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)
    
    if (diffInHours < 1) return '刚刚'
    if (diffInHours < 24) return `${Math.floor(diffInHours)}小时前`
    if (diffInHours < 24 * 7) return `${Math.floor(diffInHours / 24)}天前`
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  } catch (error) {
    return '未知时间'
  }
}

// 获取会话列表
const fetchSessions = async () => {
  try {
    loading.value = true
    const response = await getWorkspaceSessionsAPI()
    if (response.data.status_code === 200) {
      sessions.value = response.data.data.map((session: any) => ({
        sessionId: session.session_id || session.id,
        title: session.title || '未命名会话',
        createTime: session.create_time || session.created_at || new Date().toISOString(),
        agent: session.agent || 'lingseek', // 保存agent类型，默认为lingseek
        contexts: session.contexts || [] // 保存上下文
      }))
      console.log('工作区会话列表:', sessions.value)
    } else {
      ElMessage.error('获取会话列表失败')
    }
  } catch (error) {
    console.error('获取会话列表出错:', error)
    ElMessage.error('获取会话列表失败')
  } finally {
    loading.value = false
  }
}

// 删除会话
const deleteSession = async (sessionId: string, event: Event) => {
  event.stopPropagation()
  
  try {
    const response = await deleteWorkspaceSessionAPI(sessionId)
    if (response.data.status_code === 200) {
      ElMessage.success('会话删除成功')
      await fetchSessions()
      
      if (selectedSession.value === sessionId) {
        selectedSession.value = ''
        router.push('/workspace')
      }
    } else {
      ElMessage.error('删除会话失败')
    }
  } catch (error) {
    console.error('删除会话出错:', error)
    ElMessage.error('删除会话失败')
  }
}

// 选择会话 - 根据agent类型跳转到不同页面
const selectSession = (sessionId: string) => {
  selectedSession.value = sessionId
  
  // 找到对应的会话
  const session = sessions.value.find(s => s.sessionId === sessionId)
  
  if (!session) {
    console.error('未找到会话:', sessionId)
    return
  }
  
  console.log('选择会话:', sessionId, '类型:', session.agent)
  
  // 根据agent类型判断跳转页面
  // 统一跳转到日常对话页面，并传递session_id
  router.push({
    name: 'workspaceDefaultPage',
    query: {
      session_id: sessionId
    }
  })
}

// 用户下拉菜单命令处理
const handleUserCommand = async (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      router.push('/configuration')
      break
    case 'logout':
      await handleLogout()
      break
  }
}

// 退出登录
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

// 跳转到应用中心
const goToHomepage = () => {
  router.push('/homepage')
}

// 跳转到工作台（当前页）
const goToWorkspace = () => {
  router.push('/workspace')
}

// 应用中心下拉（与首页保持一致）
const showAppCenterMenu = ref(false)
let appCenterHoverTimer: any = null

const openAppCenterMenu = () => {
  if (appCenterHoverTimer) clearTimeout(appCenterHoverTimer)
  showAppCenterMenu.value = true
}

const closeAppCenterMenu = () => {
  if (appCenterHoverTimer) clearTimeout(appCenterHoverTimer)
  appCenterHoverTimer = setTimeout(() => {
    showAppCenterMenu.value = false
  }, 120)
}

const appCenterColumns = ref([
  [
    { label: '会话', icon: dialogIcon, route: '/conversation' },
    { label: '工作台', icon: workspaceIcon, route: '/workspace' }
  ],
  [
    { label: '智能体', icon: robotIcon, route: '/agent' },
    { label: '工具', icon: pluginIcon, route: '/tool' }
  ],
  [
    { label: '知识库', icon: knowledgeIcon, route: '/knowledge' },
    { label: '模型', icon: modelIcon, route: '/model' }
  ],
  [
  ]
])

// 顶栏按钮激活态（工作台页自身）
const isWorkspaceActive = computed(() => route.path.startsWith('/workspace'))
const isAppCenterActive = computed(() => route.path.startsWith('/homepage'))

onMounted(async () => {
  userStore.initUserState()
  
  // 如果已登录但没有头像，则尝试获取用户信息
  if (userStore.isLoggedIn && userStore.userInfo && !userStore.userInfo.avatar) {
    try {
      const response = await getUserInfoAPI(userStore.userInfo.id)
      if (response.data.status_code === 200 && response.data.data) {
        const userData = response.data.data
        userStore.updateUserInfo({
          avatar: userData.user_avatar || userData.avatar || '/src/assets/user.svg',
          description: userData.user_description || userData.description
        })
      }
    } catch (error) {
      console.error('初始化时获取用户信息失败:', error)
    }
  }
  
  await fetchSessions()
})
</script>

<template>
  <div class="workspace-container">
    <!-- 顶栏 -->
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark">KB</div>
        <div class="brand-text">
          <span class="brand-name">KBQA</span>
          <span class="brand-sub">企业知识库智能问答</span>
        </div>
      </div>
      <div class="topbar-right">
        <button class="ghost-btn" @click="goToHomepage">
          <span>应用中心</span>
        </button>
        <el-dropdown @command="handleUserCommand" trigger="click">
          <div class="avatar-wrap" title="账号">
            <img
              :src="userStore.userInfo?.avatar || '/src/assets/user.svg'"
              alt="用户头像"
              @error="handleAvatarError"
              referrerpolicy="no-referrer"
            />
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile" :icon="User">个人资料</el-dropdown-item>
              <el-dropdown-item divided command="logout" :icon="SwitchButton">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <div class="workspace-body">
      <!-- 会话侧栏 -->
      <aside class="sidebar">
        <div class="sidebar-label">会话</div>

        <div v-if="loading" class="side-hint">正在加载会话…</div>

        <div v-else-if="sessions.length === 0" class="side-empty">
          <div class="empty-ring"></div>
          <p>暂无会话记录</p>
          <span>发起一次对话后显示在这里</span>
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
          <button class="session-del" title="删除会话" @click="deleteSession(session.sessionId, $event)">×</button>
        </div>
      </aside>

      <!-- 内容区 -->
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.workspace-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--color-bg);
  color: var(--color-ink);
}

/* ---------- 顶栏 ---------- */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 52px;
  flex-shrink: 0;
  padding: 0 16px;
  background: var(--color-panel);
  border-bottom: 1px solid var(--color-edge);
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

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

.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.brand-name {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 1px;
  color: var(--color-ink);
}

.brand-sub {
  font-size: 11px;
  color: var(--color-ink-3);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ghost-btn {
  padding: 5px 12px;
  font-size: 12px;
  color: var(--color-ink-2);
  background: transparent;
  border: 1px solid var(--color-edge);
  border-radius: 7px;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    color: var(--color-ink);
    background: var(--color-hover);
  }
}

.avatar-wrap {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  overflow: hidden;
  border: 1px solid var(--color-edge);
  cursor: pointer;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

/* ---------- 主体 ---------- */
.workspace-body {
  display: flex;
  flex: 1;
  min-height: 0;
}

/* ---------- 会话侧栏 ---------- */
.sidebar {
  display: flex;
  flex-direction: column;
  width: 248px;
  flex-shrink: 0;
  padding: 14px 10px;
  background: var(--color-panel);
  border-right: 1px solid var(--color-edge);
  overflow-y: auto;
}

.sidebar-label {
  padding: 0 8px 10px;
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 2px;
  color: var(--color-ink-3);
}

.side-hint {
  padding: 12px 8px;
  font-size: 12px;
  color: var(--color-ink-3);
}

.side-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 42px 10px;
  text-align: center;

  p {
    margin: 0;
    font-size: 13px;
    color: var(--color-ink-2);
  }

  span {
    font-size: 11px;
    color: var(--color-ink-3);
  }
}

.empty-ring {
  width: 34px;
  height: 34px;
  margin-bottom: 6px;
  border: 1.5px dashed var(--color-edge);
  border-radius: 50%;
}

.session-item {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 9px 10px;
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

/* ---------- 内容区 ---------- */
.content {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  background: var(--color-bg);
}
</style>
