from presets.scenario_base import ScenarioBase

class ScenarioCurrentUnsupportedModality(ScenarioBase):
    SCENARIO_NAME = "cu_unsupported_modality"

    def build_scenario_config(self):
        config = super().build_scenario_config()
        
        # we do the last image => "OT" modality, but still MG SOP
        images = config["current_study"]["images"]
        if images:
            bad_img = images[-1]["tags"]
            bad_img["Modality"] = "OT" 
            # Keep MG SOP Class (1.2.840.10008.5.1.4.1.1.1.2)
            bad_img["SeriesDescription"] = "Current Study w/ Unsupported Modality=OT"
        
        return config