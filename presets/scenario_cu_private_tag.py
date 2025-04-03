from presets.scenario_base import ScenarioBase

class ScenarioCurrentPrivateTag(ScenarioBase):
    SCENARIO_NAME = "cu_private_tag"

    def build_scenario_config(self):
        config = super().build_scenario_config()
        images = config["current_study"]["images"]
        if images:
            bad_img = images[-1]["tags"]
            bad_img["Private_9999_0010"] = "MyPrivateValue"
            bad_img["SeriesDescription"] = "Current Study w/ Private Tag"
        return config