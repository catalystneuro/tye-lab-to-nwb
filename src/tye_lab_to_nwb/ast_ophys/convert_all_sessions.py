import ast
from pathlib import Path
from typing import Optional

from neuroconv.utils import FilePathType
from tye_lab_to_nwb.ast_ophys.convert_session import session_to_nwb
from tye_lab_to_nwb.tools import read_session_config, parallel_execute


def parallel_convert_sessions(
    excel_file_path: FilePathType,
    num_parallel_jobs: Optional[int] = 1,
    stub_test: Optional[bool] = False,
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
    stub_test: bool, optional
        For testing purposes, when stub_test=True only writes a subset of ecephys and plexon data.
        Default is to write the whole ecephys recording and plexon data to the file.
    """

    config = read_session_config(excel_file_path=excel_file_path)

    kwargs_list = []
    for row_ind, row in config.iterrows():
        subject_metadata = dict()
        for subject_field in ["sex", "subject_id", "age", "genotype", "strain"]:
            if config[subject_field][row_ind]:
                subject_metadata[subject_field] = str(config[subject_field][row_ind])
        kwargs_list.append(
            dict(
                nwbfile_path=row["nwbfile_path"],
                miniscope_folder_path=row["miniscope_folder_path"],
                processed_miniscope_avi_file_path=row["processed_miniscope_avi_file_path"],
                motion_corrected_mat_file_path=row["motion_corrected_mat_file_path"],
                timestamps_mat_file_path=row["timestamps_mat_file_path"],
                reward_trials_indices=ast.literal_eval(row["reward_trials_indices"])
                if row["reward_trials_indices"]
                else None,
                segmentation_mat_file_path=row["segmentation_mat_file_path"],
                session_start_time=row["session_start_time"],
                subject_metadata=subject_metadata,
                stub_test=stub_test,
            )
        )
    parallel_execute(
        session_to_nwb_function=session_to_nwb,
        kwargs_list=kwargs_list,
        num_parallel_jobs=num_parallel_jobs,
    )


if __name__ == "__main__":
    # Parameters for converting sessions in parallel
    # The path to the Excel (.xlsx) file that contains the file paths for each data stream.
    # The number of rows in the file corresponds to the number of sessions that can be converted.
    excel_file_path = Path("/Volumes/t7-ssd/Miniscope/session_config.xlsx")

    # For faster conversion, stub_test=True would only write the first 100 frames of the imaging data.
    # When running a full conversion, use stub_test=False.
    stub_test = True

    # Run conversion for all sessions that are in the configuration file
    parallel_convert_sessions(
        excel_file_path=excel_file_path,
        stub_test=stub_test,
        num_parallel_jobs=1,  # defines the number of sessions that will be converted in parallel.
    )
