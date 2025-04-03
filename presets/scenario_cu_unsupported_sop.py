from presets.scenario_base import ScenarioBase

class ScenarioCurrentUnsupportedSOP(ScenarioBase):
    SCENARIO_NAME = "cu_unsupported_sop"

    def build_scenario_config(self):
        config = super().build_scenario_config()
        images = config["current_study"]["images"]
        if images:
            bad_img = images[-1]["tags"]
            # we use PR SOP (Presentation State) => 1.2.840.10008.5.1.4.1.1.11.1
            bad_img["SOPClassUID"] = "1.2.840.10008.5.1.4.1.1.11.1"
            bad_img["Modality"]    = "PR"
            bad_img["SeriesDescription"] = "Current w/ Unsupported SOP=PR"
        return config