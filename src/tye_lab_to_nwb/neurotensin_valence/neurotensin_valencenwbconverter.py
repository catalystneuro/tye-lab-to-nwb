"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter

from tye_lab_to_nwb.neurotensin_valence.behavior import NeurotensinDeepLabCutInterface


class NeurotensinValenceNWBConverter(NWBConverter):
    """Primary conversion class for my extracellular electrophysiology dataset."""

    data_interface_classes = dict(
        Behavior=NeurotensinDeepLabCutInterface,
    )

    def get_metadata_schema(self) -> dict:
        metadata_schema = super().get_metadata_schema()
        # Manual override to allow additional properties for pose estimation metadata
        metadata_schema["additionalProperties"] = True
        return metadata_schema
