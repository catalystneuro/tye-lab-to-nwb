import traceback
from pathlib import Path
from typing import Optional, List
from warnings import warn

from dateutil import tz
from neuroconv.utils import (
    FilePathType,
    FolderPathType,
    load_dict_from_file,
    dict_deep_update,
)
from nwbinspector import inspect_nwbfile
from nwbinspector.inspector_tools import save_report, format_messages

from tye_lab_to_nwb.ast_ophys.ast_ophysnwbconverter import AStOphysNWBConverter


def session_to_nwb(
    nwbfile_path: FilePathType,
    miniscope_folder_path: Optional[FolderPathType] = None,
    processed_miniscope_avi_file_path: Optional[FilePathType] = None,
    motion_corrected_mat_file_path: Optional[FilePathType] = None,
    timestamps_mat_file_path: Optional[FilePathType] = None,
    reward_trials_indices: Optional[List[int]] = None,
    segmentation_mat_file_path: Optional[FilePathType] = None,
    subject_metadata: Optional[dict] = None,
    stub_test: Optional[bool] = False,
):
    """
    Converts a single session to NWB.

    Parameters
    ----------
    nwbfile_path : FilePathType
        The file path to the NWB file that will be created.
    miniscope_folder_path: FolderPathType, optional
        The path that points to the folder where the raw Miniscope data is located.
    processed_miniscope_avi_file_path: FilePathType, optional
        The path that points to the concatenated and first frames deleted "ffd" Miniscope video (.avi).
    motion_corrected_mat_file_path: FilePathType, optional
        The path to the .mat file that contains the motion corrected imaging data.
    timestamps_mat_file_path: FilePathType, optional
        The path to the .mat file that contains the timestamps for the trials data.
    reward_trials_indices: List, optional
        The list that denotes which trial indices are reward trials.
        e.g. [1, 3, 6, 9, 10, 12, 13, 15, 16, 20, 23, 24, 27, 28, 30]
    segmentation_mat_file_path: FilePathType, optional
        The path that points to the MATLAB file containing the "neuron" struct has been saved to the file.
    stub_test: bool, optional
        Write the first 100 frames to the NWB file for testing purposes.
        Default is to write the whole imaging and segmentation data to the file.
    """

    source_data = dict()
    conversion_options = dict()

    # Add raw Miniscope imaging
    if miniscope_folder_path:
        imaging_folder_path = Path(miniscope_folder_path)
        source_data.update(dict(RawImaging=dict(folder_path=str(imaging_folder_path))))
        conversion_options.update(dict(RawImaging=dict(stub_test=stub_test)))

    # Add processed Miniscope imaging
    if processed_miniscope_avi_file_path:
        source_data.update(
            dict(
                ProcessedImaging=dict(
                    file_path=str(processed_miniscope_avi_file_path),
                    timestamps_file_path=str(timestamps_mat_file_path),
                )
            )
        )
        conversion_options.update(dict(ProcessedImaging=dict(stub_test=stub_test)))

    # Add motion corrected imaging
    if motion_corrected_mat_file_path:
        source_data.update(
            dict(
                MotionCorrectedImaging=dict(
                    file_path=str(motion_corrected_mat_file_path),
                    timestamps_file_path=str(timestamps_mat_file_path),
                )
            )
        )
        reward_trials_indices = None or reward_trials_indices
        conversion_options.update(
            dict(MotionCorrectedImaging=dict(stub_test=stub_test, reward_trials_indices=reward_trials_indices))
        )

    # Add Segmentation
    if segmentation_mat_file_path:
        source_data.update(dict(Segmentation=dict(file_path=str(segmentation_mat_file_path))))
        conversion_options.update(dict(Segmentation=dict(stub_test=stub_test)))

    converter = AStOphysNWBConverter(source_data=source_data)

    # Add datetime to conversion
    metadata = converter.get_metadata()

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "metadata" / "general_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    subject_id = None
    if "session_id" not in metadata["NWBFile"] and processed_miniscope_avi_file_path is not None:
        file_name = Path(processed_miniscope_avi_file_path).stem
        subject_id, disc_id = file_name.split("_", maxsplit=2)[:2]
        session_id = f"{subject_id}-{disc_id}"
        metadata["NWBFile"].update(session_id=session_id)

    if subject_metadata:
        metadata = dict_deep_update(metadata, dict(Subject=subject_metadata))

    if "Subject" in metadata and "subject_id" not in metadata["Subject"] and subject_id is not None:
        metadata["Subject"].update(subject_id=subject_id)

    # For data provenance we can add the time zone information to the conversion if missing
    session_start_time = metadata["NWBFile"]["session_start_time"]
    # Get the timezone object for US/Pacific (San Diego, California)
    pacific_timezone = tz.gettz("US/Pacific")
    metadata["NWBFile"].update(session_start_time=session_start_time.replace(tzinfo=pacific_timezone))

    try:
        # Run conversion
        converter.run_conversion(
            nwbfile_path=str(nwbfile_path), metadata=metadata, conversion_options=conversion_options
        )

        # Run inspection for nwbfile
        nwbfile_path = Path(nwbfile_path)
        results = list(inspect_nwbfile(nwbfile_path=nwbfile_path))
        report_path = nwbfile_path.parent / f"{nwbfile_path.stem}_inspector_result.txt"
        save_report(
            report_file_path=report_path,
            formatted_messages=format_messages(
                results,
                levels=["importance", "file_path"],
            ),
            overwrite=True,
        )
    except Exception as e:
        with open(f"{nwbfile_path.parent}/{nwbfile_path.stem}_error_log.txt", "w") as f:
            f.write(traceback.format_exc())
        warn(f"There was an error during the conversion of {nwbfile_path}. The full traceback: {e}")


if __name__ == "__main__":
    # Parameters for converting a single session

    # The file path where the NWB file will be created.
    nwbfile_path = "/Users/weian/catalystneuro/demo_notebooks/C6-J588-Disc5.nwb"

    # The folder path where the *raw* Miniscope data is located. (optional)
    # Check the `ast_ophys_notes.md` file to see the expected folder structure.
    miniscope_folder_path = "/Volumes/t7-ssd/Miniscope/C6-J588_Disc5"

    # The file path that points to the concatenated and first frames deleted "ffd" Miniscope video (.avi). (optional)
    processed_miniscope_avi_file_path = "/Volumes/t7-ssd/Miniscope/C6-J588_Disc5_msCamAll_ffd.avi"

    # The file path that points to the motion corrected Miniscope video (.mat). (optional)
    motion_corrected_mat_file_path = "/Volumes/t7-ssd/Miniscope/C6-J588_Disc5_msCamComb_MC.mat"

    # The file path that points to the MATLAB file that contains the Miniscope and trial timings.
    # Required for the processed and motion corrected Miniscope data.
    timestamps_mat_file_path = "/Volumes/t7-ssd/Miniscope/C6-J588_Disc5_timestampsAllCumulData.mat"

    # The list of trials that correspond to the CS-Reward trials. (optional)
    reward_trials_indices = [1, 3, 6, 9, 10, 12, 13, 15, 16, 20, 23, 24, 27, 28, 30]

    # The file path that points to the MATLAB file containing the "neuron" struct has been saved to the file.
    # Check the `ast_ophys_notes.md` file to see how to save the "neuron" struct to a MATLAB file.
    segmentation_mat_file_path = "/Volumes/t7-ssd/Miniscope/neuron.mat"

    # For faster conversion, stub_test=True will only write the first 100 frames of the imaging data.
    # When running a full conversion, use stub_test=False.
    stub_test = False

    # subject metadata like sex (optional)
    subject_metadata = dict(sex="M")

    # Run conversion for a single session
    session_to_nwb(
        nwbfile_path=nwbfile_path,
        miniscope_folder_path=miniscope_folder_path,
        processed_miniscope_avi_file_path=processed_miniscope_avi_file_path,
        motion_corrected_mat_file_path=motion_corrected_mat_file_path,
        timestamps_mat_file_path=timestamps_mat_file_path,
        reward_trials_indices=reward_trials_indices,
        segmentation_mat_file_path=segmentation_mat_file_path,
        subject_metadata=subject_metadata,
        stub_test=stub_test,
    )
