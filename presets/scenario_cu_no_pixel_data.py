from presets.scenario_base import ScenarioBase

class ScenarioCurrentNoPixelData(ScenarioBase):
    SCENARIO_NAME = "cu_no_pixel_data"

    def build_scenario_config(self):
        config = super().build_scenario_config()
        images = config["current_study"]["images"]
        if images:
            images[-1]["tags"]["no_pixel_data"] = True
            images[-1]["tags"]["SeriesDescription"] = "Current Study w/ No PixelData"
        return config