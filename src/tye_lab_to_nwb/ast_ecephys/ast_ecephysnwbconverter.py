from typing import Optional

from pynwb import NWBFile

from neuroconv import NWBConverter
from neuroconv.datainterfaces import (
    OpenEphysRecordingInterface,
    PlexonSortingInterface,
    SLEAPInterface,
    VideoInterface,
)
from tye_lab_to_nwb.ast_ecephys.ast_sortinginterface import AstSortingInterface
from tye_lab_to_nwb.general_interfaces import DiscriminationTaskEventsInterface


class AStEcephysNWBConverter(NWBConverter):
    """Primary conversion class for the ASt electrophysiology dataset."""

    data_interface_classes = dict(
        Behavior=SLEAPInterface,
        Video=VideoInterface,
        Events=DiscriminationTaskEventsInterface,
        Recording=OpenEphysRecordingInterface,
        Sorting=PlexonSortingInterface,
        FilteredSorting=AstSortingInterface,
    )

    def get_metadata(self):
        metadata = super().get_metadata()

        recording_interface = self.data_interface_objects["Recording"]
        interface_metadata = recording_interface.get_metadata()
        # Explicitly set session_start_time to OpenEphys recording start time
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
        recording_interface = self.data_interface_objects["Recording"]
        recording_extractor = recording_interface.recording_extractor
        num_channels = recording_extractor.get_num_channels()
        recording_extractor.set_property(
            # SpikeInterface refers to this as 'brain_area', NeuroConv remaps to 'location'
            key="brain_area",
            values=["ASt"] * num_channels,
        )
        super().run_conversion(
            nwbfile_path=nwbfile_path,
            nwbfile=nwbfile,
            metadata=metadata,
            conversion_options=conversion_options,
        )
