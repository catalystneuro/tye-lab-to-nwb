"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter
from neuroconv.datainterfaces import (
    OpenEphysRecordingInterface,
    PlexonSortingInterface,
)

from tye_lab_to_nwb.neurotensin_valence.behavior import NeurotensinDeepLabCutInterface


class NeurotensinValenceNWBConverter(NWBConverter):
    """Primary conversion class for my extracellular electrophysiology dataset."""

    data_interface_classes = dict(
        Recording=OpenEphysRecordingInterface,
        Sorting=PlexonSortingInterface,
        Behavior=NeurotensinDeepLabCutInterface,
    )

    def get_metadata_schema(self) -> dict:
        metadata_schema = super().get_metadata_schema()
        # Manual override to allow additional properties for pose estimation metadata
        metadata_schema["additionalProperties"] = True
        return metadata_schema

    def get_metadata(self):
        """Auto-fill as much of the metadata as possible. Must comply with metadata schema."""
        metadata = super().get_metadata()
        start_times = []
        for interface in self.data_interface_objects.values():
            interface_metadata = interface.get_metadata()
            if "NWBFile" not in interface_metadata:
continue
            if "session_start_time" in interface_metadata["NWBFile"]:
                start_times.append(interface_metadata["NWBFile"]["session_start_time"])

        # Use the earliest session_start_time
        metadata["NWBFile"].update(session_start_time=min(start_times))

        return metadata
