from typing import Optional

from neuroconv.converters import MiniscopeConverter

from neuroconv import NWBConverter
from pynwb import NWBFile


from tye_lab_to_nwb.ast_ophys.interfaces import (
    CnmfeMatlabSegmentationSegmentationInterface,
    MotionCorrectedMiniscopeImagingInterface,
    ProcessedMiniscopeImagingInterface,
)


class AStOphysNWBConverter(NWBConverter):
    """Primary conversion class for the ASt optical imaging dataset."""

    data_interface_classes = dict(
        RawImaging=MiniscopeConverter,
        ProcessedImaging=ProcessedMiniscopeImagingInterface,
        MotionCorrectedImaging=MotionCorrectedMiniscopeImagingInterface,
        Segmentation=CnmfeMatlabSegmentationSegmentationInterface,
    )

    def run_conversion(
        self,
        nwbfile_path: Optional[str] = None,
        nwbfile: Optional[NWBFile] = None,
        metadata: Optional[dict] = None,
        overwrite: bool = False,
        conversion_options: Optional[dict] = None,
    ):
        # TODO: remove this part if
        # if "RawImaging" in self.data_interface_objects:
        #     miniscope_converter = self.data_interface_objects["RawImaging"]
        #     imaging_interface = miniscope_converter.data_interface_objects["MiniscopeImaging"]

        if "MotionCorrectedImaging" in self.data_interface_objects:
            motion_corrected_imaging_interface = self.data_interface_objects["MotionCorrectedImaging"]
            # TODO: clarify rate (segmentation data and raw imaging is fs 15, but opencv frame rate for processed is 30.0)
            motion_corrected_imaging_interface.imaging_extractor._sampling_frequency = 30.0

        if "ProcessedImaging" in self.data_interface_objects:
            processed_imaging_interface = self.data_interface_objects["ProcessedImaging"]
            # TODO: clarify rate
            processed_imaging_interface.imaging_extractor._sampling_frequency = 30.0

        # Update imaging plane location
        imaging_plane_metadata = metadata["Ophys"]["ImagingPlane"][0]
        imaging_plane_metadata.update(location="ASt")

        super().run_conversion(
            nwbfile_path=nwbfile_path,
            nwbfile=nwbfile,
            metadata=metadata,
            conversion_options=conversion_options,
        )
