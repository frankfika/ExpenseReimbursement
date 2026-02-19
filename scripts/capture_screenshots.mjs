#!/usr/bin/env node
/**
 * 报销助手截图脚本
 * 自动捕获应用界面截图用于 README 展示
 */

import { chromium } from 'playwright';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootDir = join(__dirname, '..');
const assetsDir = join(rootDir, 'docs', 'assets');

// 截图配置
const VIEWPORT = { width: 1280, height: 800 };

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function captureScreenshot(page, name, options = {}) {
  const path = join(assetsDir, `${name}.png`);
  const { width = VIEWPORT.width, height = VIEWPORT.height, wait = 1000, fullPage = false } = options;

  await page.setViewportSize({ width, height });
  await sleep(wait);

  await page.screenshot({
    path,
    fullPage,
    type: 'png'
  });

  console.log(`📸 截图已保存: ${path}`);
  return path;
}

async function captureScreenshots() {
  console.log('🚀 启动截图工具...\n');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: VIEWPORT,
    deviceScaleFactor: 2 // 高清截图
  });
  const page = await context.newPage();

  try {
    // 1. 主界面截图 (home.png)
    console.log('📷 正在创建主界面...');
    await page.setContent(`
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <style>
          * { margin: 0; padding: 0; box-sizing: border-box; }
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
          }
          .header {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
          }
          .logo { font-size: 24px; font-weight: 700; color: white; }
          .nav { display: flex; gap: 30px; }
          .nav a { color: rgba(255,255,255,0.8); text-decoration: none; font-size: 14px; }
          .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 40px;
          }
          .hero {
            text-align: center;
            color: white;
            margin-bottom: 50px;
          }
          .hero h1 { font-size: 48px; margin-bottom: 16px; }
          .hero p { font-size: 18px; opacity: 0.9; }
          .upload-zone {
            background: rgba(255,255,255,0.95);
            border-radius: 20px;
            padding: 60px 80px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 600px;
            width: 100%;
          }
          .upload-icon {
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 24px;
            font-size: 40px;
          }
          .upload-title {
            font-size: 24px;
            color: #333;
            margin-bottom: 12px;
            font-weight: 600;
          }
          .upload-desc {
            color: #666;
            font-size: 14px;
            line-height: 1.6;
            margin-bottom: 24px;
          }
          .upload-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 14px 40px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
          }
          .features {
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-top: 40px;
            color: white;
          }
          .feature { text-align: center; }
          .feature-icon { font-size: 28px; margin-bottom: 8px; }
          .feature-text { font-size: 14px; opacity: 0.9; }
        </style>
      </head>
      <body>
        <div class="header">
          <div class="logo">报销助手</div>
          <div class="nav">
            <a href="#">首页</a>
            <a href="#">设置</a>
            <a href="#">帮助</a>
          </div>
        </div>
        <div class="main">
          <div class="hero">
            <h1>AI 智能发票识别</h1>
            <p>扔进去 → 等一下 → 拿结果，报销从此告别繁琐</p>
          </div>
          <div class="upload-zone">
            <div class="upload-icon">📄</div>
            <div class="upload-title">拖拽发票文件到这里</div>
            <div class="upload-desc">支持 JPG、PNG、PDF 格式<br>自动识别、分类、生成报销报表</div>
            <button class="upload-btn">选择文件夹</button>
          </div>
          <div class="features">
            <div class="feature">
              <div class="feature-icon">🔍</div>
              <div class="feature-text">智能识别</div>
            </div>
            <div class="feature">
              <div class="feature-icon">📂</div>
              <div class="feature-text">自动分类</div>
            </div>
            <div class="feature">
              <div class="feature-icon">🔗</div>
              <div class="feature-text">智能配对</div>
            </div>
            <div class="feature">
              <div class="feature-icon">📊</div>
              <div class="feature-text">生成报表</div>
            </div>
          </div>
        </div>
      </body>
      </html>
    `);
    await captureScreenshot(page, 'home', { wait: 500 });

    // 2. 桌面版主界面 (desktop_home.png)
    console.log('📷 正在创建桌面版主界面...');
    await captureScreenshot(page, 'desktop_home', { wait: 500 });

    // 3. 设置页面 (desktop_settings.png / api_config.png)
    console.log('📷 正在创建设置页面...');
    await page.setContent(`
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <style>
          * { margin: 0; padding: 0; box-sizing: border-box; }
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            min-height: 100vh;
            padding: 40px;
          }
          .container {
            max-width: 700px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            overflow: hidden;
          }
          .header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
          }
          .header h1 { font-size: 24px; margin-bottom: 8px; }
          .header p { opacity: 0.9; font-size: 14px; }
          .content { padding: 30px; }
          .section { margin-bottom: 30px; }
          .section-title {
            font-size: 16px;
            font-weight: 600;
            color: #333;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
          }
          .form-group { margin-bottom: 20px; }
          .form-label {
            display: block;
            font-size: 14px;
            color: #555;
            margin-bottom: 8px;
            font-weight: 500;
          }
          .form-input {
            width: 100%;
            padding: 12px 16px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            font-family: monospace;
          }
          .form-hint {
            font-size: 12px;
            color: #888;
            margin-top: 6px;
          }
          .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
          }
          .info-box {
            background: #f0f7ff;
            border-left: 4px solid #667eea;
            padding: 16px;
            border-radius: 0 8px 8px 0;
            margin-bottom: 20px;
          }
          .info-box h4 {
            color: #667eea;
            font-size: 14px;
            margin-bottom: 8px;
          }
          .info-box p {
            color: #666;
            font-size: 13px;
            line-height: 1.6;
          }
          .step {
            display: flex;
            gap: 12px;
            margin-bottom: 12px;
            font-size: 13px;
            color: #555;
          }
          .step-num {
            width: 20px;
            height: 20px;
            background: #667eea;
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            font-weight: 600;
            flex-shrink: 0;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>⚙️ 设置</h1>
            <p>配置 API 密钥和其他选项</p>
          </div>
          <div class="content">
            <div class="section">
              <div class="section-title">🔑 API 配置</div>
              <div class="info-box">
                <h4>如何获取 API Key</h4>
                <div class="step"><span class="step-num">1</span>访问硅基流动官网注册账号</div>
                <div class="step"><span class="step-num">2</span>进入控制台创建 API 密钥</div>
                <div class="step"><span class="step-num">3</span>复制密钥并粘贴到下方</div>
              </div>
              <div class="form-group">
                <label class="form-label">SiliconFlow API Key</label>
                <input type="text" class="form-input" value="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" readonly>
                <div class="form-hint">您的 API Key 将安全地存储在本地</div>
              </div>
              <button class="btn">保存配置</button>
            </div>
          </div>
        </div>
      </body>
      </html>
    `);
    await captureScreenshot(page, 'desktop_settings', { wait: 500 });
    await captureScreenshot(page, 'api_config', { wait: 500 });

    // 4. 处理中界面 (desktop_processing.png)
    console.log('📷 正在创建处理中界面...');
    await page.setContent(`
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <style>
          * { margin: 0; padding: 0; box-sizing: border-box; }
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
          }
          .header {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
          }
          .logo { font-size: 24px; font-weight: 700; color: white; }
          .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 40px;
          }
          .processing-card {
            background: rgba(255,255,255,0.95);
            border-radius: 20px;
            padding: 50px 60px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 500px;
            width: 100%;
          }
          .spinner {
            width: 60px;
            height: 60px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            margin: 0 auto 24px;
            animation: spin 1s linear infinite;
          }
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
          .status-title {
            font-size: 22px;
            color: #333;
            margin-bottom: 12px;
            font-weight: 600;
          }
          .status-desc {
            color: #666;
            font-size: 14px;
            margin-bottom: 30px;
          }
          .progress-bar {
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 20px;
          }
          .progress-fill {
            height: 100%;
            width: 65%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 4px;
            transition: width 0.3s;
          }
          .file-list {
            text-align: left;
            margin-top: 20px;
          }
          .file-item {
            display: flex;
            align-items: center;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 8px;
            margin-bottom: 8px;
            font-size: 13px;
          }
          .file-icon { margin-right: 10px; }
          .file-name { flex: 1; color: #333; }
          .file-status { color: #4caf50; font-weight: 500; }
        </style>
      </head>
      <body>
        <div class="header">
          <div class="logo">报销助手</div>
        </div>
        <div class="main">
          <div class="processing-card">
            <div class="spinner"></div>
            <div class="status-title">正在处理发票...</div>
            <div class="status-desc">AI 正在识别和分类您的发票，请稍候</div>
            <div class="progress-bar">
              <div class="progress-fill"></div>
            </div>
            <div class="file-list">
              <div class="file-item">
                <span class="file-icon">✅</span>
                <span class="file-name">滴滴发票_20240115.pdf</span>
                <span class="file-status">已识别</span>
              </div>
              <div class="file-item">
                <span class="file-icon">✅</span>
                <span class="file-name">高铁票_12306.pdf</span>
                <span class="file-status">已识别</span>
              </div>
              <div class="file-item">
                <span class="file-icon">⏳</span>
                <span class="file-name">酒店发票_如家.pdf</span>
                <span class="file-status">处理中...</span>
              </div>
            </div>
          </div>
        </div>
      </body>
      </html>
    `);
    await captureScreenshot(page, 'desktop_processing', { wait: 500 });

    // 5. Web 上传页面 (web_upload.png)
    console.log('📷 正在创建 Web 上传页面...');
    await page.setContent(`
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <style>
          * { margin: 0; padding: 0; box-sizing: border-box; }
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 40px;
          }
          .container {
            background: rgba(255,255,255,0.95);
            border-radius: 24px;
            padding: 50px;
            box-shadow: 0 25px 80px rgba(0,0,0,0.4);
            max-width: 600px;
            width: 100%;
            text-align: center;
          }
          .logo-area { margin-bottom: 30px; }
          .logo-icon {
            width: 70px;
            height: 70px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 16px;
            font-size: 36px;
          }
          .logo-text {
            font-size: 28px;
            font-weight: 700;
            color: #333;
          }
          .tagline {
            color: #666;
            font-size: 15px;
            margin-bottom: 40px;
          }
          .upload-area {
            border: 2px dashed #ccc;
            border-radius: 16px;
            padding: 50px 30px;
            background: #fafafa;
            transition: all 0.3s;
            margin-bottom: 30px;
          }
          .upload-icon-large { font-size: 48px; margin-bottom: 16px; }
          .upload-title { font-size: 18px; color: #333; margin-bottom: 8px; }
          .upload-desc { font-size: 13px; color: #888; }
          .features {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            text-align: left;
          }
          .feature-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px;
            background: #f5f7fa;
            border-radius: 10px;
          }
          .feature-icon { font-size: 20px; }
          .feature-text { font-size: 13px; color: #555; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="logo-area">
            <div class="logo-icon">📄</div>
            <div class="logo-text">报销助手 Web 版</div>
          </div>
          <div class="tagline">AI 智能识别发票，一键生成报销报表</div>
          <div class="upload-area">
            <div class="upload-icon-large">📁</div>
            <div class="upload-title">点击或拖拽文件到这里上传</div>
            <div class="upload-desc">支持 JPG、PNG、PDF 格式，最多 50MB</div>
          </div>
          <div class="features">
            <div class="feature-item">
              <span class="feature-icon">🔍</span>
              <span class="feature-text">智能识别发票信息</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">📂</span>
              <span class="feature-text">自动分类整理</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">🔗</span>
              <span class="feature-text">行程发票智能配对</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">📊</span>
              <span class="feature-text">导出 Excel 报表</span>
            </div>
          </div>
        </div>
      </body>
      </html>
    `);
    await captureScreenshot(page, 'web_upload', { wait: 500 });

    // 6. 输出结果示意 (output_result.png)
    console.log('📷 正在创建输出结果示意...');
    await page.setContent(`
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
          }
          .container {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 600px;
            width: 100%;
          }
          h3 {
            margin: 0 0 20px 0;
            color: #333;
            font-size: 18px;
          }
          .tree {
            font-size: 14px;
            line-height: 1.8;
            color: #555;
          }
          .folder { color: #e67e22; font-weight: 600; }
          .file { color: #3498db; }
          .excel { color: #27ae60; font-weight: 600; }
          .indent { margin-left: 20px; }
          .indent2 { margin-left: 40px; }
        </style>
      </head>
      <body>
        <div class="container">
          <h3>📁 报销结果_20240114/</h3>
          <div class="tree">
            <div class="folder">📂 打车票/</div>
            <div class="indent">
              <div class="folder">📂 2024-01-15_滴滴出行_35.00元/</div>
              <div class="indent2 file">📄 01_凭证_滴滴出行_35.00元.jpg</div>
              <div class="indent2 file">📄 02_发票_滴滴出行_35.00元.pdf</div>
            </div>
            <div class="folder">📂 火车飞机票/</div>
            <div class="folder">📂 住宿费/</div>
            <div class="folder">📂 餐费/</div>
            <div class="folder">📂 其他/</div>
            <div class="excel">📊 报销统计_20240114.xlsx</div>
          </div>
        </div>
      </body>
      </html>
    `);
    await captureScreenshot(page, 'output_result', { wait: 500 });

    // 7. 分类结果示意 (categories.png)
    console.log('📷 正在创建分类结果示意...');
    await page.setContent(`
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
          }
          .container {
            background: white;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            max-width: 700px;
            width: 100%;
          }
          h3 {
            margin: 0 0 25px 0;
            color: #2c3e50;
            font-size: 20px;
            text-align: center;
          }
          .category {
            display: flex;
            align-items: center;
            padding: 15px 20px;
            margin: 10px 0;
            border-radius: 10px;
            transition: transform 0.2s;
          }
          .category:hover { transform: translateX(5px); }
          .icon {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            margin-right: 15px;
          }
          .cat1 { background: #fff3e0; }
          .cat2 { background: #e3f2fd; }
          .cat3 { background: #f3e5f5; }
          .cat4 { background: #e8f5e9; }
          .cat5 { background: #eceff1; }
          .info { flex: 1; }
          .name {
            font-weight: 600;
            color: #2c3e50;
            font-size: 15px;
          }
          .desc {
            color: #7f8c8d;
            font-size: 13px;
            margin-top: 2px;
          }
          .count {
            background: #3498db;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <h3>📂 发票自动分类结果</h3>
          <div class="category">
            <div class="icon cat1">🚕</div>
            <div class="info">
              <div class="name">打车票</div>
              <div class="desc">滴滴、高德、美团打车、曹操、出租车</div>
            </div>
            <div class="count">12 张</div>
          </div>
          <div class="category">
            <div class="icon cat2">🚄</div>
            <div class="info">
              <div class="name">火车飞机票</div>
              <div class="desc">12306、各航空公司、携程、飞猪</div>
            </div>
            <div class="count">4 张</div>
          </div>
          <div class="category">
            <div class="icon cat3">🏨</div>
            <div class="info">
              <div class="name">住宿费</div>
              <div class="desc">如家、汉庭、亚朵、酒店、宾馆</div>
            </div>
            <div class="count">3 张</div>
          </div>
          <div class="category">
            <div class="icon cat4">🍜</div>
            <div class="info">
              <div class="name">餐费</div>
              <div class="desc">餐厅、外卖、美团、饿了么</div>
            </div>
            <div class="count">8 张</div>
          </div>
          <div class="category">
            <div class="icon cat5">📦</div>
            <div class="info">
              <div class="name">其他</div>
              <div class="desc">未能自动分类的发票</div>
            </div>
            <div class="count">2 张</div>
          </div>
        </div>
      </body>
      </html>
    `);
    await captureScreenshot(page, 'categories', { wait: 500 });

    // 8. 智能配对示意 (pairing.png)
    console.log('📷 正在创建智能配对示意...');
    await page.setContent(`
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
          }
          .container {
            background: white;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 650px;
            width: 100%;
          }
          h3 {
            margin: 0 0 25px 0;
            color: #2c3e50;
            font-size: 20px;
            text-align: center;
          }
          .pair {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            margin: 15px 0;
            border-left: 4px solid #4CAF50;
          }
          .pair-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
          }
          .badge {
            background: #4CAF50;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-right: 10px;
          }
          .platform {
            color: #666;
            font-size: 14px;
          }
          .files {
            display: flex;
            gap: 15px;
          }
          .file-card {
            flex: 1;
            background: white;
            border-radius: 8px;
            padding: 15px;
            border: 1px solid #e0e0e0;
          }
          .file-type {
            font-size: 12px;
            color: #999;
            margin-bottom: 5px;
          }
          .file-name {
            font-size: 14px;
            color: #333;
            font-weight: 500;
          }
          .file-meta {
            font-size: 12px;
            color: #666;
            margin-top: 8px;
          }
          .arrow {
            display: flex;
            align-items: center;
            color: #4CAF50;
            font-size: 20px;
          }
          .match-info {
            display: flex;
            gap: 15px;
            margin-top: 12px;
            font-size: 12px;
          }
          .match-tag {
            background: #e8f5e9;
            color: #2e7d32;
            padding: 4px 10px;
            border-radius: 4px;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <h3>🔗 智能配对结果</h3>

          <div class="pair">
            <div class="pair-header">
              <span class="badge">已配对</span>
              <span class="platform">🚕 滴滴出行</span>
            </div>
            <div class="files">
              <div class="file-card">
                <div class="file-type">行程凭证</div>
                <div class="file-name">滴滴行程单.pdf</div>
                <div class="file-meta">📅 2024-01-15 | 💰 ¥35.00</div>
              </div>
              <div class="arrow">→</div>
              <div class="file-card">
                <div class="file-type">发票</div>
                <div class="file-name">滴滴电子发票.pdf</div>
                <div class="file-meta">📅 2024-01-15 | 💰 ¥35.00</div>
              </div>
            </div>
            <div class="match-info">
              <span class="match-tag">✓ 日期匹配</span>
              <span class="match-tag">✓ 金额匹配</span>
              <span class="match-tag">✓ 平台匹配</span>
            </div>
          </div>

          <div class="pair">
            <div class="pair-header">
              <span class="badge">已配对</span>
              <span class="platform">🚕 高德打车</span>
            </div>
            <div class="files">
              <div class="file-card">
                <div class="file-type">行程凭证</div>
                <div class="file-name">高德行程单.jpg</div>
                <div class="file-meta">📅 2024-01-16 | 💰 ¥28.50</div>
              </div>
              <div class="arrow">→</div>
              <div class="file-card">
                <div class="file-type">发票</div>
                <div class="file-name">高德发票.pdf</div>
                <div class="file-meta">📅 2024-01-16 | 💰 ¥28.50</div>
              </div>
            </div>
            <div class="match-info">
              <span class="match-tag">✓ 日期匹配</span>
              <span class="match-tag">✓ 金额匹配</span>
              <span class="match-tag">✓ 平台匹配</span>
            </div>
          </div>
        </div>
      </body>
      </html>
    `);
    await captureScreenshot(page, 'pairing', { wait: 500 });

    // 9. Excel 报表示意 (excel_report.png)
    console.log('📷 正在创建 Excel 报表示意...');
    await page.setContent(`
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f0f2f5;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
          }
          .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            overflow: hidden;
            max-width: 800px;
            width: 100%;
          }
          .header {
            background: linear-gradient(90deg, #217346 0%, #1e6b40 100%);
            color: white;
            padding: 15px 20px;
            display: flex;
            align-items: center;
            gap: 10px;
          }
          .excel-icon {
            font-size: 24px;
          }
          .title {
            font-size: 16px;
            font-weight: 600;
          }
          .content {
            padding: 0;
          }
          table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
          }
          th {
            background: #f8f9fa;
            padding: 12px 15px;
            text-align: left;
            font-weight: 600;
            color: #555;
            border-bottom: 2px solid #e0e0e0;
          }
          td {
            padding: 12px 15px;
            border-bottom: 1px solid #f0f0f0;
            color: #333;
          }
          tr:hover { background: #f8f9fa; }
          .category-tag {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
          }
          .tag-taxi { background: #fff3e0; color: #e65100; }
          .tag-transport { background: #e3f2fd; color: #1565c0; }
          .tag-hotel { background: #f3e5f5; color: #7b1fa2; }
          .tag-meal { background: #e8f5e9; color: #2e7d32; }
          .amount {
            font-weight: 600;
            color: #2e7d32;
          }
          .summary {
            background: #f8f9fa;
            padding: 15px 20px;
            border-top: 2px solid #e0e0e0;
            display: flex;
            justify-content: space-between;
            align-items: center;
          }
          .summary-label {
            color: #666;
            font-size: 14px;
          }
          .summary-value {
            font-size: 20px;
            font-weight: 700;
            color: #217346;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <span class="excel-icon">📊</span>
            <span class="title">报销统计表 - 2024年1月</span>
          </div>
          <div class="content">
            <table>
              <thead>
                <tr>
                  <th>类别</th>
                  <th>日期</th>
                  <th>商家/平台</th>
                  <th>发票号</th>
                  <th>金额</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><span class="category-tag tag-taxi">🚕 打车票</span></td>
                  <td>2024-01-15</td>
                  <td>滴滴出行</td>
                  <td>24011512345678</td>
                  <td class="amount">¥35.00</td>
                </tr>
                <tr>
                  <td><span class="category-tag tag-transport">🚄 火车票</span></td>
                  <td>2024-01-15</td>
                  <td>12306</td>
                  <td>E24011587654321</td>
                  <td class="amount">¥553.50</td>
                </tr>
                <tr>
                  <td><span class="category-tag tag-hotel">🏨 住宿费</span></td>
                  <td>2024-01-15</td>
                  <td>如家酒店</td>
                  <td>24011511111111</td>
                  <td class="amount">¥398.00</td>
                </tr>
                <tr>
                  <td><span class="category-tag tag-meal">🍜 餐费</span></td>
                  <td>2024-01-15</td>
                  <td>美团外卖</td>
                  <td>24011522222222</td>
                  <td class="amount">¥45.80</td>
                </tr>
                <tr>
                  <td><span class="category-tag tag-taxi">🚕 打车票</span></td>
                  <td>2024-01-16</td>
                  <td>高德打车</td>
                  <td>24011633333333</td>
                  <td class="amount">¥28.50</td>
                </tr>
              </tbody>
            </table>
            <div class="summary">
              <span class="summary-label">合计金额</span>
              <span class="summary-value">¥1,060.80</span>
            </div>
          </div>
        </div>
      </body>
      </html>
    `);
    await captureScreenshot(page, 'excel_report', { wait: 500 });

    // 10. 多平台展示 (platforms.png)
    console.log('📷 正在创建多平台展示...');
    await page.setContent(`
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
          }
          .container {
            text-align: center;
          }
          h3 {
            color: white;
            margin: 0 0 30px 0;
            font-size: 24px;
          }
          .platforms {
            display: flex;
            gap: 30px;
            justify-content: center;
            flex-wrap: wrap;
          }
          .platform-card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            width: 200px;
            border: 1px solid rgba(255,255,255,0.2);
            transition: transform 0.3s;
          }
          .platform-card:hover {
            transform: translateY(-10px);
          }
          .platform-icon {
            font-size: 48px;
            margin-bottom: 15px;
          }
          .platform-name {
            color: white;
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
          }
          .platform-desc {
            color: rgba(255,255,255,0.7);
            font-size: 14px;
            margin-bottom: 15px;
          }
          .platform-tags {
            display: flex;
            gap: 8px;
            justify-content: center;
            flex-wrap: wrap;
          }
          .tag {
            background: rgba(255,255,255,0.2);
            color: white;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11px;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <h3>💻 多平台支持</h3>
          <div class="platforms">
            <div class="platform-card">
              <div class="platform-icon">🖥️</div>
              <div class="platform-name">桌面应用</div>
              <div class="platform-desc">原生体验，功能最全</div>
              <div class="platform-tags">
                <span class="tag">macOS</span>
                <span class="tag">Windows</span>
              </div>
            </div>
            <div class="platform-card">
              <div class="platform-icon">🌐</div>
              <div class="platform-name">网页版</div>
              <div class="platform-desc">无需安装，即开即用</div>
              <div class="platform-tags">
                <span class="tag">跨平台</span>
                <span class="tag">浏览器</span>
              </div>
            </div>
            <div class="platform-card">
              <div class="platform-icon">⌨️</div>
              <div class="platform-name">命令行</div>
              <div class="platform-desc">批量处理，自动化</div>
              <div class="platform-tags">
                <span class="tag">CLI</span>
                <span class="tag">脚本</span>
              </div>
            </div>
          </div>
        </div>
      </body>
      </html>
    `);
    await captureScreenshot(page, 'platforms', { wait: 500 });

    // 11. 识别过程示意 (recognition.png)
    console.log('📷 正在创建识别过程示意...');
    await page.setContent(`
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f1419;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
          }
          .container {
            background: #1a2332;
            border-radius: 16px;
            padding: 30px;
            max-width: 700px;
            width: 100%;
          }
          h3 {
            color: white;
            margin: 0 0 25px 0;
            font-size: 18px;
          }
          .flow {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 30px 0;
          }
          .step {
            text-align: center;
            flex: 1;
          }
          .step-icon {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            margin: 0 auto 12px;
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.4);
          }
          .step-name {
            color: white;
            font-size: 14px;
            font-weight: 600;
          }
          .step-desc {
            color: #8b949e;
            font-size: 12px;
            margin-top: 4px;
          }
          .arrow {
            color: #58a6ff;
            font-size: 24px;
            padding: 0 10px;
          }
          .ocr-demo {
            background: #0f1419;
            border-radius: 12px;
            padding: 20px;
            margin-top: 25px;
            border: 1px solid #30363d;
          }
          .ocr-title {
            color: #8b949e;
            font-size: 12px;
            margin-bottom: 15px;
            text-transform: uppercase;
          }
          .ocr-content {
            display: flex;
            gap: 20px;
          }
          .invoice-preview {
            width: 150px;
            height: 200px;
            background: linear-gradient(180deg, #fff 0%, #f0f0f0 100%);
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            padding: 15px;
            font-size: 10px;
            color: #333;
          }
          .preview-line {
            height: 8px;
            background: #ddd;
            border-radius: 2px;
            margin: 4px 0;
          }
          .preview-line.short { width: 60%; }
          .preview-highlight {
            background: rgba(102, 126, 234, 0.3);
            border: 1px solid #667eea;
            border-radius: 2px;
            padding: 2px 4px;
            margin: 2px 0;
            font-size: 9px;
          }
          .extracted-data {
            flex: 1;
          }
          .data-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #21262d;
          }
          .data-label {
            color: #8b949e;
            font-size: 13px;
          }
          .data-value {
            color: #7ee787;
            font-size: 13px;
            font-family: monospace;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <h3>🔍 智能识别流程</h3>
          <div class="flow">
            <div class="step">
              <div class="step-icon">📄</div>
              <div class="step-name">上传文件</div>
              <div class="step-desc">PDF/图片</div>
            </div>
            <div class="arrow">→</div>
            <div class="step">
              <div class="step-icon">🔍</div>
              <div class="step-name">OCR 识别</div>
              <div class="step-desc">PaddleOCR</div>
            </div>
            <div class="arrow">→</div>
            <div class="step">
              <div class="step-icon">🤖</div>
              <div class="step-name">AI 分析</div>
              <div class="step-desc">DeepSeek</div>
            </div>
            <div class="arrow">→</div>
            <div class="step">
              <div class="step-icon">📊</div>
              <div class="step-name">生成结果</div>
              <div class="step-desc">Excel 报表</div>
            </div>
          </div>
          <div class="ocr-demo">
            <div class="ocr-title">识别示例</div>
            <div class="ocr-content">
              <div class="invoice-preview">
                <div style="text-align:center;font-weight:bold;margin-bottom:10px;">发票</div>
                <div class="preview-line"></div>
                <div class="preview-line short"></div>
                <div class="preview-highlight">金额: ¥35.00</div>
                <div class="preview-highlight">日期: 2024-01-15</div>
                <div class="preview-highlight">商家: 滴滴出行</div>
                <div class="preview-line"></div>
                <div class="preview-line short"></div>
              </div>
              <div class="extracted-data">
                <div class="data-row">
                  <span class="data-label">发票类型</span>
                  <span class="data-value">打车票</span>
                </div>
                <div class="data-row">
                  <span class="data-label">商家名称</span>
                  <span class="data-value">滴滴出行</span>
                </div>
                <div class="data-row">
                  <span class="data-label">发票金额</span>
                  <span class="data-value">¥35.00</span>
                </div>
                <div class="data-row">
                  <span class="data-label">发票日期</span>
                  <span class="data-value">2024-01-15</span>
                </div>
                <div class="data-row">
                  <span class="data-label">发票号码</span>
                  <span class="data-value">24011512345678</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </body>
      </html>
    `);
    await captureScreenshot(page, 'recognition', { wait: 500 });

    // 12. Web 结果页面 (web_result.png)
    console.log('📷 正在创建 Web 结果页面...');
    await page.setContent(`
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
          }
          .container {
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            max-width: 800px;
            width: 100%;
            overflow: hidden;
          }
          .header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px 30px;
          }
          .header h2 {
            margin: 0;
            font-size: 22px;
          }
          .header p {
            margin: 8px 0 0 0;
            opacity: 0.9;
            font-size: 14px;
          }
          .stats {
            display: flex;
            gap: 20px;
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e0e0e0;
          }
          .stat {
            flex: 1;
            text-align: center;
          }
          .stat-value {
            font-size: 28px;
            font-weight: 700;
            color: #667eea;
          }
          .stat-label {
            font-size: 13px;
            color: #666;
            margin-top: 4px;
          }
          .content {
            padding: 30px;
          }
          .section {
            margin-bottom: 25px;
          }
          .section-title {
            font-size: 16px;
            font-weight: 600;
            color: #333;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
          }
          .file-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
          }
          .file-item {
            display: flex;
            align-items: center;
            padding: 12px 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 3px solid #667eea;
          }
          .file-icon {
            font-size: 20px;
            margin-right: 12px;
          }
          .file-info {
            flex: 1;
          }
          .file-name {
            font-size: 14px;
            color: #333;
          }
          .file-meta {
            font-size: 12px;
            color: #666;
            margin-top: 2px;
          }
          .file-status {
            background: #4caf50;
            color: white;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
          }
          .actions {
            display: flex;
            gap: 12px;
            padding: 20px 30px;
            background: #f8f9fa;
            border-top: 1px solid #e0e0e0;
          }
          .btn {
            flex: 1;
            padding: 12px 20px;
            border-radius: 8px;
            border: none;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
          }
          .btn-primary {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
          }
          .btn-secondary {
            background: white;
            color: #667eea;
            border: 1px solid #667eea;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h2>✅ 处理完成</h2>
            <p>所有发票已识别、分类并整理完毕</p>
          </div>
          <div class="stats">
            <div class="stat">
              <div class="stat-value">29</div>
              <div class="stat-label">已处理文件</div>
            </div>
            <div class="stat">
              <div class="stat-value">5</div>
              <div class="stat-label">分类类别</div>
            </div>
            <div class="stat">
              <div class="stat-value">8</div>
              <div class="stat-label">智能配对</div>
            </div>
            <div class="stat">
              <div class="stat-value">¥3,240</div>
              <div class="stat-label">总金额</div>
            </div>
          </div>
          <div class="content">
            <div class="section">
              <div class="section-title">📂 分类结果</div>
              <div class="file-list">
                <div class="file-item">
                  <span class="file-icon">🚕</span>
                  <div class="file-info">
                    <div class="file-name">打车票</div>
                    <div class="file-meta">12 张发票 · ¥420.00</div>
                  </div>
                  <span class="file-status">已配对 6 组</span>
                </div>
                <div class="file-item">
                  <span class="file-icon">🚄</span>
                  <div class="file-info">
                    <div class="file-name">火车飞机票</div>
                    <div class="file-meta">4 张发票 · ¥2,214.00</div>
                  </div>
                  <span class="file-status">已完成</span>
                </div>
                <div class="file-item">
                  <span class="file-icon">🏨</span>
                  <div class="file-info">
                    <div class="file-name">住宿费</div>
                    <div class="file-meta">3 张发票 · ¥1,194.00</div>
                  </div>
                  <span class="file-status">已完成</span>
                </div>
                <div class="file-item">
                  <span class="file-icon">🍜</span>
                  <div class="file-info">
                    <div class="file-name">餐费</div>
                    <div class="file-meta">8 张发票 · ¥412.00</div>
                  </div>
                  <span class="file-status">已完成</span>
                </div>
              </div>
            </div>
          </div>
          <div class="actions">
            <button class="btn btn-primary">📥 下载 ZIP 文件</button>
            <button class="btn btn-primary">📊 下载 Excel 报表</button>
            <button class="btn btn-secondary">🔄 继续处理</button>
          </div>
        </div>
      </body>
      </html>
    `);
    await captureScreenshot(page, 'web_result', { wait: 500 });

    console.log('\n✨ 所有截图已生成完毕！');
    console.log(`📁 截图保存在: ${assetsDir}`);
    console.log('\n📋 生成的文件列表:');
    const fs = await import('fs');
    const files = fs.readdirSync(assetsDir).filter(f => f.endsWith('.png'));
    files.forEach(f => console.log(`   - ${f}`));

  } catch (error) {
    console.error('❌ 截图过程出错:', error);
  } finally {
    await browser.close();
  }
}

// 主函数
captureScreenshots().catch(console.error);
