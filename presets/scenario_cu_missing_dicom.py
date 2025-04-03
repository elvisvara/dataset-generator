from presets.scenario_base import ScenarioBase

class ScenarioCurrentMissingDicom(ScenarioBase):
    SCENARIO_NAME = "cu_missing_dicom"

    def build_scenario_config(self):
        config = super().build_scenario_config()
        images = config["current_study"]["images"]
        if images:
            images[-1]["tags"]["skip_writing"] = True
            images[-1]["tags"]["SeriesDescription"] = "Current Missing DICOM (Physically Not Written)"
        return config