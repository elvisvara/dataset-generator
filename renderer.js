// renderer.js
const { ipcRenderer } = require('electron');

// Folder selection: assumes an element with id "chooseBtn" and "outputPath"
document.getElementById('chooseBtn').addEventListener('click', () => {
  ipcRenderer.send('choose-directory');
});

ipcRenderer.on('directory-selected', (event, folderPath) => {
  document.getElementById('outputPath').value = folderPath;
});

// Preset mode generation
document.getElementById('generateBtn').addEventListener('click', () => {
  const outputDir = document.getElementById('outputPath').value;
  if (!outputDir) {
    alert("Please select an output directory.");
    return;
  }
  const scenario = document.getElementById('presetSelect').value;
  let faults = [];
  if (scenario === "custom") {
    if (document.getElementById('chk_null').checked) faults.push('null_byte');
    if (document.getElementById('chk_missing').checked) faults.push('missing_file');
    if (document.getElementById('chk_unsupported').checked) faults.push('unsupported_sop');
    if (document.getElementById('chk_modality').checked) faults.push('incorrect_modality');
    if (document.getElementById('chk_corrupt').checked) faults.push('corrupt_pixel');
    if (document.getElementById('chk_unexpected').checked) faults.push('unexpected_values');
    if (document.getElementById('chk_external').checked) faults.push('external_prior');
    if (document.getElementById('chk_sanity').checked) faults.push('sanity_failure');
    if (document.getElementById('chk_studyuid').checked) faults.push('study_uid_mismatch');
    if (document.getElementById('chk_modality_ot').checked) faults.push('modality_ot_instead_mg');
    if (document.getElementById('chk_rawdata').checked) faults.push('rawdata_storage_sop');
    if (document.getElementById('chk_presentation').checked) faults.push('incorrect_presentation_lut');
    if (document.getElementById('chk_prior_missing').checked) faults.push('prior_missing_in_pacs');
    if (document.getElementById('chk_studyuid2').checked) faults.push('study_uid_mismatch_2');
    if (document.getElementById('chk_modality_ot2').checked) faults.push('modality_ot_instead_mg_2');
    if (document.getElementById('chk_rawdata2').checked) faults.push('rawdata_storage_sop');
    if (document.getElementById('chk_presentation2').checked) faults.push('incorrect_presentation_lut');
    if (document.getElementById('chk_prior_missing2').checked) faults.push('prior_missing_in_pacs_2');
  }
  const preview = document.getElementById('previewToggle').checked;
  const templateType = "synthetic"; // or "cancerous" / "non-cancerous" based on your UI selection
  ipcRenderer.send('start-generation', { outputDir, scenario, faults, preview, templateType });
});

// Power Customize mode: open the wizard window
document.getElementById('powerCustomizeBtn').addEventListener('click', () => {
  ipcRenderer.send('open-power-customize');
});

// Log updates and progress
ipcRenderer.on('log-update', (event, message) => {
  const logPanel = document.getElementById('logPanel');
  logPanel.textContent += message;
  logPanel.scrollTop = logPanel.scrollHeight;
  const progMatch = message.match(/PROGRESS: (\d+)/);
  if (progMatch) {
    const percent = Number(progMatch[1]);
    document.getElementById('progressBar').value = percent;
    document.getElementById('progressDisplay').textContent = percent + "%";
  }
});

ipcRenderer.on('generation-complete', () => {
  document.getElementById('progressBar').value = 100;
  document.getElementById('progressDisplay').textContent = "100%";
  const logPanel = document.getElementById('logPanel');
  logPanel.textContent += "\nGeneration complete.\n";
});

// Save logs
document.getElementById('saveLogBtn').addEventListener('click', () => {
  ipcRenderer.send('save-logs', document.getElementById('logPanel').textContent);
});
