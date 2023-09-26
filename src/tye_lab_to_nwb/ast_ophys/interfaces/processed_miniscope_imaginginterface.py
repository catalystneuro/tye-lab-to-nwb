from pathlib import Path
from typing import Optional

import numpy as np
from neuroconv.datainterfaces.ophys.baseimagingextractorinterface import BaseImagingExtractorInterface
from pynwb import NWBFile
from roiextractors.extractors.miniscopeimagingextractor.miniscopeimagingextractor import _MiniscopeImagingExtractor
from neuroconv.utils import FilePathType, dict_deep_update
from neuroconv.tools.roiextractors import get_nwb_imaging_metadata

from tye_lab_to_nwb.ast_ophys.tools import load_timestamps_from_mat, add_processed_one_photon_series


class ProcessedMiniscopeImagingInterface(BaseImagingExtractorInterface):
    """Data Interface for ProcessedMiniscopeImagingExtractor."""

    Extractor = _MiniscopeImagingExtractor

    def __init__(
        self,
        file_path: FilePathType,
        timestamps_file_path: FilePathType,
    ):
        """
        Initialize reading the processed Miniscope (first 3 frames is deleted for each trial) imaging data.

        Parameters
        ----------
        file_path : FilePathType
            The path that points to the processed miniscope video file.
        """

        self.timestamps_file_path = Path(timestamps_file_path)
        self._timestamps_arr = load_timestamps_from_mat(self.timestamps_file_path)

        super().__init__(file_path=file_path)

    def get_original_timestamps(self) -> np.ndarray:
        frames = load_timestamps_from_mat(self.timestamps_file_path)
        # also shift to start from zero beacuse of matlab start from 1.0
        frames = frames[~np.isnan(frames[:, 5]), 4] - 1
        timestamps = frames / self.imaging_extractor.get_sampling_frequency()
        return timestamps

    def get_metadata(self) -> dict:
        metadata = super().get_metadata()

        default_metadata = get_nwb_imaging_metadata(self.imaging_extractor, photon_series_type="OnePhotonSeries")
        metadata = dict_deep_update(metadata, default_metadata)
        metadata["Ophys"].pop("TwoPhotonSeries", None)

        device_metadata = metadata["Ophys"]["Device"][0]
        device_metadata.update(name="Miniscope")
        imaging_plane_metadata = metadata["Ophys"]["ImagingPlane"][0]
        imaging_plane_name = imaging_plane_metadata["name"]
        imaging_plane_metadata.update(device="Miniscope")
        one_photon_series_metadata = metadata["Ophys"]["OnePhotonSeries"][0]
        one_photon_series_metadata.update(
            name="OnePhotonSeriesProcessed",
            imaging_plane=imaging_plane_name,
            description="The processed imaging data from one-photon excitation microscopy."
            "The first three frame for each trial was deleted from the original video snippets.",
        )
        return metadata

    def get_metadata_schema(self) -> dict:
        metadata_schema = super().get_metadata_schema(photon_series_type="OnePhotonSeries")
        metadata_schema["properties"]["Ophys"]["properties"]["definitions"]["Device"]["additionalProperties"] = True
        return metadata_schema

    def add_to_nwbfile(
        self,
        nwbfile: NWBFile,
        metadata: Optional[dict] = None,
        stub_test: bool = False,
        stub_frames: int = 100,
    ):
        imaging_extractor = self.imaging_extractor
        timestamps = self.get_original_timestamps()
        if stub_test:
            stub_frames = min([stub_frames, self.imaging_extractor.get_num_frames()])
            imaging_extractor = self.imaging_extractor.frame_slice(start_frame=0, end_frame=stub_frames)
            timestamps = timestamps[:stub_frames]

        add_processed_one_photon_series(
            nwbfile=nwbfile,
            metadata=metadata,
            photon_series_index=2,
            imaging=imaging_extractor,
            timestamps=timestamps,
        )
