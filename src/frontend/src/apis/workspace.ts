import { request } from '../utils/request'
import { fetchEventSource } from '@microsoft/fetch-event-source'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

// 获取工作区插件列表
export const getWorkspacePluginsAPI = async () => {
  return request({
    url: '/api/v1/workspace/plugins',
    method: 'get'
  })
}

// 获取工作区会话列表
export const getWorkspaceSessionsAPI = async () => {
  return request({
    url: '/api/v1/workspace/session',
    method: 'get'
  })
}

// 创建工作区会话
export const createWorkspaceSessionAPI = async (data: { title?: string, contexts?: any }) => {
  return request({
    url: '/api/v1/workspace/session',
    method: 'post',
    data
  })
}

// 获取工作区会话信息
export const getWorkspaceSessionInfoAPI = async (sessionId: string) => {
  return request({
    url: `/api/v1/workspace/session/${sessionId}`,
    method: 'post'
  })
}

// 删除工作区会话  
export const deleteWorkspaceSessionAPI = async (sessionId: string) => {
  return request({
    url: `/api/v1/workspace/session`,
    method: 'delete',
    params: {
      session_id: sessionId
    }
  })
}

// 工作区日常对话接口
export interface WorkSpaceSimpleTask {
  query: string
  model_id: string
  plugins: string[]
  session_id?: string  // 会话ID，使用uuid4().hex格式
}

export const workspaceSimpleChatAPI = async (data: WorkSpaceSimpleTask) => {
  return request({
    url: '/api/v1/workspace/simple/chat',
    method: 'post',
    data,
    responseType: 'stream'
  })
}

// 工作区日常对话（SSE 流式）
export const workspaceSimpleChatStreamAPI = async (
  data: WorkSpaceSimpleTask,
  onMessage: (chunk: string) => void,
  onError?: (err: any) => void,
  onClose?: () => void
) => {
  const token = localStorage.getItem('token')
  const ctrl = new AbortController()


  try {
    await fetchEventSource(`${BASE_URL}/api/v1/workspace/simple/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      },
      body: JSON.stringify(data),
      signal: ctrl.signal,
      openWhenHidden: true,
      onmessage(event) {
        if (!event.data) return
        try {
          const parsed = JSON.parse(event.data)
          // 兼容后端返回 {event:'task_result', data:{message}} 或 {data:{chunk}}
          if (parsed?.data?.message !== undefined) {
            // 只有当 message 不为空字符串时才调用回调
            if (parsed.data.message !== '') {
              onMessage(parsed.data.message)
            } else {
            }
          } else if (parsed?.data?.chunk !== undefined) {
            if (parsed.data.chunk !== '') {
              onMessage(parsed.data.chunk)
            } else {
            }
          } else {
            console.warn('⚠️ 未识别的数据格式，跳过')
          }
        } catch (_) {
          console.warn('⚠️ JSON 解析失败，跳过:', event.data)
        }
      },
      onerror(err) {
        console.error('❌ SSE 错误:', err)
        onError?.(err)
        ctrl.abort()
      },
      onclose() {
        onClose?.()
      }
    })
  } catch (error: any) {
    console.error('❌ fetchEventSource 异常:', error)
    if (error?.name !== 'AbortError') {
      onError?.(error)
    }
  }
}
