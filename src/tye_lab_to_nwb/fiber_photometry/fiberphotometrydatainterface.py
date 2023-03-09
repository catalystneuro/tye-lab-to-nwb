"""Primary class for converting fiber photometry data."""
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.tools.nwb_helpers import make_or_load_nwbfile
from neuroconv.utils import FilePathType, load_dict_from_file, OptionalFilePathType
from pynwb import NWBFile

from tye_lab_to_nwb.fiber_photometry.tools.photometry import add_photometry


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

    def get_metadata(self) -> dict:
        metadata = super().get_metadata()

        photometry_metadata = load_dict_from_file(
            file_path=Path(__file__).parent / "metadata" / "fiber_photometry_metadata.yaml"
        )
        metadata.update(photometry_metadata)

        return metadata

    def _load_source_data(self) -> pd.DataFrame:
        return pd.read_csv(self.source_data["file_path"], header=0)

    def get_original_timestamps(self) -> np.ndarray:
        """
        Retrieve the original unaltered timestamps for the data in this interface.

        This function should retrieve the data on-demand by re-initializing the IO.

        Returns
        -------
        timestamps: numpy.ndarray
            The timestamps for the data stream.
        """
        raise NotImplementedError(
            "Unable to retrieve the original unaltered timestamps for this interface! "
            "Define the `get_original_timestamps` method for this interface."
        )

    def get_timestamps(self) -> np.ndarray:
        """
        Retrieve the timestamps for the data in this interface.

        Returns
        -------
        timestamps: numpy.ndarray
            The timestamps for the data stream.
        """
        raise NotImplementedError(
            "Unable to retrieve timestamps for this interface! Define the `get_timestamps` method for this interface."
        )

    def align_timestamps(self, aligned_timestamps: np.ndarray):
        """
        Replace all timestamps for this interface with those aligned to the common session start time.

        Must be in units seconds relative to the common 'session_start_time'.

        Parameters
        ----------
        aligned_timestamps : numpy.ndarray
            The synchronized timestamps for data in this interface.
        """
        raise NotImplementedError(
            "The protocol for synchronizing the timestamps of this interface has not been specified!"
        )

    def run_conversion(
        self,
        nwbfile_path: OptionalFilePathType = None,
        nwbfile: Optional[NWBFile] = None,
        metadata: Optional[dict] = None,
        stub_test: bool = False,
        overwrite: bool = False,
    ):
        with make_or_load_nwbfile(
            nwbfile_path=nwbfile_path, nwbfile=nwbfile, metadata=metadata, overwrite=overwrite, verbose=self.verbose
        ) as nwbfile_out:
            photometry_data = self._load_source_data()
            add_photometry(photometry_dataframe=photometry_data, nwbfile=nwbfile_out, metadata=metadata)
