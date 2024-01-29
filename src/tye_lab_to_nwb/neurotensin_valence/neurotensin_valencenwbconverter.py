"""Primary NWBConverter class for this dataset."""

from typing import Optional

from pynwb import NWBFile
from neuroconv import NWBConverter
from neuroconv.datainterfaces import (
    OpenEphysRecordingInterface,
    PlexonSortingInterface,
    VideoInterface,
)
from tye_lab_to_nwb.general_interfaces import DiscriminationTaskEventsInterface
from tye_lab_to_nwb.neurotensin_valence.behavior import NeurotensinDeepLabCutInterface
from tye_lab_to_nwb.neurotensin_valence.images import NeurotensinConfocalImagesInterface


class NeurotensinValenceNWBConverter(NWBConverter):
    """Primary conversion class for my extracellular electrophysiology dataset."""

    data_interface_classes = dict(
        Recording=OpenEphysRecordingInterface,
        Sorting=PlexonSortingInterface,
        PoseEstimation=NeurotensinDeepLabCutInterface,
        Events=DiscriminationTaskEventsInterface,
        Images=NeurotensinConfocalImagesInterface,
        OriginalVideo=VideoInterface,
    )

    def get_metadata_schema(self) -> dict:
        metadata_schema = super().get_metadata_schema()
        # Manual override to allow additional properties for pose estimation metadata
        metadata_schema["additionalProperties"] = True
        return metadata_schema

    def get_metadata(self):
        metadata = super().get_metadata()
        # Explicitly use the recording interface session_start_time
        if "Recording" in self.data_interface_objects:
            recording_interface = self.data_interface_objects["Recording"]
            interface_metadata = recording_interface.get_metadata()
            metadata["NWBFile"].update(session_start_time=interface_metadata["NWBFile"]["session_start_time"])

        return metadata

    def run_conversion(
        self,
        nwbfile_path: Optional[str] = None,
        nwbfile: Optional[NWBFile] = None,
        metadata: Optional[dict] = None,
        overwrite: bool = False,
        conversion_options: Optional[dict] = None,
    ):
        if "Recording" in self.data_interface_objects:
            recording_interface = self.data_interface_objects["Recording"]
            # manually override t_start
            recording_interface.recording_extractor._recording_segments[0].t_start = None
        super().run_conversion(
            nwbfile_path=nwbfile_path,
            nwbfile=nwbfile,
            metadata=metadata,
            conversion_options=conversion_options,
        )
