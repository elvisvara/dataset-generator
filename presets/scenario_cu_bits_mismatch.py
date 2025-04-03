from presets.scenario_base import ScenarioBase

class ScenarioCurrentBitsMismatch(ScenarioBase):
    SCENARIO_NAME = "cu_bits_mismatch"

    def build_scenario_config(self):
        config = super().build_scenario_config()
        images = config["current_study"]["images"]
        if images:
            images[-1]["tags"]["force_bits_mismatch"] = True
            images[-1]["tags"]["BitsAllocated"] = 16
            images[-1]["tags"]["BitsStored"]    = 14
            images[-1]["tags"]["HighBit"]       = 3
            images[-1]["tags"]["SeriesDescription"] = "Current Study w/ Bits Mismatch"
        return config