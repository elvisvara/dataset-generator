#!/usr/bin/env python3
"""
ScenarioBase: a common base class for scenario classes.

Key features:
- A single random patient name, ID, and birthdate is generated and reused
  for both current and prior studies.
- A 'cancerous' flag affects the StudyDescription (e.g., "Cancerous Study").
- All images get standard mammography tags (Manufacturer, BodyPartExamined, etc.).
- Each 4-view set includes views (RCC, LCC, RMLO, LMLO) with correct Laterality.
- Patients age range of [50..75] so the ingestion pipeline won’t reject them.

Child classes (e.g. scenario_faulty_prior.py) can override build_scenario_config()
to add special "faulty" tags or logic.
"""

import random
from datetime import datetime, timedelta
from pydicom.uid import generate_uid
import json

FIRST_NAMES = [
    "Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace",
    "Hank", "Irene", "Jack", "Karen", "Larry", "Maria", "Nate", "Olivia",
    "Peter", "Quincy", "Rachel", "Sam", "Tina", "Uma", "Victor", "Wendy", "Xander"
]
LAST_NAMES = [
    "Smith", "Jones", "Brown", "Taylor", "Wilson", "Davis", "Miller", "Anderson",
    "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia",
    "Martinez", "Robinson", "Clark", "Rodriguez", "Lewis", "Lee"
]

def random_uid():
    """Generate a robust random DICOM UID using pydicom's generate_uid."""
    return generate_uid()

def random_date_yyyymmdd(start_year=1950, end_year=2023):
    """Return a random date in [start_year..end_year] in 'YYYYMMDD' format."""
    year = random.randint(start_year, end_year)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{year:04d}{month:02d}{day:02d}"

def parse_yyyymmdd(s: str):
    """Parse a 'YYYYMMDD' string into a datetime object, or return None if invalid."""
    if len(s) != 8:
        return None
    try:
        return datetime.strptime(s, "%Y%m%d")
    except Exception:
        return None

def format_yyyymmdd(dt: datetime):
    """Convert a datetime to a 'YYYYMMDD' formatted string."""
    return dt.strftime("%Y%m%d")

def random_name(preset=None):
    """
    Return a random patient name.
    
    If a preset is provided, it will be sanitized (non-alphanumerics removed),  
    converted to uppercase, and used in full (up to 20 characters) as a prefix  
    to a random 6‑digit number and a random last name.
    
    Example output:
      "CURRENT_STUDYUID_MISMATCH_123456_SMITH"
    """
    last = random.choice(LAST_NAMES)
    suffix = str(random.randint(100000, 999999))
    if preset:
        preset_clean = "".join(filter(str.isalnum, preset)).upper()
        if len(preset_clean) > 20:
            preset_clean = preset_clean[:20]
        return f"{preset_clean}_{suffix}_{last}"
    else:
        first = random.choice(FIRST_NAMES) + suffix
        return f"{first}_{last}"

def random_six_digit():
    """Return a random 6-digit string (used for StudyID or AccessionNumber)."""
    return str(random.randint(0, 999999)).zfill(6)

class ScenarioBase:
    # Child classes should override SCENARIO_NAME with a descriptive preset.
    SCENARIO_NAME = "BASE_SCENARIO"

    def __init__(self):
        """
        Generate a single random patient name, ID, and birthdate.
        Also pick a random current study date between 2010 and 2023 and an age in [50..75].
        """
        self.patient_name = random_name(self.SCENARIO_NAME)
        self.patient_id = str(random.randint(100000, 999999))  

        self.current_study_date = random_date_yyyymmdd(2010, 2023)

        cdt = parse_yyyymmdd(self.current_study_date)
        if cdt is None:
            cdt = datetime(2020, 1, 1)

        self.preset_description = f"Preset: {self.SCENARIO_NAME}"

        # Pick an age between 50 and 75 and calculate the birth year.
        patient_age = random.randint(50, 75)
        birth_year = cdt.year - patient_age
        try:
            birth_dt = cdt.replace(year=birth_year)
        except ValueError:
            # Handle cases like February 29 on non-leap years.
            birth_dt = cdt.replace(year=birth_year, day=28)
        self.birth_date_yyyymmdd = format_yyyymmdd(birth_dt)

        self.patient_sex = random.choice(["M", "F"])

    def make_mg_image_tags(self, view_position, is_cancerous, study_uid, study_date, study_id, accession):
        """
        Create a dictionary of DICOM tags with typical mammography fields.
        """
        # Create a mapping for series UIDs and numbers per view.
        if not hasattr(self, "_series_uid_map"):
            self._series_uid_map = {}
            self._series_num_map = {}
            self._next_series_num = 1

        if view_position not in self._series_uid_map:
            self._series_uid_map[view_position] = random_uid()
            self._series_num_map[view_position] = self._next_series_num
            self._next_series_num += 1

        series_uid = self._series_uid_map[view_position]
        series_num = self._series_num_map[view_position]

        # Set the StudyDescription based on cancerous flag.
        study_desc = "Cancerous Study" if is_cancerous else "Non-cancerous Study"
        study_desc += f" - {self.preset_description}"

        # Determine laterality from the view position.
        dicom_laterality = "L" if view_position.startswith("L") else "R"

        return {
            "SOPInstanceUID": random_uid(),
            "StudyInstanceUID": study_uid,
            "StudyDate": study_date,
            "StudyTime": "000000",
            "StudyID": study_id,
            "AccessionNumber": accession,
            "PatientName": self.patient_name,
            "PatientID": self.patient_id,
            "PatientBirthDate": self.birth_date_yyyymmdd,
            "PatientSex": self.patient_sex,
            "Modality": "MG",
            "ViewPosition": view_position,
            "ImageLaterality": "R" if view_position.startswith("R") else "L",
            "Rows": 256,
            "Columns": 256,
            "BitsAllocated": 16,
            "BitsStored": 12,
            "HighBit": 11,
            "PixelRepresentation": 0,
            "PhotometricInterpretation": "MONOCHROME2",
            "WindowCenter": "2048",
            "WindowWidth": "4096",
            "Manufacturer": "SIEMENS",
            "BodyPartExamined": "BREAST",
            "Laterality": dicom_laterality,
            "DetectorType": "DIRECT",
            "SoftwareVersions": "1.0.0",
            "PresentationLUTShape": "IDENTITY",
            "SeriesInstanceUID": series_uid,
            "SeriesNumber": series_num,
            "SeriesDescription": f"Mammo {view_position}",
            "InstanceNumber": 1,
            "StudyDescription": study_desc,
        }

    def create_current_study_config(self, is_cancerous=False):
        """Return a configuration for a current study with 4 mammography images."""
        study_uid = random_uid()
        study_id = random_six_digit()
        accession = random_six_digit()

        views = ["RCC", "LCC", "RMLO", "LMLO"]
        images = []
        for i, vp in enumerate(views):
            tags = self.make_mg_image_tags(vp, is_cancerous, study_uid, self.current_study_date, study_id, accession)
            tags["StudyDescription"] += " - Current Study"
            tags["cancerous"] = is_cancerous
            tags["InstanceNumber"] = i + 1
            images.append({"tags": tags})

        return {
            "cancerous": is_cancerous,
            "count": len(images),
            "images": images
        }

    def create_prior_config(self, is_cancerous=False):
        """Return a configuration for an internal prior study with 4 images using an older date."""
        cdt = parse_yyyymmdd(self.current_study_date)
        if cdt is None:
            cdt = datetime(2020, 1, 1)
        offset_days = random.randint(30, 1825)
        older_dt = cdt - timedelta(days=offset_days)
        older_date_yyyymmdd = format_yyyymmdd(older_dt)

        study_uid = random_uid()
        study_id = random_six_digit()
        accession = random_six_digit()

        views = ["RCC", "LCC", "RMLO", "LMLO"]
        images = []
        for i, vp in enumerate(views):
            tags = self.make_mg_image_tags(vp, is_cancerous, study_uid, older_date_yyyymmdd, study_id, accession)
            tags["StudyDescription"] += " - Internal Prior"
            tags["cancerous"] = is_cancerous
            tags["InstanceNumber"] = i + 1
            images.append({"tags": tags})

        return {
            "cancerous": is_cancerous,
            "count": len(images),
            "images": images
        }

    def build_scenario_config(self):
        """
        Build and return the scenario configuration.
        By default, this includes one current study (non-cancerous) and no priors.
        Child classes can override this to add additional logic.
        """
        current_study_cfg = self.create_current_study_config(is_cancerous=False)
        return {
            "current_study": current_study_cfg,
            "internal_priors": [],
            "external_priors": []
        }


if __name__ == "__main__":
    # need this fr testing purposess
    sb = ScenarioBase()
    config = sb.build_scenario_config()
    print(json.dumps(config, indent=2))
