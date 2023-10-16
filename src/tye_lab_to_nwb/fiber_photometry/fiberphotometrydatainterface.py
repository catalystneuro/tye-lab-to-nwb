"""Primary class for converting fiber photometry data."""
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.tools.nwb_helpers import make_or_load_nwbfile
from neuroconv.utils import FilePathType, load_dict_from_file, OptionalFilePathType
from pynwb import NWBFile

from tye_lab_to_nwb.fiber_photometry.tools import (
    add_photometry,
    add_events_from_photometry,
)


class FiberPhotometryInterface(BaseDataInterface):
    """Primary interface for converting fiber photometry data in custom CSV format."""

    def __init__(
        self,
        file_path: FilePathType,
        verbose: bool = True,
    ):
        """
        Interface for writing fiber photometry data from CSV to NWB.

        Parameters
        ----------
        file_path : FilePathType
            path to the CSV file that contains the intensity values.
        verbose: bool, default: True
            controls verbosity.
        """
        self.verbose = verbose
        super().__init__(file_path=file_path)
        self.photometry_dataframe = self._read_file()

    def get_metadata(self) -> dict:
        metadata = super().get_metadata()

        photometry_metadata = load_dict_from_file(
            file_path=Path(__file__).parent / "metadata" / "fiber_photometry_metadata.yaml"
        )
        metadata.update(photometry_metadata)

        return metadata

    def _read_file(self) -> pd.DataFrame:
        return pd.read_csv(self.source_data["file_path"], header=0)

    def get_original_timestamps(self, column: str = "Timestamp") -> np.ndarray:
        """
        Retrieve the original unaltered timestamps for the data in this interface.

        This function should retrieve the data on-demand by re-initializing the IO.

        Returns
        -------
        timestamps: numpy.ndarray
            The timestamps for the data stream.
        """
        return self._read_file()[column].values

    def get_timestamps(self, column: str = "Timestamp") -> np.ndarray:
        """
        Retrieve the timestamps for the data in this interface.

        Returns
        -------
        timestamps: numpy.ndarray
            The timestamps for the data stream.
        """
        return self.photometry_dataframe[column].values

    def align_timestamps(self, aligned_timestamps: np.ndarray, column: str = "Timestamp"):
        """
        Replace all timestamps for this interface with those aligned to the common session start time.

        Must be in units seconds relative to the common 'session_start_time'.

        Parameters
        ----------
        aligned_timestamps : numpy.ndarray
            The synchronized timestamps for data in this interface.
        """
        self.photometry_dataframe[column] = aligned_timestamps

    def add_to_nwbfile(
        self,
        nwbfile: NWBFile,
        metadata: Optional[dict] = None,
        stub_test: bool = False,
        overwrite: bool = False,
    ):
        add_events_from_photometry(photometry_dataframe=self.photometry_dataframe, nwbfile=nwbfile, metadata=metadata)
        add_photometry(photometry_dataframe=self.photometry_dataframe, nwbfile=nwbfile, metadata=metadata)
