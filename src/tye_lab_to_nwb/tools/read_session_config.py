from pathlib import Path

import numpy as np
import pandas as pd

from neuroconv.utils import FilePathType


def read_session_config(
    excel_file_path: FilePathType, required_column_name: str = "ecephys_folder_path"
) -> pd.DataFrame:
    """
    Converts a single session to NWB.

    Parameters
    ----------
    excel_file_path : FilePathType
        The path to the Excel (.xlsx) file that contains the file paths for each data stream.
        The number of rows in the file corresponds to the number of sessions that can be converted.
    required_column_name: str
        The name of the column in the file that corresponds to the ecephys data stream.
        The default name for this column is 'ecephys_folder_path'.
    """
    sessions_config_file_path = Path(excel_file_path)
    assert sessions_config_file_path.is_file(), f"The excel file does not exist at '{excel_file_path}'."
    config = pd.read_excel(sessions_config_file_path)

    assert (
        required_column_name in config.columns
    ), f"The excel file does not contain the expected '{required_column_name}' column."
    assert "nwbfile_path" in config.columns, "The excel file does not contain the expected 'nwbfile_path' column."

    config = config.replace(np.nan, None)
    return config
