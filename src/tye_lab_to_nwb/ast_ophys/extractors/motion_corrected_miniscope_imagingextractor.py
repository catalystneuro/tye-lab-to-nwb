from typing import Tuple, List, Optional

import numpy as np
from lazy_ops import DatasetView
from roiextractors import ImagingExtractor

from neuroconv.utils import FilePathType


class MotionCorrectedMiniscopeImagingExtractor(ImagingExtractor):
    extractor_name = "MotionCorrectedMiniscopeImaging"

    def __init__(self, file_path: FilePathType):
        """
        The ImagingExtractor for loading the motion corrected Miniscope video which is stored in a MATLAB (.mat) file.

        Parameters
        ----------
        file_path: PathType
           The path that points to the motion corrected Miniscope video saved as a Matlab file.
        """
        import h5py

        super().__init__(file_path=file_path)

        file = h5py.File(file_path, mode="r")
        expected_struct_name = "Mr_8bit"
        assert expected_struct_name in file.keys(), f"'{expected_struct_name}' is not in {file_path}."
        self._video = DatasetView(file[expected_struct_name])
        self._num_frames, self._width, self._height = self._video.shape
        self._sampling_frequency = None

    def get_image_size(self) -> Tuple[int, int]:
        return self._height, self._width

    def get_num_frames(self) -> int:
        return self._num_frames

    def get_sampling_frequency(self) -> float:
        return self._sampling_frequency

    def get_channel_names(self) -> List[str]:
        return ["OpticalChannel"]

    def get_num_channels(self) -> int:
        return 1

    def get_video(
        self, start_frame: Optional[int] = None, end_frame: Optional[int] = None, channel: int = 0
    ) -> np.ndarray:
        return self._video.lazy_slice[start_frame:end_frame, ...].lazy_transpose(axis_order=(0, 2, 1)).dsetread()
