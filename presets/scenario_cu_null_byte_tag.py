from presets.scenario_base import ScenarioBase

class ScenarioCurrentNullByteTag(ScenarioBase):
    SCENARIO_NAME = "cu_null_byte_tag"

    def build_scenario_config(self):
        config = super().build_scenario_config()
        images = config["current_study"]["images"]
        if images:
            bad_img = images[-1]["tags"]
            bad_img["SeriesDescription"] = "CurrentHasNullByte\x00Here"
        return config