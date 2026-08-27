<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const modules = [
  {
    key: 'workspace',
    title: '对话工作台',
    desc: '发起问答，流式回答附带知识库来源引用',
    route: '/workspace',
    accent: '#5b9dff',
    icon: '💬'
  },
  {
    key: 'knowledge',
    title: '知识库管理',
    desc: '上传 PDF / Word / TXT，自动解析分块并向量化',
    route: '/knowledge',
    accent: '#34d399',
    icon: '📚'
  },
  {
    key: 'agent',
    title: '智能体管理',
    desc: '配置模型、工具与知识库绑定的专属 Agent',
    route: '/agent',
    accent: '#fbbf24',
    icon: '🤖'
  },
  {
    key: 'model',
    title: '模型管理',
    desc: '维护对话 / 工具调用 / 推理 / 向量化模型接入',
    route: '/model',
    accent: '#f87171',
    icon: '🧠'
  },
  {
    key: 'tool',
    title: '工具管理',
    desc: '查看内置插件工具与自定义 OpenAPI 工具',
    route: '/tool',
    accent: '#a78bfa',
    icon: '🧩'
  },
  {
    key: 'profile',
    title: '个人资料',
    desc: '头像、昵称与个人描述设置',
    route: '/profile',
    accent: '#94a3b8',
    icon: '👤'
  }
]

const go = (route: string) => {
  router.push(route)
}

const goWorkspace = () => {
  router.push('/workspace')
}
</script>

<template>
  <div class="app-center">
    <!-- 头部 -->
    <div class="hero">
      <h1>应用中心</h1>
      <p>选择一个模块开始工作，或直接发起一次知识库问答</p>
      <el-button type="primary" size="large" class="quick-ask" @click="goWorkspace">
        发起问答 →
      </el-button>
    </div>

    <!-- 模块网格 -->
    <div class="module-grid">
      <button
        v-for="m in modules"
        :key="m.key"
        class="module-card"
        @click="go(m.route)"
      >
        <div class="card-icon" :style="{ color: m.accent, borderColor: m.accent + '44', background: m.accent + '14' }">
          {{ m.icon }}
        </div>
        <div class="card-title">{{ m.title }}</div>
        <div class="card-desc">{{ m.desc }}</div>
        <div class="card-arrow">→</div>
      </button>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.app-center {
  max-width: 960px;
  margin: 0 auto;
  padding: 48px 28px;
}

.hero {
  text-align: center;
  margin-bottom: 40px;

  h1 {
    margin: 0;
    font-size: 24px;
    font-weight: 600;
    color: var(--color-ink);
  }

  p {
    margin: 10px 0 0;
    font-size: 13px;
    color: var(--color-ink-3);
  }
}

.quick-ask {
  margin-top: 20px;
}

.module-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 14px;
}

.module-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  padding: 20px;
  text-align: left;
  background: var(--color-panel);
  border: 1px solid var(--color-edge);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    border-color: var(--color-brand);
    background: var(--color-hover);
    transform: translateY(-2px);

    .card-arrow {
      opacity: 1;
      transform: translateX(0);
    }
  }
}

.card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  font-size: 18px;
  border-radius: 10px;
  border: 1px solid;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-ink);
}

.card-desc {
  font-size: 12px;
  line-height: 1.6;
  color: var(--color-ink-3);
}

.card-arrow {
  position: absolute;
  right: 16px;
  top: 20px;
  font-size: 13px;
  color: var(--color-brand);
  opacity: 0;
  transform: translateX(-4px);
  transition: all 0.15s ease;
}
</style>
