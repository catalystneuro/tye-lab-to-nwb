"""Primary NWBConverter class for this dataset."""
from typing import Optional

from pynwb import NWBFile
from neuroconv import NWBConverter
from neuroconv.datainterfaces import (
    OpenEphysRecordingInterface,
    PlexonSortingInterface,
)

from tye_lab_to_nwb.neurotensin_valence.behavior import (
    NeurotensinDeepLabCutInterface,
    NeurotensinEventsInterface,
)


class NeurotensinValenceNWBConverter(NWBConverter):
    """Primary conversion class for my extracellular electrophysiology dataset."""

    data_interface_classes = dict(
        PoseEstimation=NeurotensinDeepLabCutInterface,
        Events=NeurotensinEventsInterface,
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

    def run_conversion(
        self,
        nwbfile_path: Optional[str] = None,
        nwbfile: Optional[NWBFile] = None,
        metadata: Optional[dict] = None,
        overwrite: bool = False,
        conversion_options: Optional[dict] = None,
    ):
        recording_interface = self.data_interface_objects["Recording"]
        # manually override t_start
        recording_interface.recording_extractor._recording_segments[0].t_start = None
        super().run_conversion(
            nwbfile_path=nwbfile_path,
            nwbfile=nwbfile,
            metadata=metadata,
            conversion_options=conversion_options,
        )
