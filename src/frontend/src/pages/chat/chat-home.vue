<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { MdPreview } from "md-editor-v3"
import "md-editor-v3/lib/style.css"
import { getWorkspacePluginsAPI, workspaceSimpleChatStreamAPI, type WorkSpaceSimpleTask } from '../../apis/workspace'
import { getVisibleLLMsAPI, type LLMResponse } from '../../apis/llm'
import { useUserStore } from '../../store/user'

const userStore = useUserStore()

const router = useRouter()
const route = useRoute()
const inputMessage = ref('')
const selectedMode = ref('normal')
const plugins = ref<any[]>([])
const showModelSelector = ref(false)
const showToolSelector = ref(false)
const showSearchSelector = ref(false)
const selectedModel = ref<string>('')
const selectedModelId = ref<string>('')
const selectedTools = ref<string[]>([])
const webSearchEnabled = ref(false)
const toolDropdownRef = ref<HTMLElement | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const currentSessionId = ref<string>('')  // 当前会话ID
const chatConversationRef = ref<HTMLElement | null>(null)  // 聊天容器引用
const isGenerating = ref(false)  // 是否正在生成回复

// 模型数据（来自应用中心"可见模型"）
const modelOptions = ref<LLMResponse[]>([])
const modelsLoading = ref(false)

// 本页对话消息（用户在上，AI在下）
const messages = ref<Array<{ role: 'user' | 'assistant'; content: string }>>([])

// 头像加载错误处理
const handleAvatarError = (event: Event) => {
  const target = event.target as HTMLImageElement
  if (target) {
    target.src = '/src/assets/user.svg'
  }
}



// 从接口加载模型
const fetchModels = async () => {
  modelsLoading.value = true
  try {
    const res = await getVisibleLLMsAPI()
    if (res.data && res.data.status_code === 200) {
      const grouped = res.data.data || {}
      const list: LLMResponse[] = []
      Object.values(grouped).forEach((arr: any) => {
        if (Array.isArray(arr)) list.push(...arr)
      })
      // 仅保留 LLM 类型
      modelOptions.value = list.filter(m => (m.llm_type || '').toUpperCase() === 'LLM')
      // 默认选择第一个
      if (!selectedModelId.value && modelOptions.value.length > 0) {
        selectedModelId.value = modelOptions.value[0].llm_id
        selectedModel.value = modelOptions.value[0].model
      }
    }
  } catch (e) {
    console.error('获取模型失败', e)
  } finally {
    modelsLoading.value = false
  }
}

// 获取可用插件
const fetchPlugins = async () => {
  try {
    const response = await getWorkspacePluginsAPI()
    if (response.data.status_code === 200) {
      plugins.value = response.data.data || []
    }
  } catch (error) {
    console.error('获取插件列表出错:', error)
  }
}

// 选择模型
const selectModel = (llmId: string) => {
  const model = modelOptions.value.find(m => m.llm_id === llmId)
  if (model) {
    selectedModelId.value = model.llm_id
    selectedModel.value = model.model
  }
  showModelSelector.value = false
}

// 切换工具选择
const toggleTool = (toolId: string) => {
  const index = selectedTools.value.indexOf(toolId)
  if (index > -1) {
    selectedTools.value.splice(index, 1)
  } else {
    selectedTools.value.push(toolId)
  }
}

// 切换联网搜索
const toggleWebSearch = () => {
  webSearchEnabled.value = !webSearchEnabled.value
  showSearchSelector.value = false
}

// 点击空白处关闭工具/MCP下拉
const handleClickOutside = (e: MouseEvent) => {
  const target = e.target as Node
  if (showToolSelector.value && toolDropdownRef.value && !toolDropdownRef.value.contains(target)) {
    showToolSelector.value = false
  }
}

// 触发文件选择
const triggerFileInput = () => {
  fileInputRef.value?.click()
}

// 处理文件选择
const onFileChange = (e: Event) => {
  const input = e.target as HTMLInputElement
  const files = input.files
  if (files && files.length > 0) {
    ElMessage.success(`已选择 ${files.length} 个文件`)
  }
  if (input) input.value = ''
}

// 切换 MCP 服务器选择

// 生成UUID（模拟Python的uuid4().hex）
const generateSessionId = (): string => {
  // 使用crypto.randomUUID()生成UUID，然后移除横杠
  return crypto.randomUUID().replace(/-/g, '')
}

// 自动滚动到底部
const scrollToBottom = () => {
  if (chatConversationRef.value) {
    setTimeout(() => {
      if (chatConversationRef.value) {
        chatConversationRef.value.scrollTop = chatConversationRef.value.scrollHeight
      }
    }, 100)
  }
}

// 发送消息
const handleSend = async () => {
  if (!inputMessage.value.trim()) {
    ElMessage.warning('请输入消息内容')
    return
  }

  // 如果正在生成回复，不允许发送新消息
  if (isGenerating.value) {
    ElMessage.warning('请等待当前回复完成')
    return
  }
  
  const query = inputMessage.value.trim()
  
  // 日常模式：在本页进行对话（流式）
  {
    
    if (!selectedModelId.value) {
      ElMessage.warning('请先选择模型')
      return
    }

    // 如果还没有session_id，生成一个新的
    if (!currentSessionId.value) {
      currentSessionId.value = generateSessionId()
    }

    // 立即清空输入框，提升用户体验
    inputMessage.value = ''
    
    // 设置正在生成状态（转圈）
    isGenerating.value = true

    // 将用户消息加入消息列表
    messages.value.push({ role: 'user' as const, content: query })
    
    // 自动滚动到底部
    scrollToBottom()
    
    // 预置一条AI消息用于流式累加（先添加到数组，然后通过索引更新以触发响应式）
    const aiMsgIndex = messages.value.length
    messages.value.push({ role: 'assistant', content: '' })

    try {
      const payload: WorkSpaceSimpleTask = {
        query,
        model_id: selectedModelId.value,
        plugins: selectedTools.value,
        session_id: currentSessionId.value  // 添加session_id参数
      }
      await workspaceSimpleChatStreamAPI(
        payload,
        (chunk) => {
          // 通过索引更新以触发 Vue 的响应式
          messages.value[aiMsgIndex].content += chunk
          // 每次收到新内容时自动滚动到底部
          scrollToBottom()
        },
        (err) => {
          console.error('日常模式流式出错', err)
          ElMessage.error('对话失败，请稍后重试')
          isGenerating.value = false  // 出错时解除生成状态
        },
        () => {
          isGenerating.value = false  // 完成时解除生成状态
          window.dispatchEvent(new CustomEvent('kbqa:refresh-sessions'))  // 通知侧栏刷新会话历史
        }
      )
    } catch (e) {
      console.error('日常模式对话异常', e)
      ElMessage.error('对话异常')
      isGenerating.value = false  // 异常时解除生成状态
    }
  }
}

// 键盘事件处理
const handleKeydown = (event: KeyboardEvent) => {
  // 直接回车发送，Shift+Enter 换行
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    // 如果正在生成，不响应回车
    if (!isGenerating.value) {
      handleSend()
    }
  }
}

// 加载会话历史
const loadSessionHistory = async (sessionId: string) => {
  try {
    // 导入 API
    const { getWorkspaceSessionsAPI } = await import('../../apis/workspace')
    const response = await getWorkspaceSessionsAPI()
    
    if (response.data.status_code === 200) {
      const session = response.data.data.find((s: any) => s.session_id === sessionId)
      
      if (session && session.contexts && Array.isArray(session.contexts)) {
        // 将 contexts 转换为 messages 格式
        messages.value = session.contexts.map((ctx: any) => [
          { role: 'user' as const, content: ctx.query || '' },
          { role: 'assistant' as const, content: ctx.answer || '' }
        ]).flat().filter((msg: any) => msg.content) // 过滤掉空内容
        
        
        // 加载历史后滚动到底部
        scrollToBottom()
      }
    }
  } catch (error) {
    console.error('加载会话历史失败:', error)
    ElMessage.error('加载会话历史失败')
  }
}

onMounted(async () => {
  fetchPlugins()
  fetchModels()
  
  // 检查是否有 session_id 参数，如果有则加载会话历史
  const sessionId = route.query.session_id as string
  if (sessionId) {
    currentSessionId.value = sessionId  // 设置当前会话ID
    await loadSessionHistory(sessionId)
  } else {
    // 如果没有session_id，生成一个新的
    currentSessionId.value = generateSessionId()
  }
  
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})

// 监听路由参数变化
watch(
  () => route.query.session_id,
  async (newSessionId, oldSessionId) => {
    if (newSessionId && newSessionId !== oldSessionId) {
      // 更新当前会话ID
      currentSessionId.value = newSessionId as string
      // 清空当前消息
      messages.value = []
      // 加载新会话的历史
      await loadSessionHistory(newSessionId as string)
    } else if (!newSessionId && oldSessionId) {
      // 如果从有session_id变为没有，生成新的session_id
      currentSessionId.value = generateSessionId()
      messages.value = []
    }
  }
)
</script>

<template>
  <div class="chat-page" :class="{ 'chat-active': messages.length > 0 }">
    <div class="chat-container">
      <!-- 欢迎区域（有对话时隐藏） -->
      <div v-if="messages.length === 0" class="welcome-section">
        <div class="brand-mark">KB</div>
        <h1 class="welcome-title">企业知识库智能问答</h1>
        <p class="welcome-subtitle">基于 RAG 检索增强与 Agent 工具调用，回答附带来源引用</p>
      </div>

      <!-- 对话历史（有对话时显示在上方） -->
      <div v-if="messages.length > 0" class="chat-conversation" ref="chatConversationRef">
        <div v-for="(msg, idx) in messages" :key="idx" class="message-group">
          <!-- User Message -->
          <div v-if="msg.role === 'user'" class="user-message">
            <div class="message-content">
              <span>{{ msg.content }}</span>
            </div>
            <img :src="userStore.userInfo?.avatar || '/src/assets/user.svg'" alt="User Avatar" class="avatar" @error="handleAvatarError" />
          </div>
          
          <!-- AI Message -->
          <div v-if="msg.role === 'assistant'" class="ai-message">
            <div class="ai-mark">KB</div>
            <div class="message-content">
              <!-- 加载转圈器 - 仅在内容为空且正在生成时显示 -->
              <div v-if="!msg.content && isGenerating && idx === messages.length - 1" class="loading-spinner-container">
                <div class="loading-spinner"></div>
                <span class="loading-text">AI正在思考中...</span>
              </div>
              <!-- 实际内容 - 有内容时显示 -->
              <MdPreview v-if="msg.content" :editorId="'workspace-ai-' + idx" :modelValue="msg.content" theme="dark" />
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域（固定在底部） -->
      <div class="input-section" :class="{ 'input-fixed': messages.length > 0 }">
        <div class="input-wrapper">
          <textarea
            v-model="inputMessage"
            placeholder="输入你的问题，例如：员工每月加班上限是多少？"
            class="message-input"
            rows="4"
            @keydown="handleKeydown"
          ></textarea>
          
          <!-- 底部控制栏 -->
          <div class="input-footer">
            <div class="footer-left">
              <!-- 模型选择（仅日常模式显示） -->
              <div v-if="selectedMode === 'normal'" class="selector-dropdown">
                <div 
                  :class="['selector-item', { open: showModelSelector }]"
                  @click="showModelSelector = !showModelSelector"
                >
                  <img src="../../assets/model.svg" alt="模型" class="selector-icon-img" />
                  <span class="selector-text">{{ selectedModel || (modelsLoading ? '加载中...' : '选择模型') }}</span>
                  <span class="selector-arrow">▲</span>
                </div>
                
                <!-- 模型下拉菜单 -->
                <transition name="dropdown">
                  <div v-if="showModelSelector" class="dropdown-menu model-menu">
                    <div v-if="modelsLoading" class="dropdown-empty">
                      <span class="empty-icon">⏳</span>
                      <span class="empty-text">正在加载模型...</span>
                    </div>
                    <div v-else-if="modelOptions.length === 0" class="dropdown-empty">
                      <img src="../../assets/model.svg" alt="模型" class="empty-icon-img" />
                      <span class="empty-text">暂无可用模型</span>
                    </div>
                    <div
                      v-for="m in modelOptions"
                      :key="m.llm_id"
                      :class="['dropdown-item', { selected: selectedModelId === m.llm_id }]"
                      @click="selectModel(m.llm_id)"
                    >
                      <div class="item-left">
                        <div class="item-icon-wrapper">
                          <img src="../../assets/model.svg" alt="模型" class="item-icon-img" />
                        </div>
                        <div class="item-content">
                          <div class="item-text">{{ m.model }}</div>
                        </div>
                      </div>
                      <div v-if="selectedModelId === m.llm_id" class="item-check-wrapper">
                        <span class="item-check">✓</span>
                      </div>
                    </div>
                  </div>
                </transition>
              </div>

                            
              <!-- 工具选择 -->
              <div class="selector-dropdown" ref="toolDropdownRef">
                <div 
                  class="selector-item"
                  @click="showToolSelector = !showToolSelector"
                >
                  <img src="../../assets/plugin.svg" alt="工具" class="selector-icon-img" />
                  <span class="selector-text">
                    {{ selectedTools.length > 0 ? `已选 ${selectedTools.length} 个` : '选择工具' }}
                  </span>
                  <span class="selector-arrow">▲</span>
                </div>
                
                <!-- 工具下拉菜单 -->
                <transition name="dropdown">
                  <div v-if="showToolSelector" class="dropdown-menu tool-menu">
                    <!-- 标题 -->
                    <div class="dropdown-header">
                      <span class="header-title">选择工具</span>
                      <span class="header-count">{{ plugins.length }} 个可用</span>
                    </div>

                    <!-- 工具列表 -->
                    <div class="dropdown-list">
                      <div v-if="plugins.length === 0" class="dropdown-empty">
                        <img src="../../assets/plugin.svg" alt="工具" class="empty-icon-img" />
                        <span class="empty-text">暂无可用工具</span>
                      </div>
                      <div
                        v-for="plugin in plugins"
                        :key="plugin.id || plugin.tool_id"
                        :class="['dropdown-item', { selected: selectedTools.includes(plugin.id || plugin.tool_id) }]"
                        @click="toggleTool(plugin.id || plugin.tool_id)"
                      >
                        <div class="item-left">
                          <div class="item-icon-wrapper">
                            <img 
                              v-if="plugin.logo_url" 
                              :src="plugin.logo_url" 
                              :alt="plugin.display_name"
                              class="item-icon-img"
                            />
                            <img v-else src="../../assets/plugin.svg" alt="工具" class="item-icon-img" />
                          </div>
                          <div class="item-content">
                            <div class="item-text">{{ plugin.display_name }}</div>
                            <div class="item-desc">{{ plugin.description || '暂无描述' }}</div>
                          </div>
                        </div>
                        <div 
                          v-if="selectedTools.includes(plugin.id || plugin.tool_id)" 
                          class="item-check-wrapper"
                        >
                          <span class="item-check">✓</span>
                        </div>
                      </div>
                    </div>

                    <!-- 底部操作栏 -->
                    <div v-if="selectedTools.length > 0" class="dropdown-footer">
                      <button 
                        class="clear-btn"
                        @click.stop="selectedTools = []"
                      >
                        <span>清空</span>
                      </button>
                      <div class="selected-info">
                        <span class="selected-count">已选 {{ selectedTools.length }} 个工具</span>
                      </div>
                    </div>
                  </div>
                </transition>
              </div>


            </div>
            
            <div class="footer-right">
              <!-- 附件按钮 -->
              <button class="icon-btn" title="上传附件" @click="triggerFileInput">
                <img src="../../assets/upload.svg" alt="上传" class="upload-icon" />
              </button>
              <input
                type="file"
                ref="fileInputRef"
                class="hidden-file-input"
                multiple
                @change="onFileChange"
              />
              
              <!-- 发送按钮 -->
              <button class="send-btn" :class="{ 'btn-disabled': isGenerating }" :disabled="isGenerating" @click="handleSend">
                <span v-if="!isGenerating">➤</span>
                <span v-else class="loading-spinner"></span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
/* ---------- 页面骨架 ---------- */
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  background: var(--color-bg);
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-width: 860px;
  margin: 0 auto;
  width: 100%;
  padding: 0 24px;
}

/* ---------- 欢迎区 ---------- */
.welcome-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding-top: 15vh;
}

.brand-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: rgba(91, 157, 255, 0.12);
  border: 1px solid rgba(91, 157, 255, 0.28);
  font-family: var(--font-mono);
  font-size: 20px;
  font-weight: 700;
  color: var(--color-brand);
}

.welcome-title {
  margin: 22px 0 0;
  font-size: 24px;
  font-weight: 600;
  letter-spacing: 0.5px;
  color: var(--color-ink);
}

.welcome-subtitle {
  margin: 10px 0 0;
  font-size: 13px;
  color: var(--color-ink-3);
}

/* ---------- 对话区 ---------- */
.chat-conversation {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 20px 4px 12px;
}

.message-group {
  margin-bottom: 22px;
}

.user-message {
  display: flex;
  justify-content: flex-end;
  gap: 10px;

  .message-content {
    max-width: 76%;
    padding: 10px 14px;
    background: var(--color-brand-dim);
    border: 1px solid rgba(91, 157, 255, 0.22);
    border-radius: 12px 12px 3px 12px;
    font-size: 14px;
    line-height: 1.65;
    color: var(--color-ink);
    white-space: pre-wrap;
  }

  .avatar {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    object-fit: cover;
    flex-shrink: 0;
  }
}

.ai-message {
  display: flex;
  gap: 10px;

  .ai-mark {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 30px;
    height: 30px;
    border-radius: 8px;
    background: rgba(91, 157, 255, 0.12);
    border: 1px solid rgba(91, 157, 255, 0.28);
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 700;
    color: var(--color-brand);
  }

  .message-content {
    max-width: 86%;
    padding: 12px 16px;
    background: var(--color-panel);
    border: 1px solid var(--color-edge-soft);
    border-radius: 3px 12px 12px 12px;
    font-size: 14px;
    line-height: 1.7;
    color: var(--color-ink);
    overflow-wrap: break-word;
  }
}

/* markdown 预览暗色适配 */
.message-content :deep(.md-editor-preview-wrapper) {
  padding: 0;
}
.message-content :deep(.md-editor-preview) {
  color: var(--color-ink);
  font-size: 14px;
}
.message-content :deep(p) {
  margin: 0 0 8px;
}
.message-content :deep(pre) {
  background: #0e1013;
  border: 1px solid var(--color-edge-soft);
  border-radius: 8px;
  padding: 12px;
  overflow-x: auto;
}
.message-content :deep(code) {
  font-family: var(--font-mono);
  font-size: 13px;
}
.message-content :deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
}
.message-content :deep(th),
.message-content :deep(td) {
  border: 1px solid var(--color-edge);
  padding: 6px 12px;
}

/* 加载态 */
.loading-spinner-container {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--color-ink-3);
  font-size: 13px;
}
.loading-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid var(--color-edge);
  border-top-color: var(--color-brand);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* ---------- 输入区 ---------- */
.input-section {
  flex-shrink: 0;
  padding: 14px 0 18px;
}

.input-wrapper {
  background: var(--color-panel);
  border: 1px solid var(--color-edge);
  border-radius: 14px;
  padding: 12px 14px 10px;
  transition: border-color 0.15s ease;

  &:focus-within {
    border-color: var(--color-brand);
  }
}

.message-input {
  width: 100%;
  resize: none;
  border: none;
  outline: none;
  background: transparent;
  color: var(--color-ink);
  font-family: var(--font-sans);
  font-size: 14px;
  line-height: 1.6;

  &::placeholder {
    color: var(--color-ink-3);
  }
}

.input-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}

.footer-left,
.footer-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ---------- 选择器（模型/工具） ---------- */
.selector-dropdown {
  position: relative;
}

.selector-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  font-size: 12px;
  color: var(--color-ink-2);
  background: var(--color-panel-2);
  border: 1px solid var(--color-edge);
  border-radius: 8px;
  cursor: pointer;
  user-select: none;
  transition: all 0.12s ease;

  &:hover,
  &.open {
    border-color: var(--color-brand);
    color: var(--color-ink);
  }
}

.selector-icon-img {
  width: 14px;
  height: 14px;
}

.selector-arrow {
  font-size: 9px;
  color: var(--color-ink-3);
}

.dropdown-menu {
  position: absolute;
  bottom: calc(100% + 6px);
  left: 0;
  z-index: 30;
  min-width: 260px;
  max-height: 320px;
  overflow-y: auto;
  background: var(--color-panel-2);
  border: 1px solid var(--color-edge);
  border-radius: 10px;
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.5);
}

.dropdown-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 12px;
  border-bottom: 1px solid var(--color-edge-soft);
}

.header-title {
  font-size: 12px;
  color: var(--color-ink);
}

.header-count {
  font-size: 11px;
  color: var(--color-ink-3);
}

.dropdown-list {
  padding: 5px;
}

.dropdown-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 7px 8px;
  border-radius: 7px;
  cursor: pointer;

  &:hover {
    background: var(--color-hover);
  }

  &.selected {
    background: rgba(91, 157, 255, 0.08);
  }
}

.item-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.item-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: var(--color-hover);
}

.item-icon-img {
  width: 14px;
  height: 14px;
}

.item-text {
  font-size: 13px;
  color: var(--color-ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-desc {
  font-size: 11px;
  color: var(--color-ink-3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 220px;
}

.item-check-wrapper {
  flex-shrink: 0;
}

.item-check {
  color: var(--color-brand);
  font-size: 12px;
}

.dropdown-empty {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 14px;
  font-size: 12px;
  color: var(--color-ink-3);
}

.dropdown-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-top: 1px solid var(--color-edge-soft);
}

.clear-btn {
  padding: 3px 10px;
  font-size: 12px;
  color: var(--color-ink-2);
  background: transparent;
  border: 1px solid var(--color-edge);
  border-radius: 6px;
  cursor: pointer;

  &:hover {
    color: var(--color-ink);
  }
}

.selected-count {
  font-size: 11px;
  color: var(--color-ink-3);
}

/* ---------- 右侧动作 ---------- */
.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  background: transparent;
  border: none;
  border-radius: 7px;
  cursor: pointer;
  transition: background 0.12s ease;

  &:hover {
    background: var(--color-hover);
  }
}

.upload-icon {
  width: 16px;
  height: 16px;
}

.hidden-file-input {
  display: none;
}

.send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  font-size: 14px;
  color: #0b0c0e;
  background: var(--color-brand);
  border: none;
  border-radius: 9px;
  cursor: pointer;
  transition: background 0.12s ease;

  &:hover {
    background: #79b1ff;
  }

  &.btn-disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

/* ---------- 下拉动画 ---------- */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.14s ease, transform 0.14s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
</style>
