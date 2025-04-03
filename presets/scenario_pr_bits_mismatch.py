from presets.scenario_base import ScenarioBase

class ScenarioBitsMismatch(ScenarioBase):
    SCENARIO_NAME = "pr_bits_mismatch"

    def build_scenario_config(self):
        config = super().build_scenario_config()

        prior = self.create_prior_config(is_cancerous=False)

        if prior["images"]:
            # The last image has intentionally invalid bits
            bad_img = prior["images"][-1]["tags"]
            bad_img["BitsAllocated"] = 12
            bad_img["BitsStored"] = 15
            bad_img["HighBit"] = 14
            bad_img["SeriesDescription"] = "Bits Mismatch (Allocated=12, Stored=15, HighBit=14)"
            # Add a special flag so create_mg_dicom() won't clamp
            bad_img["force_bits_mismatch"] = True

        config["internal_priors"].append(prior)
        return config
