// src/PowerCustomizeWizard.jsx

import React, { useState, useEffect } from 'react';
import { ipcRenderer } from 'electron';

// Example first/last name pools (no personal data)
const FIRST_NAMES = [
  "Alice","Bob","Carol","David","Eve","Frank","Grace","Hank","Irene","Jack","Karen","Larry",
  "Maria","Nate","Olivia","Peter","Quincy","Rachel","Sam","Tina","Uma","Victor","Wendy",
  "Xander","Yvonne","Zack","Allie","Ben","Cindy","Derek","Eliza","Fred","Gina","Harry",
  "Isla","Jon","Kara","Leo","Maggie"
];
const LAST_NAMES = [
  "Smith","Jones","Brown","Taylor","Wilson","Davis","Miller","Anderson","Thomas","Jackson",
  "White","Harris","Martin","Thompson","Garcia","Martinez","Robinson","Clark","Rodriguez",
  "Lewis","Lee","Walker","Hall","Allen","Young","Hernandez","King","Wright","Lopez","Hill",
  "Scott","Green","Adams","Baker","Gonzalez","Nelson","Carter","Mitchell","Perez"
];

// We track generated names to avoid collisions
const usedNames = new Set();

/**
 * Generate a guaranteed-unique name by picking a random first/last name plus random numeric suffix.
 * Example: "Alice123456 Brown"
 */
function generateUniqueName() {
  let name = "";
  do {
    const fn = FIRST_NAMES[Math.floor(Math.random() * FIRST_NAMES.length)];
    const ln = LAST_NAMES[Math.floor(Math.random() * LAST_NAMES.length)];
    const suffix = Math.floor(Math.random() * 1e6).toString().padStart(6, "0");
    name = `${fn}${suffix} ${ln}`;
  } while (usedNames.has(name));
  usedNames.add(name);
  return name;
}

/** Generate a random 8-digit date string YYYYMMDD in the range [1950..2023]. */
function randomDateYYYYMMDD() {
  const year = 1950 + Math.floor(Math.random() * 74);  // up to 2023
  const month = 1 + Math.floor(Math.random() * 12);
  const day = 1 + Math.floor(Math.random() * 28);
  return `${year}${String(month).padStart(2,"0")}${String(day).padStart(2,"0")}`;
}

/** Parse a date string YYYYMMDD into a JS Date object. */
function parseYYYYMMDD(str) {
  if (str.length !== 8) return new Date();
  const y = parseInt(str.slice(0,4), 10);
  const m = parseInt(str.slice(4,6), 10);
  const d = parseInt(str.slice(6,8), 10);
  return new Date(y, m - 1, d);
}

/** Convert a JS Date -> YYYYMMDD string. */
function formatYYYYMMDD(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}${m}${d}`;
}

/**
 * Return a random date strictly BEFORE the given currentStudyDateStr (in YYYYMMDD).
 * Subtracts a random # of days in [30..(365*5)] from the current date => up to 5 years prior.
 */
function randomPastStudyDate(currentStudyDateStr) {
  const cDate = parseYYYYMMDD(currentStudyDateStr);
  if (isNaN(cDate.getTime())) {
    return "19500101";
  }
  const offsetDays = 30 + Math.floor(Math.random() * (365 * 5)); // 30..1825
  cDate.setDate(cDate.getDate() - offsetDays);
  return formatYYYYMMDD(cDate);
}

/** Return a random UID: e.g. 1.2.826.0.1.3680043.8.498.1234567890 */
function randomUID() {
  return "1.2.826.0.1.3680043.8.498." + Math.floor(Math.random() * 1e10);
}

/**
 * The standard four MG views in mammography.
 */
const BASE_VIEWS = ["RCC", "LCC", "RMLO", "LMLO"];

/**
 * Build an array of view positions for `count` images:
 * - If count <= 4, just take that many from [RCC, LCC, RMLO, LMLO].
 * - If count > 4, produce [RCC, LCC, RMLO, LMLO] plus extras all "RCC".
 */
function pickViewsForCount(count) {
  if (count <= 4) {
    return BASE_VIEWS.slice(0, count);
  } else {
    const result = [...BASE_VIEWS];
    const extra = count - 4;
    for (let i = 0; i < extra; i++) {
      result.push("RCC");
    }
    return result;
  }
}

/**
 * Return the base DICOM tags for an image, with recommended fields.
 */
function getBaseImageTags(studyDescription, viewPosition, isCancerous) {
  return {
    Manufacturer: "SIEMENS",
    StudyDescription: (isCancerous ? "Cancerous " : "Non-cancerous ") + studyDescription,
    Modality: "MG",
    ViewPosition: viewPosition,
    ImageLaterality: viewPosition.startsWith("R") ? "R" : "L",
    SeriesDescription: `Mammo ${viewPosition}`,
    Rows: 256,
    Columns: 256,
    BitsAllocated: 8,
    BitsStored: 8,
    HighBit: 7,
    PixelRepresentation: 0,
    PhotometricInterpretation: "MONOCHROME2",
    BodyPartExamined: "BREAST",
    Laterality: "R",
    DetectorType: "DIRECT",
    SoftwareVersions: "1.0.0",
    PresentationLUTShape: "IDENTITY"
  };
}

/**
 * Generate the array of images (with tags) for a study,
 * based on the requested count & whether it's "cancerous".
 */
function generateDicomImages(count, studyDescription, isCancerous) {
  const viewPositions = pickViewsForCount(count);

  return viewPositions.map(view => ({
    tags: getBaseImageTags(studyDescription, view, isCancerous)
  }));
}

/**
 * We apply “protected fields” (PatientName, PatientID, etc.), 
 * plus generate SOPInstanceUID, SeriesInstanceUID, etc., if missing.
 */
function applyStudyProtectedFields(images, studyProtected) {
  const seriesUIDMap = {};
  const seriesNumberMap = {};
  let nextSeriesNumber = 1;

  return images.map((img, idx) => {
    const newTags = { ...img.tags };

    // Copy the protected fields if not already set
    Object.entries(studyProtected).forEach(([k, v]) => {
      if (newTags[k] == null) {
        newTags[k] = v;
      }
    });

    // Ensure we have a unique SOPInstanceUID
    if (!newTags.SOPInstanceUID) {
      newTags.SOPInstanceUID = randomUID();
    }
    // Also set an InstanceNumber
    newTags.InstanceNumber = idx + 1;

    // If SeriesInstanceUID is missing, generate one per distinct ViewPosition
    if (!newTags.SeriesInstanceUID) {
      const view = newTags.ViewPosition || "UNDEFINED";
      if (!seriesUIDMap[view]) {
        seriesUIDMap[view] = randomUID();
      }
      newTags.SeriesInstanceUID = seriesUIDMap[view];
    }

    // If SeriesNumber is missing, do a dynamic approach:
    //   The first time we see a new ViewPosition, we assign nextSeriesNumber.
    //   If we see that same ViewPosition again, we reuse that SeriesNumber.
    if (!newTags.SeriesNumber) {
      const view = newTags.ViewPosition || "UNDEFINED";
      if (!(view in seriesNumberMap)) {
        seriesNumberMap[view] = nextSeriesNumber;
        nextSeriesNumber++;
      }
      newTags.SeriesNumber = seriesNumberMap[view];
    }

    return { tags: newTags };
  });
}

export default function PowerCustomizeWizard() {
  const [step, setStep] = useState(1);
  const [logs, setLogs] = useState("");
  const [internalCount, setInternalCount] = useState(0);
  const [externalCount, setExternalCount] = useState(0);

  // The final config that we pass to Python
  const [config, setConfig] = useState({
    outputDir: "",
    current_study: {
      cancerous: false,
      count: 4,
      images: []
    },
    internal_priors: [],
    external_priors: []
  });

  useEffect(() => {
    const logListener = (event, message) => {
      setLogs(prev => prev + message);
      console.log("[IPC LOG]", message);
    };
    ipcRenderer.on('log-update', logListener);
    return () => {
      ipcRenderer.removeListener('log-update', logListener);
    };
  }, []);

  useEffect(() => {
    const dirListener = (event, folderPath) => {
      setConfig(prev => ({ ...prev, outputDir: folderPath }));
    };
    ipcRenderer.on('directory-selected', dirListener);
    return () => {
      ipcRenderer.removeListener('directory-selected', dirListener);
    };
  }, []);

  const nextStep = () => setStep(s => s + 1);
  const prevStep = () => setStep(s => s - 1);

  // -----------------------------
  // STEP 1: Current Study Setup
  // -----------------------------
  const handleCurrentChange = (field, value) => {
    setConfig(prev => ({
      ...prev,
      current_study: { ...prev.current_study, [field]: value }
    }));
  };

  // Generate images for current study + random unique name, etc.
  const initCurrentImages = () => {
    setConfig(prev => {
      const { cancerous, count } = prev.current_study;
      // 1) Create placeholder images
      let images = generateDicomImages(count, "Current Study", cancerous);

      // 2) Make a brand-new unique name
      const uniqueName = generateUniqueName();

      // 3) Pick a random date for the "current" study
      const studyDate = randomDateYYYYMMDD();
      // We'll guess the patient is ~50..75
      const sDateObj = parseYYYYMMDD(studyDate);
      const randAge = 50 + Math.floor(Math.random() * 26);
      const birthYear = sDateObj.getFullYear() - randAge;
      const bDateObj = new Date(birthYear, sDateObj.getMonth(), sDateObj.getDate());
      if (isNaN(bDateObj.getTime())) {
        bDateObj.setDate(15);
      }
      const birthDateStr = formatYYYYMMDD(bDateObj);

      const studyProtected = {
        PatientName: uniqueName,
        PatientID: String(Math.floor(100000 + Math.random() * 900000)),
        PatientBirthDate: birthDateStr,
        PatientSex: Math.random() < 0.5 ? "M" : "F",
        StudyInstanceUID: randomUID(),
        StudyID: String(Math.floor(100000 + Math.random() * 900000)),
        StudyDate: studyDate,
        StudyTime: "000000",
        AccessionNumber: String(Math.floor(100000 + Math.random() * 900000))
      };

      images = applyStudyProtectedFields(images, studyProtected);

      return {
        ...prev,
        current_study: {
          ...prev.current_study,
          images
        }
      };
    });
  };

  // For editing a single tag in current study
  const updateCurrentTag = (imgIdx, tagKey, val) => {
    setConfig(prev => {
      const newImgs = [...prev.current_study.images];
      newImgs[imgIdx] = {
        tags: { ...newImgs[imgIdx].tags, [tagKey]: val }
      };
      return {
        ...prev,
        current_study: {
          ...prev.current_study,
          images: newImgs
        }
      };
    });
  };

  // Delete a single tag from the current study image
  const removeCurrentTag = (imgIdx, tagKey) => {
    setConfig(prev => {
      const newImgs = [...prev.current_study.images];
      const newTags = { ...newImgs[imgIdx].tags };
      delete newTags[tagKey];
      newImgs[imgIdx] = { tags: newTags };
      return {
        ...prev,
        current_study: {
          ...prev.current_study,
          images: newImgs
        }
      };
    });
  };

  // -----------------------------
  // STEP 3: Internal Priors
  // -----------------------------
  const initInternalPriors = (newCount) => {
    setConfig(prev => {
      let arr = [...prev.internal_priors];

      const curImages = prev.current_study.images;
      if (curImages.length === 0) {
        return { ...prev, internal_priors: [] };
      }
      const firstCurrent = curImages[0].tags;

      const samePatientFields = {
        PatientName: firstCurrent.PatientName,
        PatientID: firstCurrent.PatientID,
        PatientBirthDate: firstCurrent.PatientBirthDate,
        PatientSex: firstCurrent.PatientSex
      };

      if (newCount < arr.length) {
        arr = arr.slice(0, newCount);
      } else {
        while (arr.length < newCount) {
          let images = generateDicomImages(4, "Internal Prior", false);

          const olderDate = randomPastStudyDate(firstCurrent.StudyDate);

          const priorStudyProtected = {
            ...samePatientFields,
            StudyInstanceUID: randomUID(),
            StudyDate: olderDate,
            StudyTime: "000000",
            AccessionNumber: String(Math.floor(100000 + Math.random() * 900000)),
            StudyID: String(Math.floor(100000 + Math.random() * 900000))
          };

          images = applyStudyProtectedFields(images, priorStudyProtected);

          arr.push({
            cancerous: false,
            count: 4,
            images
          });
        }
      }
      return { ...prev, internal_priors: arr };
    });
  };

  const updateInternalPrior = (pIdx, field, val) => {
    setConfig(prev => {
      const newList = [...prev.internal_priors];
      newList[pIdx] = { ...newList[pIdx], [field]: val };
      return { ...prev, internal_priors: newList };
    });
  };

  const regenerateInternalImages = (pIdx) => {
    setConfig(prev => {
      const newList = [...prev.internal_priors];
      const item = newList[pIdx];

      const curImages = prev.current_study.images;
      if (curImages.length === 0) return prev;

      const firstCurrent = curImages[0].tags;
      const samePatientFields = {
        PatientName: firstCurrent.PatientName,
        PatientID: firstCurrent.PatientID,
        PatientBirthDate: firstCurrent.PatientBirthDate,
        PatientSex: firstCurrent.PatientSex
      };

      let existingDate = "19700101";
      let existingUID = randomUID();
      if (item.images.length > 0) {
        const firstPrior = item.images[0].tags;
        existingDate = firstPrior.StudyDate || randomPastStudyDate(firstCurrent.StudyDate);
        existingUID = firstPrior.StudyInstanceUID || randomUID();
      }

      const newImages = generateDicomImages(item.count, `Internal Prior #${pIdx + 1}`, item.cancerous);
      const priorStudyProtected = {
        ...samePatientFields,
        StudyInstanceUID: existingUID,
        StudyDate: existingDate,
        StudyTime: "000000",
        AccessionNumber: String(Math.floor(100000 + Math.random() * 900000)),
        StudyID: String(Math.floor(100000 + Math.random() * 900000))
      };

      const finalImages = applyStudyProtectedFields(newImages, priorStudyProtected);
      newList[pIdx] = { ...item, images: finalImages };
      return { ...prev, internal_priors: newList };
    });
  };

  const updateInternalTag = (pIdx, iIdx, tagKey, val) => {
    setConfig(prev => {
      const newList = [...prev.internal_priors];
      const newImgs = [...newList[pIdx].images];
      newImgs[iIdx] = {
        tags: { ...newImgs[iIdx].tags, [tagKey]: val }
      };
      newList[pIdx].images = newImgs;
      return { ...prev, internal_priors: newList };
    });
  };

  const removeInternalTag = (pIdx, iIdx, tagKey) => {
    setConfig(prev => {
      const newList = [...prev.internal_priors];
      const newImgs = [...newList[pIdx].images];
      const newTags = { ...newImgs[iIdx].tags };
      delete newTags[tagKey];
      newImgs[iIdx] = { tags: newTags };
      newList[pIdx].images = newImgs;
      return { ...prev, internal_priors: newList };
    });
  };

  // -----------------------------
  // STEP 4: External Priors
  // -----------------------------
  const initExternalPriors = (newCount) => {
    setConfig(prev => {
      let arr = [...prev.external_priors];

      const curImages = prev.current_study.images;
      if (curImages.length === 0) {
        return { ...prev, external_priors: [] };
      }
      const firstCurrent = curImages[0].tags;

      const samePatientFields = {
        PatientName: firstCurrent.PatientName,
        PatientID: firstCurrent.PatientID,
        PatientBirthDate: firstCurrent.PatientBirthDate,
        PatientSex: firstCurrent.PatientSex
      };

      if (newCount < arr.length) {
        arr = arr.slice(0, newCount);
      } else {
        while (arr.length < newCount) {
          let images = generateDicomImages(4, "External Prior", false);

          const olderDate = randomPastStudyDate(firstCurrent.StudyDate);

          const priorStudyProtected = {
            ...samePatientFields,
            StudyInstanceUID: randomUID(),
            StudyDate: olderDate,
            StudyTime: "000000",
            AccessionNumber: String(Math.floor(100000 + Math.random() * 900000)),
            StudyID: String(Math.floor(100000 + Math.random() * 900000))
          };

          images = applyStudyProtectedFields(images, priorStudyProtected);

          arr.push({
            cancerous: false,
            type: "external_screening",
            count: 4,
            images
          });
        }
      }
      return { ...prev, external_priors: arr };
    });
  };

  const updateExternalPrior = (pIdx, field, val) => {
    setConfig(prev => {
      const newList = [...prev.external_priors];
      newList[pIdx] = { ...newList[pIdx], [field]: val };
      return { ...prev, external_priors: newList };
    });
  };

  const regenerateExternalImages = (pIdx) => {
    setConfig(prev => {
      const newList = [...prev.external_priors];
      const item = newList[pIdx];

      const curImages = prev.current_study.images;
      if (curImages.length === 0) return prev;

      const firstCurrent = curImages[0].tags;
      const samePatientFields = {
        PatientName: firstCurrent.PatientName,
        PatientID: firstCurrent.PatientID,
        PatientBirthDate: firstCurrent.PatientBirthDate,
        PatientSex: firstCurrent.PatientSex
      };

      let existingDate = "19700101";
      let existingUID = randomUID();
      if (item.images.length > 0) {
        const firstPrior = item.images[0].tags;
        existingDate = firstPrior.StudyDate || randomPastStudyDate(firstCurrent.StudyDate);
        existingUID = firstPrior.StudyInstanceUID || randomUID();
      }

      let images = generateDicomImages(item.count, `External Prior #${pIdx + 1}`, item.cancerous);
      const priorStudyProtected = {
        ...samePatientFields,
        StudyInstanceUID: existingUID,
        StudyDate: existingDate,
        StudyTime: "000000",
        AccessionNumber: String(Math.floor(100000 + Math.random() * 900000)),
        StudyID: String(Math.floor(100000 + Math.random() * 900000))
      };

      images = applyStudyProtectedFields(images, priorStudyProtected);
      newList[pIdx] = { ...item, images };
      return { ...prev, external_priors: newList };
    });
  };

  const updateExternalTag = (pIdx, iIdx, tagKey, val) => {
    setConfig(prev => {
      const newList = [...prev.external_priors];
      const newImgs = [...newList[pIdx].images];
      newImgs[iIdx] = {
        tags: { ...newImgs[iIdx].tags, [tagKey]: val }
      };
      newList[pIdx].images = newImgs;
      return { ...prev, external_priors: newList };
    });
  };

  const removeExternalTag = (pIdx, iIdx, tagKey) => {
    setConfig(prev => {
      const newList = [...prev.external_priors];
      const newImgs = [...newList[pIdx].images];
      const newTags = { ...newImgs[iIdx].tags };
      delete newTags[tagKey];
      newImgs[iIdx] = { tags: newTags };
      newList[pIdx].images = newImgs;
      return { ...prev, external_priors: newList };
    });
  };

  // -----------------------------
  // STEP 5: Generate
  // -----------------------------
  const handleFinish = () => {
    console.log("Final config to be sent to Python:", config);
    ipcRenderer.send('log-update', "FINAL CONFIG from Step 5:\n" + JSON.stringify(config, null, 2) + "\n\n");
    ipcRenderer.send('start-power-customize', config);
  };

  // -----------------------------
  // RENDER STEPS
  // -----------------------------
  return (
    <div style={{ padding: 20, fontFamily: 'sans-serif' }}>
      {/* Step 1 */}
      {step === 1 && (
        <div>
          <h2>Step 1: Current Study Setup</h2>
          <div style={{ marginBottom: 10 }}>
            <label>
              <input
                type="checkbox"
                checked={config.current_study.cancerous}
                onChange={e => handleCurrentChange('cancerous', e.target.checked)}
              />
              Cancerous?
            </label>
          </div>
          <div style={{ marginBottom: 10 }}>
            <label>
              DICOM Count (0–20):{" "}
              <input
                type="number"
                min="0"
                max="20"
                value={config.current_study.count}
                onChange={e => handleCurrentChange('count', Number(e.target.value))}
              />
            </label>
          </div>
          <div style={{ marginBottom: 10 }}>
            <label>
              Output Directory:{" "}
              <input
                type="text"
                value={config.outputDir}
                onChange={e => setConfig(prev => ({ ...prev, outputDir: e.target.value }))}
                placeholder="/some/output/folder"
              />
            </label>
            <button onClick={() => ipcRenderer.send('choose-directory')}>Browse</button>
          </div>
          <button onClick={() => { initCurrentImages(); nextStep(); }}>Next</button>
        </div>
      )}

      {/* Step 2 */}
      {step === 2 && (
        <div>
          <h2>Step 2: Edit Current Study DICOM Tags</h2>
          {config.current_study.images.length === 0 ? (
            <p>No images (count=0)</p>
          ) : (
            <div style={{ maxHeight: 400, overflowY: 'auto', border: '1px solid #ccc', padding: 10 }}>
              {config.current_study.images.map((img, idx) => (
                <div key={idx} style={{ marginBottom: 10 }}>
                  <h4>Image {idx + 1} (View: {img.tags.ViewPosition})</h4>
                  {Object.entries(img.tags).map(([tagKey, tagVal]) => (
                    <div key={tagKey} style={{ marginBottom: 4, display: 'flex', alignItems: 'center' }}>
                      <label style={{ marginRight: 8 }}>{tagKey}:</label>
                      <input
                        type="text"
                        value={tagVal}
                        onChange={e => updateCurrentTag(idx, tagKey, e.target.value)}
                        style={{ marginRight: 8 }}
                      />
                      {/* Delete button */}
                      <button onClick={() => removeCurrentTag(idx, tagKey)}>Delete</button>
                    </div>
                  ))}
                  <hr />
                </div>
              ))}
            </div>
          )}
          <div style={{ marginTop: 20 }}>
            <button onClick={() => setStep(1)}>Back</button>
            <button onClick={() => setStep(3)}>Next</button>
          </div>
        </div>
      )}

      {/* Step 3: Internal Priors */}
      {step === 3 && (
        <div>
          <h2>Step 3: Internal Priors</h2>
          <p>Enter number of internal priors:</p>
          <input
            type="number"
            min="0"
            max="20"
            value={internalCount}
            onChange={e => {
              const val = Number(e.target.value);
              setInternalCount(val);
              initInternalPriors(val);
            }}
          />
          <div style={{ maxHeight: 400, overflowY: 'auto', border: '1px solid #ccc', padding: 10, marginTop: 10 }}>
            {config.internal_priors.map((prior, pIdx) => (
              <div key={pIdx} style={{ border: '1px solid #ddd', padding: 10, marginBottom: 10 }}>
                <h4>Internal Prior #{pIdx + 1}</h4>
                <label>
                  <input
                    type="checkbox"
                    checked={prior.cancerous}
                    onChange={e => {
                      const checked = e.target.checked;
                      updateInternalPrior(pIdx, 'cancerous', checked);
                      regenerateInternalImages(pIdx);
                    }}
                  />
                  Cancerous?
                </label>
                <div style={{ margin: '6px 0' }}>
                  <label>
                    DICOM Count (0–20):{" "}
                    <input
                      type="number"
                      min="0"
                      max="20"
                      value={prior.count}
                      onChange={e => {
                        const val = Number(e.target.value);
                        updateInternalPrior(pIdx, 'count', val);
                        regenerateInternalImages(pIdx);
                      }}
                    />
                  </label>
                </div>
                {prior.images.map((img, iIdx) => (
                  <div key={iIdx} style={{ border: '1px solid #eee', padding: 8, marginBottom: 6 }}>
                    <strong>Image {iIdx + 1} (View: {img.tags.ViewPosition})</strong>
                    {Object.entries(img.tags).map(([tagKey, tagVal]) => (
                      <div key={tagKey} style={{ marginBottom: 4, display: 'flex', alignItems: 'center' }}>
                        <label style={{ marginRight: 8 }}>{tagKey}:</label>
                        <input
                          type="text"
                          value={tagVal}
                          onChange={ev => updateInternalTag(pIdx, iIdx, tagKey, ev.target.value)}
                          style={{ marginRight: 8 }}
                        />
                        {/* Delete button */}
                        <button onClick={() => removeInternalTag(pIdx, iIdx, tagKey)}>Delete</button>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            ))}
          </div>
          <div style={{ marginTop: 20 }}>
            <button onClick={() => setStep(2)}>Back</button>
            <button onClick={() => setStep(4)}>Next</button>
          </div>
        </div>
      )}

      {/* Step 4: External Priors */}
      {step === 4 && (
        <div>
          <h2>Step 4: External Priors</h2>
          <p>Enter number of external priors:</p>
          <input
            type="number"
            min="0"
            max="20"
            value={externalCount}
            onChange={e => {
              const val = Number(e.target.value);
              setExternalCount(val);
              initExternalPriors(val);
            }}
          />
          <div style={{ maxHeight: 400, overflowY: 'auto', border: '1px solid #ccc', padding: 10, marginTop: 10 }}>
            {config.external_priors.map((prior, pIdx) => (
              <div key={pIdx} style={{ border: '1px solid #ddd', padding: 10, marginBottom: 10 }}>
                <h4>External Prior #{pIdx + 1}</h4>
                <label>
                  <input
                    type="checkbox"
                    checked={prior.cancerous}
                    onChange={e => {
                      const checked = e.target.checked;
                      updateExternalPrior(pIdx, 'cancerous', checked);
                      regenerateExternalImages(pIdx);
                    }}
                  />
                  Cancerous?
                </label>
                <div style={{ margin: '6px 0' }}>
                  <label>
                    DICOM Count (0–20):{" "}
                    <input
                      type="number"
                      min="0"
                      max="20"
                      value={prior.count}
                      onChange={e => {
                        const val = Number(e.target.value);
                        updateExternalPrior(pIdx, 'count', val);
                        regenerateExternalImages(pIdx);
                      }}
                    />
                  </label>
                </div>
                {prior.images.map((img, iIdx) => (
                  <div key={iIdx} style={{ border: '1px solid #eee', padding: 8, marginBottom: 6 }}>
                    <strong>Image {iIdx + 1} (View: {img.tags.ViewPosition})</strong>
                    {Object.entries(img.tags).map(([tagKey, tagVal]) => (
                      <div key={tagKey} style={{ marginBottom: 4, display: 'flex', alignItems: 'center' }}>
                        <label style={{ marginRight: 8 }}>{tagKey}:</label>
                        <input
                          type="text"
                          value={tagVal}
                          onChange={ev => updateExternalTag(pIdx, iIdx, tagKey, ev.target.value)}
                          style={{ marginRight: 8 }}
                        />
                        {/* Delete button */}
                        <button onClick={() => removeExternalTag(pIdx, iIdx, tagKey)}>Delete</button>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            ))}
          </div>
          <div style={{ marginTop: 20 }}>
            <button onClick={() => setStep(3)}>Back</button>
            <button onClick={() => setStep(5)}>Next</button>
          </div>
        </div>
      )}

      {/* Step 5 */}
      {step === 5 && (
        <div>
          <h2>Step 5: Final Review & Generate</h2>
          <p>Review the JSON config below. Click Generate to run the Python script.</p>
          <pre style={{ background: '#f0f0f0', padding: 10, maxHeight: 300, overflowY: 'auto' }}>
            {JSON.stringify(config, null, 2)}
          </pre>
          <div style={{ marginTop: 20 }}>
            <button onClick={() => setStep(4)}>Back</button>
            <button style={{ marginLeft: 10 }} onClick={handleFinish}>
              Generate Dataset
            </button>
          </div>
          <div id="logPanel" style={{ marginTop: 20, display: 'none' }}>
            <h4>Logs</h4>
            <div style={{ whiteSpace: 'pre-wrap' }}>{logs}</div>
          </div>
        </div>
      )}
    </div>
  );
}
