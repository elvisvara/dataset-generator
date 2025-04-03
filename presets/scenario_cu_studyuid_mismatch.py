from presets.scenario_base import ScenarioBase
from pydicom.uid import generate_uid

class ScenarioCurrentStudyUidMismatch(ScenarioBase):
    SCENARIO_NAME = "cu_studyuid_mismatch"

    def build_scenario_config(self):
        config = super().build_scenario_config()
        images = config["current_study"]["images"]
        if images:

            mismatch_uid = generate_uid()
            images[-1]["tags"]["StudyInstanceUID"] = mismatch_uid
            images[-1]["tags"]["SeriesDescription"] = "Current Study w/ Mismatching Study UID"
        return config