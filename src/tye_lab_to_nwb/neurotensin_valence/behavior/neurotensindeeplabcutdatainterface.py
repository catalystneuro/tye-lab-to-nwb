"""Primary class for converting experiment-specific behavior."""
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from ndx_pose import PoseEstimationSeries, PoseEstimation
from neuroconv.tools.nwb_helpers import make_or_load_nwbfile, get_module
from neuroconv.utils import (
    OptionalFilePathType,
    FilePathType,
    load_dict_from_file,
    ArrayType,
)
from pynwb.file import NWBFile

from neuroconv.basedatainterface import BaseDataInterface


class NeurotensinDeepLabCutInterface(BaseDataInterface):
    """Behavior interface for converting DeepLabCut data in legacy format for the Neurotensin experiment."""

    def __init__(
        self,
        file_path: FilePathType,
        config_file_path: FilePathType,
        verbose: bool = True,
    ):
        """
        Interface for writing pose estimation data from CSV and pickle to NWB.

        Parameters
        ----------
        file_path : FilePathType
            path to the CSV file output by DeepLabCut GUI.
        config_file_path : FilePathType
            path to .pickle config file output by DeepLabCut GUI.
        verbose: bool, default: True
            controls verbosity.
        """
        self.verbose = verbose
        super().__init__(file_path=file_path, config_file_path=config_file_path)

    def get_metadata(self) -> dict:
        metadata = super().get_metadata()

        pose_estimation_metadata = load_dict_from_file(
            file_path=Path(__file__).parent.parent / "metadata" / "pose_estimation_metadata.yaml"
        )
        metadata.update(pose_estimation_metadata)

        return metadata

    def _load_source_data(self):
        pose_estimation_data = pd.read_csv(self.source_data["file_path"], header=[0, 1, 2])
        # The first level contains the scorer, can be dropped from header (can be found also in conf)
        pose_estimation_data.columns = pose_estimation_data.columns.droplevel(0)
        pose_estimation_config = pd.read_pickle(self.source_data["config_file_path"])
        return pose_estimation_data, pose_estimation_config

    def run_conversion(
        self,
        nwbfile_path: OptionalFilePathType = None,
        nwbfile: Optional[NWBFile] = None,
        metadata: Optional[dict] = None,
        original_video_file_path: OptionalFilePathType = None,
        labeled_video_file_path: OptionalFilePathType = None,
        edges: Optional[ArrayType] = None,
        column_mappings: Optional[dict] = None,
        overwrite: bool = False,
    ):
        with make_or_load_nwbfile(
            nwbfile_path=nwbfile_path, nwbfile=nwbfile, metadata=metadata, overwrite=overwrite, verbose=self.verbose
        ) as nwbfile_out:
            pose_estimation_data, pose_estimation_config = self._load_source_data()

            pose_estimation_metadata = metadata["PoseEstimation"]

            pose_estimation_series = []
            for column_name in pose_estimation_metadata:
                pose_estimation_series_data = pose_estimation_data[column_name]

                pose_estimation_series.append(
                    PoseEstimationSeries(
                        name=pose_estimation_metadata[column_name]["name"],
                        description=pose_estimation_metadata[column_name]["description"],
                        data=pose_estimation_series_data[["x", "y"]].values,
                        unit="px",
                        reference_frame="(0,0,0) corresponds to bottom left corner of the cage.",
                        rate=pose_estimation_config["data"]["fps"],
                        starting_time=0.0,  # TODO
                        confidence=pose_estimation_series_data["likelihood"].values,
                        confidence_definition=pose_estimation_metadata[column_name]["confidence_definition"],
                    )
                )

            # The parameters for the pose estimation container
            pose_estimation_kwargs = dict(
                pose_estimation_series=pose_estimation_series,
                # frame_dimensions are in height x width, but for NWB it should be width x height
                dimensions=np.array([pose_estimation_config["data"]["frame_dimensions"][::-1]], dtype=np.uint16),
                scorer=pose_estimation_config["data"]["Scorer"],
                source_software="DeepLabCut",
                nodes=[pose_estimation_metadata[column_name]["name"] for column_name in pose_estimation_metadata],
                edges=np.asarray(edges, dtype=np.uint8),
            )

            if original_video_file_path is not None:
                pose_estimation_kwargs.update(original_videos=[original_video_file_path])
            if labeled_video_file_path is not None:
                pose_estimation_kwargs.update(labeled_videos=[labeled_video_file_path])

            # Create the container for pose estimation
            pose_estimation = PoseEstimation(**pose_estimation_kwargs)

            behavior = get_module(nwbfile_out, "behavior", "Processed behavior data.")
            behavior.add(pose_estimation)
