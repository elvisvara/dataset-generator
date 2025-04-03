from presets.scenario_base import ScenarioBase

class ScenarioCurrentCorruptedPixel(ScenarioBase):
    SCENARIO_NAME = "cu_corrupted_pixel"

    def build_scenario_config(self):
        config = super().build_scenario_config()
        
        images = config["current_study"]["images"]
        if images:
            images[-1]["tags"]["force_corrupt_pixel"] = True
            images[-1]["tags"]["SeriesDescription"] = "Current Study w/ Corrupted Pixel"

        return config