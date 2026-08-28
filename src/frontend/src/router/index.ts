// router/index.ts
import { createRouter, createWebHistory } from 'vue-router';
import NotFound from '../pages/notFound/index';
import Index from '../pages/index.vue'
import ChatHome from '../pages/chat/chat-home.vue';
import Login from '../pages/login'
import { Register } from '../pages/login'
import Agent from '../pages/agent'
import AgentEditor from '../pages/agent/agent-editor.vue'
import Knowledge from '../pages/knowledge'
import KnowledgeFile from '../pages/knowledge/knowledge-file.vue'
import Tool from '../pages/tool'
import Model from '../pages/model'
import ModelEditor from '../pages/model/model-editor.vue'
import Profile from '../pages/profile'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: Login,
    meta: {
      requiresAuth: false
    }
  },
  {
    path: '/register',
    name: 'register',
    component: Register,
    meta: {
      requiresAuth: false
    }
  },
  {
    // 统一应用壳：侧边栏（品牌/新建对话/模块导航/会话历史/账号）
    path: '/',
    name: 'shell',
    component: Index,
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: '',
        name: 'chat',
        component: ChatHome,
        meta: {
          current: 'chat'
        }
      },
      {
        path: 'agent',
        name: 'agent',
        meta: {
          current: 'agent'
        },
        component: Agent,
      },
      {
        path: 'agent/editor',
        name: 'agent-editor',
        meta: {
          current: 'agent'
        },
        component: AgentEditor,
      },
      {
        path: 'knowledge',
        name: 'knowledge',
        meta: {
          current: 'knowledge'
        },
        component: Knowledge,
      },
      {
        path: 'knowledge/:knowledgeId/files',
        name: 'knowledge-file',
        meta: {
          current: 'knowledge'
        },
        component: KnowledgeFile,
      },
      {
        path: 'tool',
        name: 'tool',
        meta: {
          current: 'tool'
        },
        component: Tool,
      },
      {
        path: 'model',
        name: 'model',
        meta: {
          current: 'model'
        },
        component: Model,
      },
      {
        path: 'model/editor',
        name: 'model-editor',
        meta: {
          current: 'model'
        },
        component: ModelEditor,
      },
      {
        path: 'profile',
        name: 'profile',
        meta: {
          current: 'profile'
        },
        component: Profile,
      },
    ]
  },
  {
    // 兼容旧地址
    path: '/workspace',
    redirect: '/',
  },
  {
    path: '/:catchAll(.*)',
    name: 'not-found',
    component: NotFound,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes: routes as RouteRecordRaw[],
});

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token');

  // 如果目标路由需要认证
  if (to.meta.requiresAuth) {
    if (token) {
      // 已登录，允许访问
      next();
    } else {
      // 未登录，跳转到登录页
      next('/login');
    }
  } else {
    // 不需要认证的路由（如登录页）
    if (to.path === '/login' && token) {
      // 已登录用户访问登录页，重定向到主页
      next('/');
    } else {
      next();
    }
  }
});

export default router;
