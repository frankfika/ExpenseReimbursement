const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const net = require('net');

let mainWindow;
let pythonProcess = null;
let isQuitting = false;
let backendPort = 5000;

// 检查端口是否可用
function isPortAvailable(port) {
    return new Promise((resolve) => {
        const server = net.createServer();
        server.listen(port, () => {
            server.once('close', () => resolve(true));
            server.close();
        });
        server.on('error', () => resolve(false));
    });
}

// 查找可用端口
async function findAvailablePort(startPort) {
    for (let port = startPort; port < startPort + 100; port++) {
        if (await isPortAvailable(port)) {
            return port;
        }
    }
    return startPort;
}

// 获取 Python 路径
function getPythonPath() {
    if (app.isPackaged) {
        if (process.platform === 'win32') {
            return path.join(process.resourcesPath, 'python', 'python.exe');
        } else {
            return path.join(process.resourcesPath, 'python', 'bin', 'python3');
        }
    } else {
        return 'python3';
    }
}

// 启动 Flask 后端
async function startPythonBackend() {
    const pythonPath = getPythonPath();
    const backendPath = app.isPackaged
        ? path.join(process.resourcesPath, 'backend', 'web_app.py')
        : path.join(__dirname, '..', 'web_app.py');

    // 查找可用端口
    backendPort = await findAvailablePort(5000);
    console.log('Using port:', backendPort);

    console.log('Starting Python backend:', pythonPath, backendPath);

    pythonProcess = spawn(pythonPath, [backendPath], {
        cwd: app.isPackaged ? path.join(process.resourcesPath, 'backend') : path.join(__dirname, '..'),
        env: { ...process.env, PYTHONUNBUFFERED: '1', PORT: backendPort.toString() }
    });

    pythonProcess.stdout.on('data', (data) => {
        console.log('Python:', data.toString());
    });

    pythonProcess.stderr.on('data', (data) => {
        const msg = data.toString();
        // 只打印重要的错误，过滤掉 urllib3 警告
        if (!msg.includes('NotOpenSSLWarning') && !msg.includes('development server')) {
            console.error('Python Error:', msg);
        }
    });

    pythonProcess.on('close', (code) => {
        if (!isQuitting) {
            console.log('Python backend exited unexpectedly with code:', code);
        }
    });
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 800,
        minHeight: 600,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        title: '报销助手',
        backgroundColor: '#ffffff'
    });

    // 加载 Flask 应用
    mainWindow.loadURL(`http://127.0.0.1:${backendPort}`);

    // 开发模式下可以打开 DevTools
    // if (!app.isPackaged) {
    //     mainWindow.webContents.openDevTools();
    // }

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

app.whenReady().then(async () => {
    // 先启动 Python 后端
    await startPythonBackend();

    // 等待后端启动后再创建窗口
    setTimeout(() => {
        createWindow();
    }, 2000);

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    // macOS 上，关闭窗口不退出应用
    if (process.platform !== 'darwin') {
        cleanupAndQuit();
    }
});

app.on('before-quit', (e) => {
    // 防止递归调用
    if (isQuitting) {
        return;
    }
    isQuitting = true;
    cleanupAndQuit();
});

function cleanupAndQuit() {
    if (pythonProcess) {
        try {
            pythonProcess.kill();
            console.log('Python backend terminated');
        } catch (err) {
            // 忽略错误
        }
        pythonProcess = null;
    }
    // 不在这里调用 app.quit()，让进程自然退出
}

// IPC 处理
ipcMain.handle('get-app-version', () => {
    return app.getVersion();
});
