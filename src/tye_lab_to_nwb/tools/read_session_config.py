from pathlib import Path

import numpy as np
import pandas as pd

from neuroconv.utils import FilePathType


def read_session_config(excel_file_path: FilePathType) -> pd.DataFrame:
    sessions_config_file_path = Path(excel_file_path)
    assert sessions_config_file_path.is_file(), f"The excel file does not exist at '{excel_file_path}'."
    config = pd.read_excel(sessions_config_file_path)

    assert (
        "ecephys_folder_path" in config.columns
    ), "The excel file does not contain the expected 'ecephys_folder_path' column."
    assert "nwbfile_path" in config.columns, "The excel file does not contain the expected 'nwbfile_path' column."

    config = config.replace(np.nan, None)
    return config
