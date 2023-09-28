from pathlib import Path
from typing import Optional, List

import numpy as np
import pandas as pd
from neuroconv.datainterfaces.ophys.baseimagingextractorinterface import BaseImagingExtractorInterface
from neuroconv.tools.roiextractors import get_nwb_imaging_metadata
from neuroconv.utils import ArrayType, FilePathType, dict_deep_update
from pynwb import NWBFile

from tye_lab_to_nwb.ast_ophys.extractors.motion_corrected_miniscope_imagingextractor import (
    MotionCorrectedMiniscopeImagingExtractor,
)
from tye_lab_to_nwb.ast_ophys.tools import load_timestamps_from_mat, add_processed_one_photon_series


class MotionCorrectedMiniscopeImagingInterface(BaseImagingExtractorInterface):
    """Data Interface for MotionCorrectedMiniscopeImagingExtractor."""

    Extractor = MotionCorrectedMiniscopeImagingExtractor

    def __init__(
        self,
        file_path: FilePathType,
        timestamps_file_path: FilePathType,
    ):
        """
        Initialize reading the motion corrected Miniscope imaging data.

        Parameters
        ----------
        file_path : FilePathType
            The path that points to the motion corrected miniscope mat file.
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
            name="OnePhotonSeriesMotionCorrected",
            imaging_plane=imaging_plane_name,
            description="The motion corrected imaging data from one-photon excitation microscopy.",
            binning=4,
        )

        return metadata

    def get_metadata_schema(self) -> dict:
        metadata_schema = super().get_metadata_schema(photon_series_type="OnePhotonSeries")
        metadata_schema["properties"]["Ophys"]["properties"]["definitions"]["Device"]["additionalProperties"] = True
        return metadata_schema

    def add_trials(
        self,
        nwbfile: NWBFile,
        reward_trials_indices: Optional[List[int]] = None,
    ):
        trial_frame_times = pd.DataFrame(self._timestamps_arr)
        # the first three frame indices for each trial are NaNs
        trial_frame_times = trial_frame_times.dropna()

        # get the trial start and end frames (column 2 corresponds to trial index starting from 1, column 4 corresponds to frame indices starting from 1
        trial_frame_indices = trial_frame_times.groupby(2).aggregate({4: ["min", "max"]}).values
        # shift frame indices to zero because matlab starts from 1
        trial_frame_indices -= 1
        # frame to time
        trial_frame_times_values = trial_frame_indices / self.imaging_extractor.get_sampling_frequency()

        for trial_frame_times_value in trial_frame_times_values:
            nwbfile.add_trial(
                start_time=trial_frame_times_value[0],
                stop_time=trial_frame_times_value[1],
            )

        num_trials = trial_frame_times_values.shape[0]
        if reward_trials_indices is not None:
            trial_types = [
                "Reward" if (trial_ind + 1) in reward_trials_indices else "Shock" for trial_ind in range(num_trials)
            ]
            nwbfile.add_trial_column(
                name="trial_type",
                description="Defines whether the trial was reward or shock.",
                data=trial_types,
            )

        return nwbfile

    def add_to_nwbfile(
        self,
        nwbfile: NWBFile,
        metadata: Optional[dict] = None,
        stub_test: bool = False,
        stub_frames: int = 100,
        photon_series_index: int = 0,
        reward_trials_indices: Optional[ArrayType] = None,
    ):
        imaging_extractor = self.imaging_extractor
        timestamps = self.get_original_timestamps()
        if stub_test:
            stub_frames = min([stub_frames, self.imaging_extractor.get_num_frames()])
            imaging_extractor = self.imaging_extractor.frame_slice(start_frame=0, end_frame=stub_frames)
            timestamps = timestamps[:stub_frames]

        self.add_trials(nwbfile=nwbfile, reward_trials_indices=reward_trials_indices)

        add_processed_one_photon_series(
            nwbfile=nwbfile,
            metadata=metadata,
            imaging=imaging_extractor,
            timestamps=timestamps,
            photon_series_index=photon_series_index,
        )
