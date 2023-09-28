import numpy as np
from pymatreader import read_mat
from roiextractors import SegmentationExtractor
from roiextractors.extraction_tools import PathType
from scipy.sparse import csc_matrix


class CnmfeMatlabSegmentationExtractor(SegmentationExtractor):
    """A SegmentationExtractor for matlab CNMF-E segmentation output."""

    extractor_name = "CnmfeMatlabSegmentation"
    mode = "file"

    def __init__(self, file_path: PathType):
        """Initialize a CnmfeMatlabSegmentationExtractor instance.

        Parameters
        ----------
        file_path: str
            The location of the folder containing  CNMF-E .mat output file.
        """
        super().__init__()
        self.file_path = file_path

        self._dataset_file = self._load_mat_file()

        self._sampling_frequency = float(self._dataset_file["Fs"])
        # image axis order should be height and width
        self._image_size = (self._dataset_file["options"]["d1"], self._dataset_file["options"]["d2"])
        self._num_frames = self._dataset_file["P"]["numFrames"]
        self._roi_response_raw = self._dataset_file["C"].T
        self._roi_response_deconvolved = self._transform_deconvolved_traces()
        self._image_correlation = self._dataset_file["Cn"]
        self._image_masks = self._transform_image_masks()

    def _load_mat_file(self):
        return read_mat(self.file_path)

    def get_image_size(self):
        return self._image_size

    def get_num_frames(self):
        return self._num_frames

    def get_accepted_list(self):
        return list(range(self.get_num_rois()))

    def get_rejected_list(self):
        return []

    def _transform_deconvolved_traces(self):
        deconvolved_traces = self._dataset_file["S"]

        if isinstance(deconvolved_traces, csc_matrix):
            deconvolved_traces = deconvolved_traces.toarray()
        if not np.any(deconvolved_traces):
            return None

        return deconvolved_traces.T

    def _transform_image_masks(self):
        image_masks = self._dataset_file["A"].toarray()
        num_rois = self.get_num_rois()
        return image_masks.reshape((*self._image_size, num_rois))
