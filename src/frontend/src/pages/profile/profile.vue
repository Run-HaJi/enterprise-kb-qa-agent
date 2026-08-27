<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Edit, Upload, Check, Close } from '@element-plus/icons-vue'
import { useUserStore } from '../../store/user'
import { updateUserInfoAPI, getUserIconsAPI, getUserInfoAPI } from '../../apis/auth'

const userStore = useUserStore()

// 表单数据
const formData = ref({
  user_avatar: '',
  user_description: '该用户很懒，没有留下一片云彩'
})

// 测试按钮点击
const testButtonClick = () => {
  console.log('按钮被点击了！');
  alert('按钮被点击了！');
  confirmAvatarSelection();
}

// 页面状态
const loading = ref(false)
const iconsLoading = ref(false)
const editingDescription = ref(false)
const showAvatarDialog = ref(false)
const pageLoading = ref(true)
const uploading = ref(false)

// 头像相关
const availableIcons = ref<string[]>([])
const selectedAvatar = ref('')
const uploadRef = ref()

// 初始化数据
onMounted(async () => {
  await loadUserInfo()
  await loadAvailableIcons()
  pageLoading.value = false
})

// 获取用户信息
const loadUserInfo = async () => {
  try {
    const userId = userStore.userInfo?.id
    
    if (userId) {
      const response = await getUserInfoAPI(userId)
      
      if (response.data.status_code === 200) {
        const userInfo = response.data.data
        
        // 更新本地存储的用户信息，适配数据库字段
        const updatedInfo = {
          id: userInfo.user_id || userInfo.id,
          username: userInfo.user_name || userInfo.username,
          avatar: userInfo.user_avatar || userInfo.avatar,
          description: userInfo.user_description || userInfo.description
        }
        userStore.updateUserInfo(updatedInfo)
        
        // 更新表单数据
        formData.value = {
          user_avatar: userInfo.user_avatar || userInfo.avatar || '/src/assets/user.svg',
          user_description: userInfo.user_description || userInfo.description || '该用户很懒，没有留下一片云彩'
        }
        selectedAvatar.value = formData.value.user_avatar
      }
    } else {
      // 如果没有用户ID，使用本地存储的信息
      formData.value = {
        user_avatar: userStore.userInfo?.avatar || '/src/assets/user.svg',
        user_description: userStore.userInfo?.description || '该用户很懒，没有留下一片云彩'
      }
      selectedAvatar.value = formData.value.user_avatar
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
    // 使用本地存储的信息作为备选
    formData.value = {
      user_avatar: userStore.userInfo?.avatar || '/src/assets/user.svg',
      user_description: userStore.userInfo?.description || '该用户很懒，没有留下一片云彩'
    }
    selectedAvatar.value = formData.value.user_avatar
  }
}

// 获取可选头像
const loadAvailableIcons = async () => {
  iconsLoading.value = true
  try {
    const response = await getUserIconsAPI()
    // 修复：后端返回的是code，不是code
    if (response.data.status_code === 200) {
      availableIcons.value = response.data.data
    }
  } catch (error) {
    console.error('获取头像列表失败:', error)
    ElMessage.error('获取头像列表失败')
  } finally {
    iconsLoading.value = false
  }
}

// 选择头像
const selectAvatar = (avatarUrl: string) => {
  selectedAvatar.value = avatarUrl
}

// 确认选择头像
const confirmAvatarSelection = async () => {
  const userId = userStore.userInfo?.id
  if (!userId) {
    ElMessage.error('用户ID不存在')
    return
  }
  
  // 更新表单数据
  formData.value.user_avatar = selectedAvatar.value
  
  try {
    // 直接保存头像更改到服务器
    const response = await updateUserInfoAPI(
      userId,
      selectedAvatar.value,
      formData.value.user_description
    )
    
    if (response.data.status_code === 200) {
      // 更新本地用户信息
      userStore.updateUserInfo({
        avatar: selectedAvatar.value
      })
      
      showAvatarDialog.value = false
      ElMessage.success('头像更新成功')
    } else {
      ElMessage.error(response.data.status_message || '头像更新失败')
    }
  } catch (error) {
    console.error('头像更新失败:', error)
    ElMessage.error('头像更新失败')
  }
}

// 上传自定义头像
const handleUploadSuccess = async (response: any) => {
  // 后端直接返回图片链接字符串，格式为: data = "http........."
  const imageUrl = typeof response === 'string' ? response : response.data
  
  if (imageUrl) {
    // 只更新选中的头像，不立即保存到服务器
    selectedAvatar.value = imageUrl;
    uploading.value = false;
    ElMessage.success('头像上传成功，请点击"确定选择"保存');
  } else {
    ElMessage.error('上传失败，未获取到图片链接');
    uploading.value = false;
  }
}

// 上传前验证
const beforeUpload = (file: File) => {
  const isJPGOrPNG = file.type === 'image/jpeg' || file.type === 'image/png'
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isJPGOrPNG) {
    ElMessage.error('只能上传 JPG/PNG 格式的图片!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB!')
    return false
  }
  
  uploading.value = true
  return true
}

// 上传失败处理
const handleUploadError = (error: any) => {
  console.error('上传失败:', error)
  ElMessage.error('头像上传失败，请重试')
  uploading.value = false
}

// 保存用户信息
const saveUserInfo = async () => {
  loading.value = true
  try {
    const userId = userStore.userInfo?.id
    if (!userId) {
      ElMessage.error('用户ID不存在')
      return
    }
    
    const response = await updateUserInfoAPI(
      userId,
      formData.value.user_avatar,
      formData.value.user_description
    )
    
    if (response.data.status_code === 200) {
      // 更新本地用户信息，映射字段名
      userStore.updateUserInfo({
        avatar: formData.value.user_avatar,
        description: formData.value.user_description
      })
      
      ElMessage.success('保存成功')
      editingDescription.value = false
    } else {
      ElMessage.error(response.data.status_message || '保存失败')
    }
  } catch (error) {
    console.error('保存用户信息失败:', error)
    ElMessage.error('保存失败')
  } finally {
    loading.value = false
  }
}

// 编辑描述
const startEditDescription = () => {
  editingDescription.value = true
}

const cancelEditDescription = () => {
  editingDescription.value = false
  // 恢复原始值
  formData.value.user_description = userStore.userInfo?.description || '该用户很懒，没有留下一片云彩'
}

// 处理图片加载错误
const handleImageError = (event: Event) => {
  const target = event.target as HTMLImageElement
  target.src = '/src/assets/user.svg' // 设置默认头像
}

// 处理自定义上传
const handleCustomUpload = async (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (!input.files || input.files.length === 0) return;
  
  const file = input.files[0];
  
  // 验证文件类型
  const isJPGOrPNG = file.type === 'image/jpeg' || file.type === 'image/png';
  const isLt2M = file.size / 1024 / 1024 < 2;

  if (!isJPGOrPNG) {
    ElMessage.error('只能上传 JPG/PNG 格式的图片!');
    return;
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB!');
    return;
  }
  
  uploading.value = true;
  
  try {
    // 创建表单数据
    const formData = new FormData();
    formData.append('file', file);
    
    // 发送请求
    const response = await fetch('/api/v1/upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
      },
      body: formData
    });
    
    if (!response.ok) {
      throw new Error('上传失败');
    }
    
    const result = await response.json();
    
    // 处理响应
    handleUploadSuccess(result);
  } catch (error) {
    console.error('上传失败:', error);
    ElMessage.error('头像上传失败，请重试');
    uploading.value = false;
  }
};
</script>

<template>
  <div class="profile-page" v-loading="pageLoading">
    <div class="profile-header">
      <div>
        <h2>个人资料</h2>
        <p>管理您的个人信息和偏好设置</p>
      </div>
      <el-button type="primary" @click="loadUserInfo" :loading="pageLoading">
        刷新信息
      </el-button>
    </div>

    <div class="profile-content" v-if="!pageLoading">
      <div class="profile-card">
        <!-- 用户头像区域 -->
        <div class="avatar-section">
          <div class="avatar-container">
            <div class="avatar-wrapper">
              <img 
                :src="formData.user_avatar" 
                alt="用户头像"
                class="user-avatar"
                @error="handleImageError"
              />
              <div class="avatar-overlay" @click="showAvatarDialog = true">
                <el-icon><Edit /></el-icon>
              </div>
            </div>
          </div>
          
          <div class="user-basic-info">
            <h3>{{ userStore.userInfo?.nickname || userStore.userInfo?.username || '用户' }}</h3>
            <p class="user-id">ID: {{ userStore.userInfo?.id || '未知' }}</p>
          </div>
        </div>

        <!-- 用户描述区域 -->
        <div class="description-section">
          <div class="section-header">
            <h4>个人描述</h4>
            <el-button 
              v-if="!editingDescription"
              type="primary" 
              size="small" 
              :icon="Edit"
              @click="startEditDescription"
            >
              编辑
            </el-button>
          </div>
          
          <div v-if="!editingDescription" class="description-display">
            <p>{{ formData.user_description }}</p>
          </div>
          
          <div v-else class="description-edit">
            <el-input
              v-model="formData.user_description"
              type="textarea"
              :rows="4"
              placeholder="请输入个人描述"
              maxlength="200"
              show-word-limit
            />
            <div class="edit-actions">
              <el-button size="small" @click="cancelEditDescription">
                <el-icon><Close /></el-icon>
                取消
              </el-button>
              <el-button 
                type="primary" 
                size="small" 
                :loading="loading"
                @click="saveUserInfo"
              >
                <el-icon><Check /></el-icon>
                保存
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 头像选择对话框 -->
    <el-dialog
      v-model="showAvatarDialog"
      title="选择头像"
      width="600px"
      :close-on-click-modal="false"
      append-to-body
    >
      <div class="avatar-selection">
        <!-- 当前选中头像 -->
        <div class="current-selection">
          <h4>当前选择：</h4>
          <div class="selected-avatar">
            <img :src="selectedAvatar" alt="选中的头像" />
          </div>
        </div>

        <!-- 预设头像列表 -->
        <div class="preset-avatars">
          <h4>选择预设头像：</h4>
          <div class="avatar-grid">
            <div
              v-for="(icon, index) in availableIcons"
              :key="index"
              class="avatar-option"
              :class="{ active: selectedAvatar === icon }"
              @click="selectAvatar(icon)"
            >
              <img :src="icon" alt="头像选项" />
            </div>
          </div>
        </div>

        <!-- 上传自定义头像 -->
        <div class="upload-section">
          <h4>上传自定义头像：</h4>
          <el-upload
            ref="uploadRef"
            action="/api/v1/upload"
            :show-file-list="false"
            :on-success="handleUploadSuccess"
            :before-upload="beforeUpload"
            :on-error="handleUploadError"
            accept="image/*"
            :disabled="uploading"
          >
            <el-button type="primary" :icon="Upload" :loading="uploading">
              {{ uploading ? '上传中...' : '点击上传头像' }}
            </el-button>
          </el-upload>
          <p class="upload-tip">支持 JPG、PNG 格式，文件大小不超过 2MB</p>
        </div>
      </div>

      <template #footer>
        <el-button @click="showAvatarDialog = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="testButtonClick"
          :disabled="!selectedAvatar"
        >
          确定选择
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 自定义头像选择对话框 -->
    <div v-if="showAvatarDialog" class="custom-dialog-overlay">
      <div class="custom-dialog">
        <div class="custom-dialog-header">
          <h3>选择头像</h3>
          <button class="close-button" @click="showAvatarDialog = false">×</button>
        </div>
        
        <div class="custom-dialog-body">
          <!-- 当前选中头像 -->
          <div class="current-selection">
            <h4>当前选择：</h4>
            <div class="selected-avatar">
              <img :src="selectedAvatar" alt="选中的头像" />
            </div>
          </div>

          <div class="avatar-content">
            <!-- 预设头像列表 -->
            <div class="preset-avatars">
              <h4>选择预设头像：</h4>
              <div class="avatar-grid">
                <div
                  v-for="(icon, index) in availableIcons"
                  :key="index"
                  class="avatar-option"
                  :class="{ active: selectedAvatar === icon }"
                  @click="selectAvatar(icon)"
                >
                  <img :src="icon" alt="头像选项" />
                </div>
              </div>
            </div>

            <!-- 上传自定义头像 -->
            <div class="upload-section">
              <h4>上传自定义头像：</h4>
              <div class="upload-area">
                <label for="avatar-upload" class="upload-button">
                  <span v-if="!uploading">点击上传头像</span>
                  <span v-else>上传中...</span>
                </label>
                <input 
                  id="avatar-upload" 
                  type="file" 
                  accept="image/*" 
                  @change="handleCustomUpload" 
                  :disabled="uploading"
                  style="display: none;"
                />
                <p class="upload-tip">支持 JPG、PNG 格式，文件大小不超过 2MB</p>
              </div>
            </div>
          </div>
        </div>
        
        <div class="custom-dialog-footer">
          <button class="cancel-button" @click="showAvatarDialog = false">取消</button>
          <button 
            class="confirm-button" 
            @click="confirmAvatarSelection"
            :disabled="!selectedAvatar"
          >
            确定选择
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.profile-page {
  max-width: 860px;
  margin: 0 auto;
  padding: 28px 24px;
}

.profile-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 22px;

  h2 {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    color: var(--color-ink);
  }

  p {
    margin: 6px 0 0;
    font-size: 13px;
    color: var(--color-ink-3);
  }
}

.profile-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.profile-card {
  background: var(--color-panel);
  border: 1px solid var(--color-edge);
  border-radius: 12px;
  padding: 24px;
}

/* 头像区 */
.avatar-section {
  display: flex;
  align-items: center;
  gap: 18px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--color-edge-soft);
}

.avatar-wrapper {
  position: relative;
  width: 72px;
  height: 72px;
}

.user-avatar {
  width: 72px;
  height: 72px;
  border-radius: 12px;
  object-fit: cover;
  border: 1px solid var(--color-edge);
}

.avatar-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.45);
  color: #fff;
  opacity: 0;
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.avatar-wrapper:hover .avatar-overlay {
  opacity: 1;
}

.user-basic-info {
  h3 {
    margin: 0;
    font-size: 17px;
    font-weight: 600;
    color: var(--color-ink);
  }
}

.user-id {
  margin: 6px 0 0;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--color-ink-3);
}

/* 描述区 */
.description-section {
  padding-top: 18px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;

  h4 {
    margin: 0;
    font-size: 14px;
    font-weight: 600;
    color: var(--color-ink-2);
  }
}

.description-display {
  padding: 12px 14px;
  background: var(--color-panel-2);
  border: 1px solid var(--color-edge-soft);
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.7;
  color: var(--color-ink-2);
  min-height: 44px;
}

.description-edit {
  .el-textarea__inner {
    background: var(--color-panel-2);
  }
}

.edit-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

/* 头像选择弹窗 */
.custom-dialog-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
}

.custom-dialog {
  width: 520px;
  max-width: 92vw;
  background: var(--color-panel-2);
  border: 1px solid var(--color-edge);
  border-radius: 14px;
  overflow: hidden;
}

.custom-dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid var(--color-edge-soft);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink);
}

.close-button {
  background: none;
  border: none;
  color: var(--color-ink-3);
  font-size: 16px;
  cursor: pointer;

  &:hover {
    color: var(--color-ink);
  }
}

.custom-dialog-body {
  padding: 18px;
}

.avatar-content {
  .upload-section {
    margin-bottom: 18px;
  }

  .upload-button {
    width: 100%;
  }

  .upload-tip {
    margin: 8px 0 0;
    font-size: 12px;
    color: var(--color-ink-3);
    text-align: center;
  }
}

.avatar-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 10px;
}

.avatar-option {
  aspect-ratio: 1;
  border-radius: 10px;
  overflow: hidden;
  border: 1.5px solid var(--color-edge);
  cursor: pointer;
  transition: all 0.12s ease;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  &:hover {
    border-color: var(--color-brand);
  }

  &.selected-avatar {
    border-color: var(--color-brand);
    box-shadow: 0 0 0 2px rgba(91, 157, 255, 0.25);
  }
}

.current-selection {
  margin-top: 14px;
  font-size: 12px;
  color: var(--color-ink-3);
  text-align: center;
}

.custom-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 18px;
  border-top: 1px solid var(--color-edge-soft);
}
</style>
