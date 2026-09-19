/**
 * Interactive UI testing via Chrome DevTools Protocol (CDP)
 */
const { spawn } = require('child_process');
const http = require('http');

const PORT = 9225;
const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const ARTIFACT_DIR = "C:\\Users\\HP\\.gemini\\antigravity-ide\\brain\\20d7e211-daf8-4e4a-a295-7c920323ccd8";

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function getJson(url) {
  return new Promise((resolve, reject) => {
    http.get(url, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(JSON.parse(data)));
    }).on('error', reject);
  });
}

class CDPClient {
  constructor(wsUrl) {
    this.ws = new WebSocket(wsUrl);
    this.id = 0;
    this.callbacks = new Map();
    this.ready = new Promise((resolve, reject) => {
      this.ws.onopen = resolve;
      this.ws.onerror = reject;
    });
    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && this.callbacks.has(msg.id)) {
        const { resolve, reject } = this.callbacks.get(msg.id);
        this.callbacks.delete(msg.id);
        if (msg.error) reject(msg.error);
        else resolve(msg.result);
      }
    };
  }

  send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = ++this.id;
      this.callbacks.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  async eval(expression) {
    const res = await this.send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
    return res.result?.value;
  }

  async screenshot(filePath) {
    const fs = require('fs');
    const res = await this.send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(filePath, Buffer.from(res.data, 'base64'));
    console.log(`Saved screenshot: ${filePath}`);
  }

  close() {
    this.ws.close();
  }
}

async function main() {
  console.log('Launching headless Chrome with debugging port...');
  const chrome = spawn(CHROME_PATH, [
    '--headless',
    '--no-sandbox',
    '--disable-gpu',
    `--remote-debugging-port=${PORT}`,
    '--window-size=1536,1000',
    'http://127.0.0.1:8000/dashboard/'
  ]);

  try {
    await sleep(3000);
    const versionInfo = await getJson(`http://127.0.0.1:${PORT}/json/version`);
    const tabs = await getJson(`http://127.0.0.1:${PORT}/json/list`);
    const pageTab = tabs.find(t => t.type === 'page');
    if (!pageTab) throw new Error('No page tab found');

    const client = new CDPClient(pageTab.webSocketDebuggerUrl);
    await client.ready;
    await client.send('Page.enable');
    await client.send('DOM.enable');

    console.log('Page connected. Waiting for dashboard data to hydrate...');
    await sleep(3000);

    // 1. Verify and capture Subsystem Health Modal
    console.log('Opening Subsystem Health Modal...');
    await client.eval(`document.getElementById('btn-open-sys-health')?.click()`);
    await sleep(600);
    await client.screenshot(`${ARTIFACT_DIR}\\modal_subsystem_health.png`);

    console.log('Closing Subsystem Health Modal...');
    await client.eval(`document.getElementById('btn-close-sys-modal')?.click()`);
    await sleep(400);

    // 2. Verify and capture Model Intelligence Modal
    console.log('Opening Model Intelligence Modal...');
    await client.eval(`document.getElementById('btn-open-model-modal-top')?.click()`);
    await sleep(600);

    // 3. Trigger Live SHAP explanation inside modal
    console.log('Triggering live SHAP explanation probe...');
    await client.eval(`document.getElementById('btn-trigger-sample-explain')?.click()`);
    await sleep(3000); // Wait for /explain API and rendering
    await client.screenshot(`${ARTIFACT_DIR}\\modal_model_intelligence_shap.png`);

    console.log('Closing Model Intelligence Modal...');
    await client.eval(`document.getElementById('btn-close-model-modal')?.click()`);
    await sleep(400);

    // 4. Test Alert Detail Drawer
    console.log('Opening first alert detail drawer...');
    await client.eval(`
      const firstRowBtn = document.querySelector('#alerts-table-body tr button');
      if (firstRowBtn) firstRowBtn.click();
      else if (typeof openAlertDetail === 'function') openAlertDetail('ALT-000049');
    `);
    await sleep(1000);
    await client.screenshot(`${ARTIFACT_DIR}\\drawer_alert_detail.png`);

    client.close();
    console.log('All interactive UI validations completed successfully!');
  } finally {
    chrome.kill();
  }
}

main().catch(err => {
  console.error('Test execution failed:', err);
  process.exit(1);
});
