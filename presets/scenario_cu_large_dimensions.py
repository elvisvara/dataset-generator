from presets.scenario_base import ScenarioBase

class ScenarioCurrentLargeDimensions(ScenarioBase):
    SCENARIO_NAME = "cu_large_dimensions"

    def build_scenario_config(self):
        config = super().build_scenario_config()
        images = config["current_study"]["images"]
        if images:
            big_img = images[-1]["tags"]
            big_img["Rows"] = 8000
            big_img["Columns"] = 8000
            big_img["force_large_dims"] = True
            big_img["SeriesDescription"] = "Current w/ Large Dimensions"
        return config