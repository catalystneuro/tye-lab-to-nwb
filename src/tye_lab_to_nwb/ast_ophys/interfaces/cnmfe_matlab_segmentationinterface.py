from neuroconv.datainterfaces.ophys.basesegmentationextractorinterface import BaseSegmentationExtractorInterface
from neuroconv.utils import FilePathType
from tye_lab_to_nwb.ast_ophys.extractors.cnmfe_matlab_segmentationextractor import CnmfeMatlabSegmentationExtractor


class CnmfeMatlabSegmentationSegmentationInterface(BaseSegmentationExtractorInterface):
    """Data interface for constrained non-negative matrix factorization (CNMFE) segmentation extractor."""

    Extractor = CnmfeMatlabSegmentationExtractor

    def __init__(self, file_path: FilePathType, verbose: bool = True):
        super().__init__(file_path=file_path)
        self.verbose = verbose

    def get_metadata(self) -> dict:
        metadata = super().get_metadata()

        # Use the same device as for imaging
        device_metadata = metadata["Ophys"]["Device"][0]
        imaging_plane_metadata = metadata["Ophys"]["ImagingPlane"][0]
        device_metadata.update(name="Miniscope")
        imaging_plane_metadata.update(device="Miniscope")

        return metadata
