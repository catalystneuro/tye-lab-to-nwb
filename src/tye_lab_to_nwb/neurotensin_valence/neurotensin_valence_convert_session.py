"""Primary script to run to convert an entire session for of data using the NWBConverter."""

import traceback
from pathlib import Path
from typing import Optional, Dict
from warnings import warn

from dateutil import parser

from neuroconv.utils import (
    load_dict_from_file,
    dict_deep_update,
    FilePathType,
    FolderPathType,
)
from nwbinspector import inspect_nwbfile
from nwbinspector.inspector_tools import save_report, format_messages

from tye_lab_to_nwb.neurotensin_valence import NeurotensinValenceNWBConverter


def session_to_nwb(
    nwbfile_path: FilePathType,
    ecephys_recording_folder_path: Optional[FolderPathType] = None,
    subject_metadata: Optional[Dict[str, str]] = None,
    plexon_file_path: Optional[FilePathType] = None,
    events_file_path: Optional[FilePathType] = None,
    pose_estimation_file_path: Optional[FilePathType] = None,
    pose_estimation_config_file_path: Optional[FilePathType] = None,
    pose_estimation_sampling_rate: Optional[float] = None,
    session_start_time: Optional[str] = None,
    original_video_file_path: Optional[FilePathType] = None,
    labeled_video_file_path: Optional[FilePathType] = None,
    confocal_images_oif_file_path: Optional[FilePathType] = None,
    confocal_images_composite_tif_file_path: Optional[FilePathType] = None,
    stub_test: bool = False,
):
    """
    Converts a single session to NWB.

    Parameters
    ----------
    nwbfile_path : FilePathType
        The file path to the NWB file that will be created.
    ecephys_recording_folder_path: FolderPathType
         The path that points to the folder where the OpenEphys (.continuous) files are located.
    subject_metadata: dict, optional
        The optional metadata for the experimental subject.
    plexon_file_path: FilePathType, optional
        The path that points to the Plexon (.plx) file that contains the spike times.
    events_file_path: FilePathType, optional
        The path that points to the .mat file that contains the event onset and offset times.
    pose_estimation_file_path: FilePathType, optional
        The path that points to the .csv file that contains the DLC output.
    pose_estimation_config_file_path: FilePathType, optional
        The path that points to the .pickle file that contains the DLC configuration settings.
    original_video_file_path: FilePathType, optional
        The path that points to the original behavior movie that was used for pose estimation.
    labeled_video_file_path: FilePathType, optional
        The path that points to the labeled behavior movie.
    confocal_images_oif_file_path: FilePathType, optional
        The path that points to the Olympus Image File (.oif).
    confocal_images_composite_tif_file_path: FilePathType, optional
        The path that points to the TIF image that contains the confocal images aggregated over depth.
    stub_test: bool, optional
        For testing purposes, when stub_test=True only writes a subset of ecephys and plexon data.
        Default is to write the whole ecephys recording and plexon data to the file.
    """

    source_data = dict()
    conversion_options = dict()

    # Add Recording
    if ecephys_recording_folder_path:
        recording_source_data = dict(folder_path=str(ecephys_recording_folder_path), stream_name="Signals CH")

        source_data.update(dict(Recording=recording_source_data))
        conversion_options.update(dict(Recording=dict(stub_test=stub_test)))

    # Add Sorting (optional)
    if plexon_file_path:
        source_data.update(dict(Sorting=dict(file_path=str(plexon_file_path))))
        conversion_options.update(dict(Sorting=dict(stub_test=stub_test)))

    # Add Behavior (optional)
    # Add events
    if events_file_path:
        event_names_mapping = {
            0: "reward_stimulus_presentation",
            1: "phototagging",
            2: "shock_stimulus_presentation",
            3: "reward_delivery",
            4: "shock_relay",
            5: "port_entry",
            6: "neutral_stimulus_presentation",
        }
        read_kwargs = dict(event_names_mapping=event_names_mapping)
        events_source_data = dict(file_path=str(events_file_path), read_kwargs=read_kwargs)
        source_data.update(dict(Events=events_source_data))

        events_column_mappings = dict(onset="start_time", offset="stop_time")
        events_conversion_options = dict(column_name_mapping=events_column_mappings)
        conversion_options.update(
            dict(
                Events=events_conversion_options,
            )
        )

    # Add pose estimation (optional)
    pose_estimation_source_data = dict()
    pose_estimation_conversion_options = dict()
    if pose_estimation_file_path:
        pose_estimation_source_data.update(file_path=str(pose_estimation_file_path))
        if pose_estimation_config_file_path:
            pose_estimation_source_data.update(config_file_path=str(pose_estimation_config_file_path))
        elif pose_estimation_sampling_rate is not None:
            pose_estimation_conversion_options.update(rate=float(pose_estimation_sampling_rate))

        source_data.update(dict(PoseEstimation=pose_estimation_source_data))

    if original_video_file_path:
        pose_estimation_conversion_options.update(original_video_file_path=original_video_file_path)
        source_data.update(
            dict(
                OriginalVideo=dict(file_paths=[str(original_video_file_path)]),
            )
        )
    if labeled_video_file_path:
        pose_estimation_conversion_options.update(labeled_video_file_path=labeled_video_file_path)

    if pose_estimation_source_data:
        # The edges between the nodes (e.g. labeled body parts) defined as array of pairs of indices.
        edges = [(0, 1), (0, 2), (2, 3), (1, 3), (5, 6), (5, 7), (5, 8), (5, 9)]
        pose_estimation_conversion_options.update(edges=edges)
        conversion_options.update(dict(PoseEstimation=pose_estimation_conversion_options))

    # Add confocal images
    images_source_data = dict()
    if confocal_images_oif_file_path:
        images_source_data.update(file_path=str(confocal_images_oif_file_path))
        if confocal_images_composite_tif_file_path:
            images_source_data.update(composite_tif_file_path=str(confocal_images_composite_tif_file_path))

        source_data.update(dict(Images=images_source_data))

    converter = NeurotensinValenceNWBConverter(source_data=source_data)

    # Add datetime to conversion
    metadata = converter.get_metadata()

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "metadata" / "general_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    if subject_metadata:
        metadata = dict_deep_update(metadata, dict(Subject=subject_metadata))

    if "session_id" not in metadata["NWBFile"]:
        if ecephys_recording_folder_path:
            ecephys_recording_folder_path = Path(ecephys_recording_folder_path)
            ecephys_folder_name = ecephys_recording_folder_path.name
            session_id = ecephys_folder_name.replace(" ", "").replace("_", "-")
        elif pose_estimation_file_path:
            session_id = Path(pose_estimation_file_path).name.replace(" ", "").replace("_", "-")
        else:
            session_id = Path(nwbfile_path).stem.replace(" ", "").replace("_", "-")

        metadata["NWBFile"].update(session_id=session_id)

    if "session_start_time" not in metadata["NWBFile"]:
        if session_start_time is None:
            raise ValueError(
                "When ecephys recording is not specified the start time of the session must be provided."
                "Specify session_start_time in YYYY-MM-DDTHH:MM:SS format (e.g. 2023-08-21T15:30:00)."
            )
        session_start_time_dt = parser.parse(session_start_time)
        metadata["NWBFile"].update(session_start_time=session_start_time_dt)

    nwbfile_path = Path(nwbfile_path)
    try:
        # Run conversion
        converter.run_conversion(
            nwbfile_path=str(nwbfile_path), metadata=metadata, conversion_options=conversion_options
        )

        # Run inspection for nwbfile
        results = list(inspect_nwbfile(nwbfile_path=nwbfile_path))
        report_path = nwbfile_path.parent / f"{nwbfile_path.stem}_inspector_result.txt"
        save_report(
            report_file_path=report_path,
            formatted_messages=format_messages(
                results,
                levels=["importance", "file_path"],
            ),
        )
    except Exception as e:
        with open(f"{nwbfile_path.parent}/{nwbfile_path.stem}_error_log.txt", "w") as f:
            f.write(traceback.format_exc())
        warn(f"There was an error during the conversion of {nwbfile_path}. The full traceback: {e}")


if __name__ == "__main__":
    # Parameters for conversion
    # The path that points to the folder where the OpenEphys (.continuous) files are located.
    ecephys_folder_path = Path("Hao_NWB/recording/H28_2020-02-19_14-27-39_Disc3_20k")

    # The path that points to the Plexon file (optional)
    # plexon_file_path = None
    plexon_file_path = Path("Hao_NWB/recording/H28_2020-02-20_13-43-12_Disc4_20k/0028_20200221_20k.plx")

    # Parameters for events data (optional)
    # The file path that points to the events.mat file
    # events_mat_file_path = None
    events_mat_file_path = Path(
        "/Volumes/t7-ssd/Hao_NWB/recording/H28_2020-02-20_13-43-12_Disc4_20k/0028_20200221_20k_events.mat"
    )

    # Parameters for pose estimation data (optional)
    # The file path that points to the DLC output (.CSV file)
    # pose_estimation_file_path = None
    pose_estimation_file_path = (
        "Hao_NWB/behavior/freezing_DLC/28_Disc4DLC_resnet50_Hao_MedPC_ephysFeb9shuffle1_800000.csv"
    )
    # The file path that points to the DLC configuration file (.pickle file), optional
    # pose_estimation_config_file_path = None
    pose_estimation_config_file_path = (
        "Hao_NWB/behavior/freezing_DLC/H028Disc4DLC_resnet50_Hao_MedPC_ephysFeb9shuffle1_800000includingmetadata.pickle"
    )
    # If the pickle file is not available the sampling rate in units of Hz for the behavior data must be provided.
    pose_estimation_sampling_rate = None

    # For sessions where only the pose estimation data is available the start time of the session must be provided.
    # The session_start_time in YYYY-MM-DDTHH:MM:SS format (e.g. 2023-08-21T15:30:00).
    session_start_time = None

    # The file path that points to the behavior movie file, optional
    # original_video_file_path = None
    original_video_file_path = "H028Disc4.mkv"
    # The file path that points to the labeled behavior movie file, optional
    # labeled_video_file_path = None
    labeled_video_file_path = "H028Disc4DLC_resnet50_Hao_MedPC_ephysFeb9shuffle1_800000_labeled.mp4"

    # Parameters for histology images (optional)
    # The file path to the Olympus Image File (.oif)
    confocal_images_oif_file_path = "Hao_NWB/problem_histo/H31PVT_40x.oif"
    # The file path to the aggregated confocal images in TIF format.
    # confocal_images_composite_tif_file_path = None
    confocal_images_composite_tif_file_path = "Hao_NWB/histo/H28_MAX_Composite.tif"

    # The file path where the NWB file will be created.
    nwbfile_path = Path("Hao_NWB/nwbfiles/test.nwb")

    # For faster conversion, stub_test=True would only write a subset of ecephys and plexon data.
    # When running a full conversion, use stub_test=False.
    stub_test = False

    # subject metadata (optional)
    subject_metadata = dict(sex="M")

    session_to_nwb(
        nwbfile_path=nwbfile_path,
        ecephys_recording_folder_path=ecephys_folder_path,
        subject_metadata=subject_metadata,
        plexon_file_path=plexon_file_path,
        events_file_path=events_mat_file_path,
        pose_estimation_file_path=pose_estimation_file_path,
        pose_estimation_config_file_path=pose_estimation_config_file_path,
        pose_estimation_sampling_rate=pose_estimation_sampling_rate,
        session_start_time=session_start_time,
        original_video_file_path=original_video_file_path,
        labeled_video_file_path=labeled_video_file_path,
        confocal_images_oif_file_path=confocal_images_oif_file_path,
        confocal_images_composite_tif_file_path=confocal_images_composite_tif_file_path,
        stub_test=stub_test,
    )
