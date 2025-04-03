# /Users/elvis/Desktop/SUH/presets/scenario_bits_consistent.py
"""
ScenarioBitsConsistent:
- 1 current study (normal),
- 1 prior with 4 images. The last image forcibly sets BitsAllocated=12,
  BitsStored=12, HighBit=11, which is a valid combination (no mismatch).

This ensures ingestion should succeed if bits mismatch was the only reason
the 'bits_mismatch' scenario failed.
"""

from presets.scenario_base import ScenarioBase

class ScenarioBitsConsistent(ScenarioBase):
    SCENARIO_NAME = "bits_consistent"

    def build_scenario_config(self):
        config = super().build_scenario_config()

        # Create one non-cancerous internal prior
        prior = self.create_prior_config(is_cancerous=False)

        if prior["images"]:
            # The last image => intentionally set consistent bits
            last_img = prior["images"][-1]["tags"]
            last_img["BitsAllocated"] = 12
            last_img["BitsStored"]    = 12
            last_img["HighBit"]       = 11
            last_img["SeriesDescription"] = "Bits Consistent (Allocated=12, Stored=12, HighBit=11)"
            # Note: we do NOT set force_bits_mismatch = True
            # so it won't override anything, and the pipeline sees valid bits

        config["internal_priors"].append(prior)
        return config
