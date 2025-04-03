#!/usr/bin/env python3
"""
Generate MG DICOMs for either:
  --power-customize <config.json>  (Wizard approach)  => writes to "power_customized_dataset"
  --scenario <scenario_name>       (Presets approach) => writes to "scenario_{scenario_name}_dataset"

Or do:
  --list-scenarios  to see which scenario_*.py are available in /presets.

Example usage:
  # List scenario names
  python generate_dicom_dataset.py --output . --list-scenarios

  # Generate a scenario
  python generate_dicom_dataset.py --output /path/to/out --scenario faulty_prior

  # Generate from your wizard config
  python generate_dicom_dataset.py --output /path/to/out --power-customize config.json
"""

import os
import sys
import json
import random
import argparse
from pathlib import Path
from datetime import datetime

import numpy as np
from PIL import Image, ImageFilter
import pydicom
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import generate_uid
import logging
import importlib.util

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("dicomgen")

# (A) Dynamically load scenario classes

def load_scenario_classes():
    """
    Scan the /presets folder for any files named scenario_*.py.
    For each file, import it, look for classes that define SCENARIO_NAME,
    and build a {scenario_name: scenario_class} map.
    """
    scenario_map = {}
    scenario_folder = Path(__file__).parent / "presets"
    if not scenario_folder.is_dir():
        return scenario_map

    for file in scenario_folder.glob("scenario_*.py"):
        mod_name = file.stem
        spec = importlib.util.spec_from_file_location(mod_name, str(file))
        if not spec:
            continue
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        for attr_name in dir(mod):
            obj = getattr(mod, attr_name)
            if isinstance(obj, type):
                scenario_name = getattr(obj, "SCENARIO_NAME", None)
                if scenario_name:
                    scenario_map[scenario_name] = obj
    return scenario_map


# (B) Synthetic Pixel Data Generation

def generate_synthetic_mammo_8bit(width, height):
    """Generate a synthetic 8-bit grayscale array."""
    gradient = np.tile(np.linspace(80, 160, width, dtype=np.uint8), (height, 1))
    noise = np.random.randint(0, 30, (height, width), dtype=np.uint8)
    arr = np.clip(gradient + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr, mode="L")
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    return np.array(img, dtype=np.uint8).tobytes()

def generate_synthetic_mammo_16bit(width, height, bits_stored=12):
    """Generate a 16-bit array with intensities up to 2^bits_stored - 1."""
    max_val = (1 << bits_stored) - 1
    base = np.tile(np.linspace(500, max_val - 500, width, dtype=np.uint16), (height, 1))
    noise = np.random.randint(0, 500, (height, width), dtype=np.uint16)
    arr = np.clip(base + noise, 0, max_val).astype(np.uint16)
    return arr.tobytes()  # 2 bytes per pixel

def random_uid():
    return "1.2.826.0.1.3680043.8.498." + str(random.randint(10**9, 10**10 - 1))


# (C) create_mg_dicom: The main DICOM-building function

def create_mg_dicom(outfile, tags, preview=False):
    """
    Build a DICOM from 'tags'. If a template is found (based on is_cancer/view_pos),
    we load that pixel data; otherwise, generate synthetic. Then possibly override
    geometry (force_large_dims), skip pixel data, etc. Finally, fill DICOM fields & write.

    Note: If the scenario removed 'Rows'/'Columns' from tags, we remove them
    from ds so that the final DICOM truly lacks those fields.
    """
    # 1) Basic fields
    is_cancer   = tags.get("cancerous", False)
    sop_class   = tags.get("SOPClassUID", "1.2.840.10008.5.1.4.1.1.1.2")  # default MG
    modality    = tags.get("Modality", "MG")
    bits_alloc  = int(tags.get("BitsAllocated", 16))
    bits_stored = int(tags.get("BitsStored", 12))

    rows = int(tags.get("Rows", 256))
    cols = int(tags.get("Columns", 256))

    view_pos      = tags.get("ViewPosition", "CC")
    subfolder     = "cancerous" if is_cancer else "non-cancerous"
    template_path = Path(__file__).parent / "templates" / subfolder / f"{view_pos}.dcm"

    pixel_data = None
    template_loaded = False

    # 2) Attempt to load a template from local /templates
    try:
        if template_path.exists():
            logger.info(f"Attempting template {template_path} (view={view_pos})")
            tmpl_ds = pydicom.dcmread(str(template_path), force=True)
            pixel_data  = tmpl_ds.PixelData
            rows        = tmpl_ds.Rows
            cols        = tmpl_ds.Columns
            bits_alloc  = tmpl_ds.BitsAllocated
            bits_stored = tmpl_ds.BitsStored
            template_loaded = True
            logger.info(f"Template loaded => rows={rows}, cols={cols}, "
                        f"bits_alloc={bits_alloc}, bits_stored={bits_stored}")
        else:
            logger.info(f"No template at {template_path}, using synthetic data.")
    except Exception as e:
        logger.warning(f"Error reading template {template_path}: {e}. Using synthetic data.")
        pixel_data = None

    # 3) If no template => generate synthetic
    if pixel_data is None:
        if bits_alloc == 8 and bits_stored == 8:
            pixel_data = generate_synthetic_mammo_8bit(cols, rows)
            logger.info(f"Synthetic 8-bit => {rows}x{cols}")
        else:
            if bits_stored < 6:
                bits_stored = 6
            if bits_stored > bits_alloc:
                bits_stored = bits_alloc
            pixel_data = generate_synthetic_mammo_16bit(cols, rows, bits_stored)
            logger.info(f"Synthetic {bits_alloc}-bit => {rows}x{cols}, stored={bits_stored}")
    else:
        logger.info("Using template-based pixel data")

    # 4) Scenario overrides
    if tags.get("force_corrupt_pixel"):
        old_len = len(pixel_data)
        new_len = old_len // 2
        pixel_data = pixel_data[:new_len]
        logger.info(f"[CORRUPT_PIXEL] from {old_len} -> {new_len} bytes")

    if tags.get("force_large_dims"):
        new_rows = tags.get("Rows", rows)
        new_cols = tags.get("Columns", cols)
        logger.info(f"[force_large_dims] => {new_rows}x{new_cols}")
        if bits_alloc == 8 and bits_stored == 8:
            pixel_data = generate_synthetic_mammo_8bit(new_cols, new_rows)
        else:
            if bits_stored < 6:
                bits_stored = 6
            if bits_stored > bits_alloc:
                bits_stored = bits_alloc
            pixel_data = generate_synthetic_mammo_16bit(new_cols, new_rows, bits_stored)
        rows = int(new_rows)
        cols = int(new_cols)

    if tags.get("no_pixel_data"):
        logger.info("[no_pixel_data] removing ds.PixelData completely.")
        pixel_data = None

    # 5) Build File Meta
    file_meta = FileMetaDataset()
    file_meta.FileMetaInformationVersion = b"\0\1"
    sop_uid = tags.get("SOPInstanceUID", random_uid())
    file_meta.MediaStorageSOPClassUID    = sop_class
    file_meta.MediaStorageSOPInstanceUID = sop_uid
    file_meta.TransferSyntaxUID          = "1.2.840.10008.1.2"
    file_meta.ImplementationClassUID     = random_uid()

    ds = FileDataset(outfile, {}, file_meta=file_meta, preamble=b"\0"*128)
    ds.SOPClassUID = sop_class

    # 6) Fill geometry
    ds.Rows                  = rows
    ds.Columns               = cols
    ds.BitsAllocated         = bits_alloc
    ds.BitsStored            = bits_stored
    ds.HighBit               = bits_stored - 1 if bits_stored <= bits_alloc else bits_alloc - 1
    ds.PixelRepresentation   = 0
    ds.SamplesPerPixel       = 1
    ds.PhotometricInterpretation = "MONOCHROME2"

    if tags.get("force_bits_mismatch"):
        forced_alloc   = tags.get("BitsAllocated", bits_alloc)
        forced_stored  = tags.get("BitsStored", bits_stored)
        forced_highbit = tags.get("HighBit", forced_stored - 1)
        ds.BitsAllocated = int(forced_alloc)
        ds.BitsStored    = int(forced_stored)
        ds.HighBit       = int(forced_highbit)
        logger.info(f"[BITS_MISMATCH] => Alloc={ds.BitsAllocated}, "
                    f"Stored={ds.BitsStored}, HighBit={ds.HighBit}")

    # 7) Set or remove PixelData
    if pixel_data is not None:
        ds.PixelData = pixel_data
    else:
        if "PixelData" in ds:
            del ds["PixelData"]

    # Basic MG fields
    ds.Modality                     = modality
    ds.PresentationIntentType       = "FOR PRESENTATION"
    ds.PixelIntensityRelationship   = "LOG"
    ds.PixelIntensityRelationshipSign = -1
    ds.LossyImageCompression       = "00"
    ds.BurnedInAnnotation          = "NO"
    ds.QualityControlImage         = "NO"

    # 8) Fill from tags
    optional_attrs = [
        ("SOPInstanceUID",       "SOPInstanceUID",       "str"),
        ("StudyInstanceUID",     "StudyInstanceUID",     "str"),
        ("SeriesInstanceUID",    "SeriesInstanceUID",    "str"),
        ("StudyDate",            "StudyDate",            "str"),
        ("StudyTime",            "StudyTime",            "str"),
        ("PatientName",          "PatientName",          "str"),
        ("PatientID",            "PatientID",            "str"),
        ("PatientBirthDate",     "PatientBirthDate",     "str"),
        ("PatientSex",           "PatientSex",           "str"),
        ("StudyID",              "StudyID",              "str"),
        ("AccessionNumber",      "AccessionNumber",      "str"),
        ("StudyDescription",     "StudyDescription",     "str"),
        ("SeriesDescription",    "SeriesDescription",    "str"),
        ("InstanceNumber",       "InstanceNumber",       "int"),
        ("SeriesNumber",         "SeriesNumber",         "int"),
        ("ViewPosition",         "ViewPosition",         "str"),
        ("WindowCenter",         "WindowCenter",         "str"),
        ("WindowWidth",          "WindowWidth",          "str"),
        ("Manufacturer",         "Manufacturer",         "str"),
        ("BodyPartExamined",     "BodyPartExamined",     "str"),
        ("Laterality",           "Laterality",           "str"),
        ("DetectorType",         "DetectorType",         "str"),
        ("SoftwareVersions",     "SoftwareVersions",     "str"),
        ("PresentationLUTShape", "PresentationLUTShape", "str"),
    ]
    for (dicom_name, tag_key, valtype) in optional_attrs:
        if tag_key in tags:
            raw_val = tags[tag_key]
            if valtype == "int":
                try:
                    raw_val = int(raw_val)
                except ValueError:
                    raw_val = 1
            setattr(ds, dicom_name, raw_val)

    # 9) Private tags
    for k, v in tags.items():
        if k.startswith("Private_"):
            try:
                parts = k.split("_", 2)  # e.g. ["Private","9999","0010"]
                group_hex = parts[1]
                elem_hex  = parts[2]
                group = int(group_hex, 16)
                elem  = int(elem_hex, 16)
                ds.add_new((group, elem), "LO", v)
                logger.info(f"[PRIVATE TAG] {k} => group=0x{group_hex}, elem=0x{elem_hex}, val={v}")
            except Exception as ex:
                logger.warning(f"Failed to parse private tag {k}, ignoring. Error={ex}")

    # 10) If scenario removed Rows/Columns, remove from ds
    if "Rows" not in tags and "Rows" in ds:
        del ds["Rows"]
    if "Columns" not in tags and "Columns" in ds:
        del ds["Columns"]

    # Save if not preview
    if not preview:
        ds.save_as(outfile, enforce_file_format=True)
        logger.info(
            f"[DEBUG] Created => {outfile} (rows={ds.get('Rows','(none)')}, "
            f"cols={ds.get('Columns','(none)')}, bits={ds.BitsAllocated}, stored={ds.BitsStored})"
        )

    return ds


# (D) JSON build for the final study

def build_real_json_for_study(study_cfg, images_meta):
    if not images_meta:
        return {
            "first_name": "",
            "last_name": "",
            "date_of_birth": "",
            "patient_id": "",
            "study_id": "",
            "study_date": "",
            "study_instance_uid": "",
            "accession_number": "",
            "study_description": "",
            "sop_instance_uids": [],
            "prior_study_data": None
        }

    first_img_tags = images_meta[0].get("tags", {})
    patientName = first_img_tags.get("PatientName", "")
    parts = patientName.split(" ", 1)
    fn = parts[0] if len(parts) > 0 else ""
    ln = parts[1] if len(parts) > 1 else ""

    birth = first_img_tags.get("PatientBirthDate", "")
    if len(birth) == 8:
        birth = f"{birth[:4]}-{birth[4:6]}-{birth[6:8]}"

    patID = first_img_tags.get("PatientID", "")
    stID  = first_img_tags.get("StudyID", "")
    sDate = first_img_tags.get("StudyDate", "")
    if len(sDate) == 8:
        sDate = f"{sDate[:4]}-{sDate[4:6]}-{sDate[6:8]}T00:00:00+00:00"

    stUID = first_img_tags.get("StudyInstanceUID", "")
    acc   = first_img_tags.get("AccessionNumber", "")
    study_desc = first_img_tags.get("StudyDescription", "")

    sop_uids = []
    for im in images_meta:
        suid = im.get("SOPInstanceUID", "")
        sop_uids.append(suid)

    return {
        "first_name": fn,
        "last_name": ln,
        "date_of_birth": birth,
        "patient_id": patID,
        "study_id": stID,
        "study_date": sDate,
        "study_instance_uid": stUID,
        "accession_number": acc,
        "study_description": study_desc,
        "sop_instance_uids": sop_uids,
        "prior_study_data": None
    }

def parse_study_date(json_obj):
    sdate = json_obj.get("study_date", "")
    if not sdate:
        return None
    try:
        date_only = sdate.split("T")[0]
        return datetime.strptime(date_only, "%Y-%m-%d")
    except:
        return None


# (E) Create an entire "study" from config

def generate_study_from_config(study_cfg, preview=False):
    images_list = study_cfg.get("images", [])
    if not images_list:
        rnd_study_uid = generate_uid()
        logger.info(f"No images found. Using fallback StudyUID={rnd_study_uid}")
        return (rnd_study_uid, [])

    first_tags = images_list[0].get("tags", {})
    study_uid = first_tags.get("StudyInstanceUID", random_uid())
    logger.info(f"Generating study: study_uid={study_uid}, image_count={len(images_list)}")

    images_meta = []
    for i, imgObj in enumerate(images_list):
        user_tags = imgObj.get("tags", {})
        sop_uid   = user_tags.get("SOPInstanceUID", random_uid())
        images_meta.append({
            "sop_uid": sop_uid,
            "tags": user_tags
        })
    return (study_uid, images_meta)

def create_dicoms_for_study(study_uid, images_meta, dicom_base, preview=False):
    study_folder = os.path.join(dicom_base, study_uid)
    os.makedirs(study_folder, exist_ok=True)

    out_meta = []
    for im in images_meta:
        sop_uid   = im["sop_uid"]
        user_tags = im["tags"]

        out_path = os.path.join(study_folder, f"{sop_uid}.dcm")

        # If scenario wants to skip physically writing
        if user_tags.get("skip_writing"):
            logger.info(f"[MISSING_DICOM] skip_writing=True => Not creating file for {sop_uid}")
            out_meta.append({
                "filename": f"{sop_uid}.dcm (SKIPPED)",
                "SOPInstanceUID": sop_uid,
                "tags": user_tags
            })
            continue

        ds = create_mg_dicom(out_path, user_tags, preview=preview)
        out_meta.append({
            "filename": f"{sop_uid}.dcm",
            "SOPInstanceUID": sop_uid,
            "tags": user_tags
        })
    return out_meta

def chainify_studies(prior_jsons):
    if not prior_jsons:
        return None
    prior_jsons_sorted = sorted(prior_jsons, key=lambda j: parse_study_date(j) or datetime.min)
    oldest_idx = 0
    prior_jsons_sorted[oldest_idx]["prior_study_data"] = None
    for i in range(oldest_idx + 1, len(prior_jsons_sorted)):
        prior_jsons_sorted[i]["prior_study_data"] = prior_jsons_sorted[i - 1]
    return prior_jsons_sorted[-1]


# (F) generate_dataset_from_configdict

def generate_dataset_from_configdict(
    output_dir, config_dict, preview=False,
    dataset_name="power_customized_dataset",
    scenario_name=None
):
    """
    The main function that takes a config (wizard or scenario) and writes:
      - DICOMs to <dataset_name>/dicoms/
      - JSON(s) to <dataset_name>/jsons/
    """
    dataset_folder = os.path.join(output_dir, dataset_name)
    os.makedirs(dataset_folder, exist_ok=True)

    dicoms_folder = os.path.join(dataset_folder, "dicoms")
    jsons_folder  = os.path.join(dataset_folder, "jsons")
    os.makedirs(dicoms_folder, exist_ok=True)
    os.makedirs(jsons_folder, exist_ok=True)

    # If this scenario returns *two* configs, handle them separately
    if ("external_cfg" in config_dict) and ("current_cfg" in config_dict):
        logger.info("[DUAL_CONFIG] Found 'external_cfg' and 'current_cfg' => generating two subfolders")

        # 1) external_cfg
        generate_dataset_from_configdict(
            output_dir=output_dir,
            config_dict=config_dict["external_cfg"],
            preview=preview,
            dataset_name="external_priors_only",
            scenario_name=scenario_name
        )
        # 2) current_cfg
        generate_dataset_from_configdict(
            output_dir=output_dir,
            config_dict=config_dict["current_cfg"],
            preview=preview,
            dataset_name="current_study_only",
            scenario_name=scenario_name
        )
        return  # done

    # Otherwise, do the normal single-config approach

    # 1) Current study
    cur_cfg = config_dict.get("current_study", {})
    cs_uid, cs_images = generate_study_from_config(cur_cfg, preview=preview)
    cs_images_meta    = create_dicoms_for_study(cs_uid, cs_images, dicoms_folder, preview=preview)
    current_json      = build_real_json_for_study(cur_cfg, cs_images_meta)

    # 2) Gather prior JSONs
    all_prior_jsons = []

    for idx, p_cfg in enumerate(config_dict.get("internal_priors", []), start=1):
        p_uid, p_images = generate_study_from_config(p_cfg, preview=preview)
        if scenario_name == "missing_dicom" and p_images:
            logger.info("[missing_dicom] Mark last image to skip writing but keep in JSON.")
            p_images[-1]["tags"]["skip_writing"] = True
        p_images_meta = create_dicoms_for_study(p_uid, p_images, dicoms_folder, preview=preview)
        p_json = build_real_json_for_study(p_cfg, p_images_meta)
        all_prior_jsons.append(p_json)

    # external priors
    for idx, e_cfg in enumerate(config_dict.get("external_priors", []), start=1):
        e_uid, e_images = generate_study_from_config(e_cfg, preview=preview)
        e_images_meta = create_dicoms_for_study(e_uid, e_images, dicoms_folder, preview=preview)
        e_json = build_real_json_for_study(e_cfg, e_images_meta)
        all_prior_jsons.append(e_json)

    # 3) Link them in a singly-linked chain
    if all_prior_jsons:
        newest_prior = chainify_studies(all_prior_jsons)
        current_json["prior_study_data"] = newest_prior
    else:
        current_json["prior_study_data"] = None

    current_json["external_priors"] = current_json.get("external_priors", [])

    # 4) Write final JSON
    cs_json_path = os.path.join(jsons_folder, f"{cs_uid}.json")
    if not preview:
        with open(cs_json_path, "w") as jf:
            json.dump(current_json, jf, indent=2)
        logger.info(f"[DEBUG] Wrote final merged JSON => {cs_json_path}")
        logger.info("All done. One folder per StudyInstanceUID, plus one final JSON for the current study.")
    else:
        logger.info(f"[PREVIEW] Would have written JSON => {cs_json_path}")


# ---------------------------------------------------------------------
# (G) MAIN
# ---------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate MG DICOM dataset.")
    parser.add_argument("--output", "-o", required=True, help="Output directory")
    parser.add_argument("--power-customize", "-c", help="Wizard config JSON")
    parser.add_argument("--scenario", help="Name of preset scenario to generate")
    parser.add_argument("--preview", "-p", action="store_true", help="No file writing if set.")
    parser.add_argument("--list-scenarios", action="store_true", help="List scenario names.")
    args = parser.parse_args()

    scenario_map = load_scenario_classes()

    if args.list_scenarios:
        for sname in scenario_map.keys():
            print(sname)
        sys.exit(0)

    if args.power_customize and args.scenario:
        logger.error("ERROR: Please specify either --power-customize or --scenario, not both.")
        sys.exit(1)
    if not (args.power_customize or args.scenario):
        logger.error("ERROR: Must supply either --power-customize <json> or --scenario <name>.")
        sys.exit(1)

    if not os.path.isdir(args.output):
        logger.error(f"Output directory invalid: {args.output}")
        sys.exit(1)

    # Wizard approach
    if args.power_customize:
        cfg_path = args.power_customize
        if not os.path.isfile(cfg_path):
            logger.error(f"ERROR: config file not found: {cfg_path}")
            sys.exit(1)

        with open(cfg_path, "r") as f:
            config_dict = json.load(f)

        generate_dataset_from_configdict(
            output_dir=args.output,
            config_dict=config_dict,
            preview=args.preview,
            dataset_name="power_customized_dataset",
            scenario_name=None
        )

    else:
        # Scenario approach
        scenario_name = args.scenario
        if scenario_name not in scenario_map:
            logger.error(f"ERROR: Unknown scenario '{scenario_name}'. Use --list-scenarios.")
            sys.exit(1)

        scenario_class = scenario_map[scenario_name]
        scenario_obj   = scenario_class()
        scenario_cfg   = scenario_obj.build_scenario_config()

        out_folder_name = f"scenario_{scenario_name}_dataset"

        generate_dataset_from_configdict(
            output_dir=args.output,
            config_dict=scenario_cfg,
            preview=args.preview,
            dataset_name=out_folder_name,
            scenario_name=scenario_name
        )

if __name__ == "__main__":
    main()
