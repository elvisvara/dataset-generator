#!/usr/bin/env python3
"""
not 100 percent current yet: attempt to simulate a scenario like the Aachen partner case where the ingested study
contains eight images (4 valid and 4 corrupted duplicates), butthe viewer to show no images.
"""

import random
from datetime import datetime, timedelta
import json

from presets.scenario_base import (
    ScenarioBase,
    random_uid,
    random_six_digit,
    random_date_yyyymmdd,
    parse_yyyymmdd,
    format_yyyymmdd,
)

class ScenarioAachenNoImages(ScenarioBase):
    SCENARIO_NAME = "aachen_no_images"  

    def create_current_study_config(self, is_cancerous=False):

        study_uid = random_uid()
        study_id = random_six_digit()
        accession = random_six_digit()
        views = ["RCC", "LCC", "RMLO", "LMLO"]
        images = []
        
        # Generate 4 "valid" images.
        for i, vp in enumerate(views):
            tags = self.make_mg_image_tags(
                view_position=vp,
                is_cancerous=is_cancerous,
                study_uid=study_uid,
                study_date=self.current_study_date,
                study_id=study_id,
                accession=accession,
            )
            tags["StudyDescription"] += " - Current Study (Valid)"
            tags["cancerous"] = is_cancerous
            tags["InstanceNumber"] = i + 1
            tags["SOPInstanceUID"] = random_uid()
            images.append({"tags": tags})
        
        # Generate 4 duplicate images that are corrupted.
        for i, vp in enumerate(views):
            dup_tags = self.make_mg_image_tags(
                view_position=vp,
                is_cancerous=is_cancerous,
                study_uid=study_uid,
                study_date=self.current_study_date,
                study_id=study_id,
                accession=accession,
            )
            dup_tags["StudyDescription"] += " - Current Study (Duplicate Corrupted)"
            dup_tags["cancerous"] = is_cancerous
            dup_tags["InstanceNumber"] = i + 5  
            # Simulate corruption
            dup_tags["Rows"] = 0
            dup_tags["Columns"] = 0
            dup_tags["CorruptPixelData"] = True
            dup_tags["SOPInstanceUID"] = random_uid()
            images.append({"tags": dup_tags})
        
        return {
            "cancerous": is_cancerous,
            "count": len(images),
            "images": images
        }

    def build_scenario_config(self):
        current_study_cfg = self.create_current_study_config(is_cancerous=False)
        return {
            "current_study": current_study_cfg,
            "internal_priors": [],
            "external_priors": []
        }

if __name__ == "__main__":
    scenario = ScenarioAachenNoImages()
    config = scenario.build_scenario_config()
    print(json.dumps(config, indent=2))
