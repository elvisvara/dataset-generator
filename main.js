// /Users/elvis/Desktop/SUH/main.js
const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const { spawn, execFileSync } = require('child_process');
const path = require('path');
const fs = require('fs');

let mainWindow;
let powerWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });
  mainWindow.loadFile('index.html');
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (mainWindow === null) createWindow();
});


ipcMain.on('choose-directory', async (event) => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory']
  });
  if (!result.canceled && result.filePaths.length > 0) {
    event.reply('directory-selected', result.filePaths[0]);
  }
});


ipcMain.on('get-scenarios', (event) => {
  const scriptPath = path.join(__dirname, 'generate_dicom_dataset.py');
  console.log("[DEBUG] Listing scenarios from script at:", scriptPath);
  // call python with --list-scenarios
  const pyProcess = spawn('python3', [scriptPath, '--output', '.', '--list-scenarios'], { cwd: __dirname });

  let outputData = "";
  pyProcess.stdout.on('data', (data) => {
    outputData += data.toString();
  });
  pyProcess.stderr.on('data', (err) => {
    mainWindow.webContents.send('log-update', `ERROR listing scenarios: ${err}`);
  });
  pyProcess.on('exit', () => {
    const lines = outputData.split(/\r?\n/).filter((x) => x.trim() !== "");
    event.reply('scenarios-list', lines);
  });
});

//  PRESET MODE GENERATION 
ipcMain.on('start-generation', (event, args) => {
  const { outputDir, scenario, faults, preview, templateType } = args;
  if (!outputDir) {
    mainWindow.webContents.send('log-update', "ERROR: No output directory selected.\n");
    return;
  }

  const scriptPath = path.join(__dirname, 'generate_dicom_dataset.py');
  // python script --output <dir> --scenario <scenario>
  const cmdArgs = ['--output', path.resolve(outputDir), '--scenario', scenario];

  // might wanna pass faults in the future.. right now, didn't code that in the script, so they might get ignored, but let's just do it for reference:
  if (faults && faults.length > 0) {
    cmdArgs.push('--faults', ...faults);
  }

  if (preview) {
    cmdArgs.push('--preview');
  }


  console.log("[DEBUG] Starting preset generation with args:", cmdArgs.join(" "));
  mainWindow.webContents.send('log-update', `Spawning python3 with: ${cmdArgs.join(" ")}\n`);

  const pyProcess = spawn('python3', [scriptPath, ...cmdArgs], { cwd: __dirname });

  pyProcess.stdout.on('data', (data) => {
    mainWindow.webContents.send('log-update', data.toString());
  });
  pyProcess.stderr.on('data', (data) => {
    mainWindow.webContents.send('log-update', `ERROR: ${data.toString()}`);
  });
  pyProcess.on('exit', (code) => {
    mainWindow.webContents.send('log-update', `\nProcess exited with code ${code}\n`);
    mainWindow.webContents.send('generation-complete');
  });
});

// OPEN POWER CUSTOMIZE WINDOW 
ipcMain.on('open-power-customize-window', () => {
  powerWindow = new BrowserWindow({
    width: 1000,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });
  powerWindow.loadFile('power_customize.html');
  powerWindow.on('closed', () => {
    powerWindow = null;
  });
});

//  POWER CUSTOMIZE GENERATION 
ipcMain.on('start-power-customize', (event, configData) => {
  if (!configData.outputDir) {
    mainWindow.webContents.send('log-update', "ERROR: No output directory in power config.\n");
    return;
  }
  const tempConfigPath = path.join(app.getPath('userData'), 'power_customize_config.json');
  fs.writeFileSync(tempConfigPath, JSON.stringify(configData, null, 2));

  const scriptPath = path.join(__dirname, 'generate_dicom_dataset.py');
  const outDir = path.resolve(configData.outputDir);
  const targetWindow = powerWindow || mainWindow;

  targetWindow.webContents.send('log-update', `Starting power customize with outputDir=${outDir}\n`);
  try {
    const output = execFileSync('python3', [
      scriptPath,
      '--output',
      outDir,
      '--power-customize',
      tempConfigPath
    ], {
      cwd: __dirname,
      env: process.env
    });
    targetWindow.webContents.send('log-update', output.toString());
    targetWindow.webContents.send('log-update', `\nPower Customize process exited.\n`);
    targetWindow.webContents.send('generation-complete', { success: true });
  } catch (err) {
    targetWindow.webContents.send('log-update', `ERROR: ${err.message}\n`);
  }
});

//  SAVE LOGS 
ipcMain.on('save-logs', async (event, logs) => {
  const result = await dialog.showSaveDialog(mainWindow, {
    title: "Save Logs",
    defaultPath: "generation_log.txt",
    filters: [{ name: "Text Files", extensions: ["txt"] }]
  });
  if (!result.canceled && result.filePath) {
    fs.writeFileSync(result.filePath, logs);
  }
});
