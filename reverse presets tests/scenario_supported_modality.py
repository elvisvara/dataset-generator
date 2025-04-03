from presets.scenario_base import ScenarioBase

class ScenarioSupportedModality(ScenarioBase):
    SCENARIO_NAME = "supported_modality"

    def build_scenario_config(self):
        config = super().build_scenario_config()
        normal_prior = self.create_prior_config(is_cancerous=False)

        if normal_prior["images"]:
            good_img_tags = normal_prior["images"][-1]["tags"]
            good_img_tags["SOPClassUID"] = "1.2.840.10008.5.1.4.1.1.1.2"
            good_img_tags["Modality"] = "MG"
            good_img_tags["SeriesDescription"] = "Fully Supported Modality=MG"
            # Add windowing so the pipeline sees a valid VOI transform
            good_img_tags["WindowCenter"] = "2048"
            good_img_tags["WindowWidth"]  = "4096"
            good_img_tags["VOILUTFunction"] = "LINEAR"
            good_img_tags["RescaleIntercept"] = "0"
            good_img_tags["RescaleSlope"] = "1"

        config["internal_priors"].append(normal_prior)
        return config
