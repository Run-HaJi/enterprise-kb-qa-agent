/**
 * KBQA 页面截图工具：本机 Chrome 无头渲染，完整单幅出图
 * 用法：node shot.js <路由路径> [输出文件名]
 * 示例：node shot.js /knowledge/t_xxx/files?name=员工制度 kb-files.png
 */
const puppeteer = require('puppeteer-core');

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const APP = 'http://127.0.0.1:8090';
const API = 'http://127.0.0.1:7860';

async function getToken() {
  const res = await fetch(`${API}/api/v1/user/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_name: 'demo_user', user_password: 'demo123456' })
  });
  const j = await res.json();
  return j.data.access_token;
}

(async () => {
  const route = '/' + (process.argv[2] || '').replace(/^\/+/, '');
  const out = process.argv[3] || `shot-${Date.now()}.png`;

  const token = await getToken();
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: 'new',
    args: ['--no-sandbox', '--hide-scrollbars']
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1 });

  // 同源注入登录态（应用从 localStorage 读 token）
  await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded' });
  await page.evaluate((t) => localStorage.setItem('token', t), token);

  await page.goto(`${APP}${route}`, { waitUntil: 'networkidle2', timeout: 30000 });
  await new Promise(r => setTimeout(r, 2000));

  await page.screenshot({ path: out });
  console.log('已输出:', out);
  await browser.close();
})();
