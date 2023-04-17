import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from neuroconv.utils import FilePathType
from nwbinspector.utils import calculate_number_of_cpu
from pynwb.file import Subject
from tqdm import tqdm

from tye_lab_to_nwb.neurotensin_valence.neurotensin_valence_convert_session import session_to_nwb


def parallel_convert_sessions(
    excel_file_path: FilePathType,
    num_parallel_jobs: Optional[int] = 1,
):
    """
    Parallel converts NWB files.

    Parameters
    ----------
    excel_file_path : FilePathType
        The path to the Excel (.xlsx) file that contains the parameters for converting the sessions.
        The number of rows in the file corresponds to the number of sessions that will be converted.
        The folder path to the ecephys recording and the file path to the NWB file are required values for each row.
    num_parallel_jobs: int, optional
        The number of parallel converted sessions. The default is to convert one session at a time.
        When not specified (num_parallel_jobs=None) it is set to use all available CPUs.

    """

    sessions_config_file_path = Path(excel_file_path)
    assert sessions_config_file_path.is_file(), f"The excel file does not exist at '{excel_file_path}'."
    config = pd.read_excel(sessions_config_file_path)

    assert (
        "ecephys_folder_path" in config.columns
    ), "The excel file does not contain the expected 'ecephys_folder_path' column."
    assert "nwbfile_path" in config.columns, "The excel file does not contain the expected 'nwbfile_path' column."

    config = config.replace(np.nan, None)

    if num_parallel_jobs is None:
        num_parallel_jobs = os.cpu_count()

    max_workers = calculate_number_of_cpu(requested_cpu=num_parallel_jobs)
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        with tqdm(total=len(config["ecephys_folder_path"]), position=0, leave=False) as progress_bar:
            futures = []

            for row_ind, row in config.iterrows():
                subject_metadata = dict()
                for subject_field in Subject.__nwbfields__:
                    if subject_field in row:
                        if row[subject_field]:
                            subject_metadata.update({subject_field: row[subject_field]})

                # execute call
                futures.append(
                    executor.submit(
                        session_to_nwb,
                        nwbfile_path=row["nwbfile_path"],
                        ecephys_recording_folder_path=row["ecephys_folder_path"],
                        # optional parameters
                        subject_metadata=subject_metadata,
                        plexon_file_path=row["plexon_file_path"],
                        events_file_path=row["events_mat_file_path"],
                        pose_estimation_file_path=row["pose_estimation_csv_file_path"],
                        pose_estimation_config_file_path=row["pose_estimation_pickle_file_path"],
                        original_video_file_path=row["behavior_movie_file_path"],
                        labeled_video_file_path=row["behavior_labeled_movie_file_path"],
                        confocal_images_oif_file_path=row["confocal_images_oif_file_path"],
                        confocal_images_composite_tif_file_path=row["confocal_images_composite_tif_file_path"],
                        stub_test=False,
                    )
                )
            for future in as_completed(futures):
                future.result()
                progress_bar.update(1)


if __name__ == "__main__":
    # The path to the Excel (.xlsx) file that contains the parameters for converting the sessions.
    # The number of rows in the file corresponds to the number of sessions that will be converted.
    excel_file_path = "/Volumes/t7-ssd/Hao_NWB/session_config.xlsx"

    parallel_convert_sessions(
        excel_file_path=excel_file_path,
        num_parallel_jobs=3,  # defines the number of sessions that will be converted in parallel.
    )
