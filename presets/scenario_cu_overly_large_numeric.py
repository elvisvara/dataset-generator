from presets.scenario_base import ScenarioBase

class ScenarioCurrentOverlyLargeNumeric(ScenarioBase):
    SCENARIO_NAME = "cu_overly_large_numeric"

    def build_scenario_config(self):
        config = super().build_scenario_config()
        images = config["current_study"]["images"]
        if images:
            # Example => WindowCenter=999999999..., WindowWidth=888888888...
            bad_img = images[-1]["tags"]
            bad_img["WindowCenter"] = "9999999999999999999999999999"
            bad_img["WindowWidth"]  = "8888888888888888888888888888"
            bad_img["SeriesDescription"] = "Current Overly Large Numeric"
        return config