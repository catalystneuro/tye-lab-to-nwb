from pathlib import Path
from typing import Optional, List

from neuroconv.utils import (
    FilePathType,
    FolderPathType,
)
from tye_lab_to_nwb.ast_ophys.ast_ophysnwbconverter import AStOphysNWBConverter


def session_to_nwb(
    nwbfile_path: FilePathType,
    miniscope_folder_path: Optional[FolderPathType] = None,
    processed_miniscope_avi_file_path: Optional[FilePathType] = None,
    motion_corrected_mat_file_path: Optional[FilePathType] = None,
    timestamps_mat_file_path: Optional[FilePathType] = None,
    reward_trials_indices: Optional[List[int]] = None,
    segmentation_mat_file_path: Optional[FilePathType] = None,
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
    # editable_metadata_path = Path(__file__).parent / "metadata" / "general_metadata.yaml"
    # editable_metadata = load_dict_from_file(editable_metadata_path)
    # metadata = dict_deep_update(metadata, editable_metadata)

    converter.run_conversion(
        nwbfile_path=str(nwbfile_path),
        metadata=metadata,
        conversion_options=conversion_options,
        overwrite=True,
    )


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

    # Run conversion for a single session
    session_to_nwb(
        nwbfile_path=nwbfile_path,
        miniscope_folder_path=miniscope_folder_path,
        processed_miniscope_avi_file_path=processed_miniscope_avi_file_path,
        motion_corrected_mat_file_path=motion_corrected_mat_file_path,
        timestamps_mat_file_path=timestamps_mat_file_path,
        reward_trials_indices=reward_trials_indices,
        segmentation_mat_file_path=segmentation_mat_file_path,
        stub_test=stub_test,
    )
