"""
ScenarioLargeScaleShallow:
Generates one normal "current" study, plus multiple "internal" priors.
Each prior has exactly ONE "fault injection" from a set of known scenario ideas:
  1) unsupported_sop
  2) unsupported_modality
  3) corrupted_pixel
  4) missing_required_tag
  5) missing_dicom (physically skip writing it)
  6) null_byte_tag
  7) bits_mismatch
  etc.

This gives you a single dataset that exercises many different error
cases in the *prior* studies, while the current study is normal.

Goal:
- Ensure your ingestion pipeline "skips" or "ignores" each faulty prior DICOM,
  while still ingesting the rest of the exam (esp. the current study).
- No indefinite stuck states or total rejections.
"""

import random
from presets.scenario_base import ScenarioBase
from pydicom.uid import generate_uid

class ScenarioLargeScaleShallow(ScenarioBase):
    SCENARIO_NAME = "pr_large_scale_shallow"

    def build_scenario_config(self):
        """
        We will produce:
          - 1 normal current study (4 MG images).
          - ~8 internal priors, each with a single "fault injection".

        If you want more or fewer, adjust below.
        """
        config = super().build_scenario_config()
        # The "current_study" from scenario_base is normal: 4 images, no faults.

        # Let's define 8 distinct "fault injections."
        # Each function will modify the last image in that prior to have some problem.
        # The rest of the images in that prior remain normal.
        fault_functions = [
            self.fault_unsupported_sop,
            self.fault_unsupported_modality,
            self.fault_corrupted_pixel,
            self.fault_missing_required_tag,
            self.fault_missing_dicom_physically,  # physically skip writing one file
            self.fault_null_byte_tag,
            self.fault_bits_mismatch,
            self.fault_for_processing_not_presentation,  # "raw data" example
        ]

        internal_priors = []
        for i, fault_fn in enumerate(fault_functions, start=1):
            prior = self.create_prior_config(is_cancerous=False)
            if prior["images"]:
                # We'll pick the last image to inject the fault
                # The rest remain normal
                bad_img_tags = prior["images"][-1]["tags"]

                # Call the fault injection function
                fault_fn(bad_img_tags, i)

            internal_priors.append(prior)

        config["internal_priors"] = internal_priors
        return config

    # ------------------------------------------------------------
    # Fault injection functions
    # Each function modifies "bad_img_tags" in place.
    # The 'idx' param is just a number we can use if we want to differentiate
    # or do something fancier in each prior.
    # ------------------------------------------------------------

    def fault_unsupported_sop(self, bad_img_tags, idx):
        """
        Convert the last image's SOPClassUID to a known "unsupported" one,
        e.g. '1.2.840.10008.5.1.4.1.1.11.1' (PR)
        Also mark the SeriesDescription so we can see it easily.
        """
        bad_img_tags["SOPClassUID"] = "1.2.840.10008.5.1.4.1.1.11.1"  # PR
        bad_img_tags["Modality"] = "PR"
        bad_img_tags["SeriesDescription"] = f"Fault#{idx}: Unsupported SOP (PR)"

    def fault_unsupported_modality(self, bad_img_tags, idx):
        """
        Keep the standard MG SOPClassUID, but set Modality=OT => mismatch
        """
        bad_img_tags["SOPClassUID"] = "1.2.840.10008.5.1.4.1.1.1.2"  # MG
        bad_img_tags["Modality"] = "OT"
        bad_img_tags["SeriesDescription"] = f"Fault#{idx}: Unsupported Modality=OT"

    def fault_corrupted_pixel(self, bad_img_tags, idx):
        """
        We'll let the Python code physically truncate the pixel data
        by setting 'force_corrupt_pixel': True
        """
        bad_img_tags["force_corrupt_pixel"] = True
        bad_img_tags["SeriesDescription"] = f"Fault#{idx}: Corrupted Pixel"

    def fault_missing_required_tag(self, bad_img_tags, idx):
        """
        We remove e.g. Rows/Columns from the DICOM tags,
        which might cause ingestion to fail or skip.
        """
        if "Rows" in bad_img_tags:
            del bad_img_tags["Rows"]
        if "Columns" in bad_img_tags:
            del bad_img_tags["Columns"]
        bad_img_tags["SeriesDescription"] = f"Fault#{idx}: Missing Rows/Columns"

    def fault_missing_dicom_physically(self, bad_img_tags, idx):
        """
        We'll label the last image so we know which to skip physically
        from writing later in the script. We'll do that by setting
        a special marker "physically_skip": True

        Then in 'generate_dicom_dataset.py' we can detect that tag
        and skip physically writing the file to disk.
        """
        bad_img_tags["SeriesDescription"] = f"Fault#{idx}: Missing Physically"
        bad_img_tags["physically_skip"] = True

    def fault_null_byte_tag(self, bad_img_tags, idx):
        """
        Insert a null char \0 in the SeriesDescription or a custom
        private tag so we see if ingestion crashes on null bytes.
        """
        bad_img_tags["SeriesDescription"] = f"Fault#{idx}: NullByte\0Here"

    def fault_bits_mismatch(self, bad_img_tags, idx):
        """
        E.g. BitsAllocated=16, but BitsStored=15, HighBit=14,
        or something contradictory. We'll set 'force_bits_mismatch=True'
        so that generate_dicom_dataset overwrites them.
        """
        bad_img_tags["force_bits_mismatch"] = True
        bad_img_tags["BitsAllocated"] = 16
        bad_img_tags["BitsStored"] = 15
        bad_img_tags["HighBit"] = 14
        bad_img_tags["SeriesDescription"] = f"Fault#{idx}: BitsMismatch"

    def fault_for_processing_not_presentation(self, bad_img_tags, idx):
        """
        Mark the image as "for processing" instead of "for presentation",
        which some ingestion code might not expect or might skip.
        It's still a valid SOP, but sometimes we only handle
        'FOR PRESENTATION' MG images.
        """
        bad_img_tags["PresentationIntentType"] = "FOR PROCESSING"
        bad_img_tags["SeriesDescription"] = f"Fault#{idx}: MG Raw Data (Processing)"
