from typing import Optional

from pynwb import NWBFile

from neuroconv import NWBConverter
from neuroconv.datainterfaces import (
    SpikeGLXRecordingInterface,
    PhySortingInterface,
)


class AStNeuroPixelsNNWBConverter(NWBConverter):
    """Primary conversion class for the ASt Neuropixels dataset."""

    data_interface_classes = dict(
        RecordingAP=SpikeGLXRecordingInterface,
        RecordingLF=SpikeGLXRecordingInterface,
        Sorting=PhySortingInterface,
    )

    def run_conversion(
        self,
        nwbfile_path: Optional[str] = None,
        nwbfile: Optional[NWBFile] = None,
        metadata: Optional[dict] = None,
        overwrite: bool = False,
        conversion_options: Optional[dict] = None,
    ):
        recording_interfaces = ["RecordingAP", "RecordingLF"]
        for recording_interface_name in recording_interfaces:
            recording_interface = self.data_interface_objects[recording_interface_name]
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
