import { createApp } from 'vue'
import App from './App.vue'
import router from './router';
import { createPinia } from 'pinia'
import persistState from 'pinia-plugin-persistedstate';

// Element Plus CSS（先于全局主题，便于后者覆盖）
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import './style.css'


const app = createApp(App)
app.config.errorHandler = (err: any, _inst, info) => {
  document.title = 'VUEERR: ' + (err?.message || String(err)) + ' @' + info
}
const pinia = createPinia();
pinia.use(persistState);

app.use(router);
app.use(pinia);
app.mount('#app')
