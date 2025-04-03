from presets.scenario_base import ScenarioBase

class ScenarioCurrentMissingRequiredTag(ScenarioBase):
    SCENARIO_NAME = "cu_missing_required_tag"

    def build_scenario_config(self):
        config = super().build_scenario_config()
        images = config["current_study"]["images"]
        if images:
            bad_img = images[-1]["tags"]
            if "Rows" in bad_img:
                del bad_img["Rows"]
            if "Columns" in bad_img:
                del bad_img["Columns"]
            bad_img["SeriesDescription"] = "Current Study Missing Rows/Cols"
        return config