"""Primary script to run to convert an entire session for of data using the NWBConverter."""
import re
from pathlib import Path
from typing import Optional, Dict

from neuroconv.utils import (
    load_dict_from_file,
    dict_deep_update,
    FilePathType,
    FolderPathType,
)

from tye_lab_to_nwb.neurotensin_valence import NeurotensinValenceNWBConverter


def session_to_nwb(
    ecephys_recording_folder_path: FolderPathType,
    output_dir_path: FilePathType,
    plexon_file_path: Optional[FilePathType] = None,
    events_file_path: Optional[FilePathType] = None,
    histology_source_data: Optional[Dict[str, str]] = None,
    pose_estimation_source_data: Optional[Dict[str, str]] = None,
    pose_estimation_conversion_options: Optional[Dict[str, str]] = None,
    stub_test: bool = False,
):
    ecephys_recording_folder_path = Path(ecephys_recording_folder_path)

    source_data = dict()
    conversion_options = dict()

    # Add Recording
    source_data.update(dict(Recording=dict(folder_path=str(ecephys_recording_folder_path), stream_name="Signals CH")))
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
        events_source_data = dict(file_path=events_file_path, read_kwargs=read_kwargs)
        source_data.update(dict(Events=events_source_data))

        events_column_mappings = dict(onset="start_time", offset="stop_time")
        events_conversion_options = dict(column_name_mapping=events_column_mappings)
        conversion_options.update(
            dict(
                Events=events_conversion_options,
            )
        )

    # Add pose estimation (optional)
    if pose_estimation_source_data is not None:
        source_data.update(dict(PoseEstimation=pose_estimation_source_data))
        if "config_file_path" not in pose_estimation_source_data:
            assert (
                "rate" in pose_estimation_conversion_options
            ), "The 'rate' must be specified when the sampling frequency cannot be read from the configuration (.pickle) file."
        conversion_options.update(dict(PoseEstimation=pose_estimation_conversion_options))

    if pose_estimation_conversion_options is not None:
        if "original_video_file_path" in pose_estimation_conversion_options:
            source_data.update(
                dict(
                    OriginalVideo=dict(file_paths=[pose_estimation_conversion_options["original_video_file_path"]]),
                )
            )

    # Add confocal images
    if histology_source_data is not None:
        source_data.update(dict(Images=histology_source_data))

    converter = NeurotensinValenceNWBConverter(source_data=source_data)

    # Add datetime to conversion
    metadata = converter.get_metadata()

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "metadata" / "general_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    ecephys_folder_name = ecephys_recording_folder_path.parent.name
    filename_regex_result = re.search("([a-zA-Z]+\d+)_(.*)", ecephys_folder_name)
    if filename_regex_result is not None:
        subject_id, session_id = filename_regex_result.groups()
        if "subject_id" not in metadata["Subject"]:
            metadata["Subject"].update(subject_id=subject_id)
        if "session_id" not in metadata["NWBFile"]:
            metadata["NWBFile"].update(session_id=session_id.replace("_", "-"))

    if "subject_id" in metadata["Subject"]:
        output_dir_path = Path(output_dir_path) / f"sub-{metadata['Subject']['subject_id']}"
    if stub_test:
        output_dir_path = Path(output_dir_path) / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    if "subject_id" in metadata["Subject"] and "session_id" in metadata["NWBFile"]:
        nwbfile_name = f"sub-{subject_id}_ses-{session_id}.nwb"
    else:
        nwbfile_name = f"{ecephys_folder_name}.nwb"
    nwbfile_path = output_dir_path / nwbfile_name

    # Run conversion
    converter.run_conversion(metadata=metadata, nwbfile_path=nwbfile_path, conversion_options=conversion_options)


if __name__ == "__main__":
    # Parameters for conversion
    # The path that points to the folder where the OpenEphys (.continuous) files are located.
    ecephys_folder_path = Path("Hao_NWB/recording/H28_2020-02-20_13-43-12_Disc4_20k/openephys")

    # The path that points to the Plexon file (optional)
    # plexon_file_path = None
    plexon_file_path = Path("Hao_NWB/recording/H28_2020-02-20_13-43-12_Disc4_20k/0028_20200221_20k.plx")

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
    pose_estimation_source_data = dict(
        file_path=pose_estimation_file_path,
        config_file_path=pose_estimation_config_file_path,
    )

    # The edges between the nodes (e.g. labeled body parts) defined as array of pairs of indices.
    edges = [(0, 1), (0, 2), (2, 3), (1, 3), (5, 6), (5, 7), (5, 8), (5, 9)]
    pose_estimation_conversion_options = dict(
        original_video_file_path="H028Disc4.mkv",
        labeled_video_file_path="H028Disc4DLC_resnet50_Hao_MedPC_ephysFeb9shuffle1_800000_labeled.mp4",
        edges=edges,
        # rate=30.0,  # Specifying 'rate' is necessary when the DLC configuration (.pickle) file is not available.
    )

    # Parameters for events data (optional)
    # The file path that points to the events.mat file
    # events_mat_file_path = None
    events_mat_file_path = Path("Hao_NWB/recording/H28_2020-02-20_13-43-12_Disc4_20k/0028_20200221_20k_events.mat")

    # Parameters for histology images (optional)
    # Add histology source data (optional)
    # histology_source_data = None
    histology_source_data = dict(
        file_path="Hao_NWB/histo/H28PVT_40x.oif",  # The file path to the Olympus Image File (.oif)
        composite_tif_file_path="Hao_NWB/histo/H28_MAX_Composite.tif",  # The file path to the aggregated confocal images in TIF format.
    )

    # The folder path where the NWB file will be created.
    nwbfile_folder_path = Path("Hao_NWB/nwbfiles")
    # For faster conversion, stub_test=True would only write a subset of ecephys and plexon data.
    # When running a full conversion, use stub_test=False.
    stub_test = False

    session_to_nwb(
        ecephys_recording_folder_path=ecephys_folder_path,
        output_dir_path=nwbfile_folder_path,
        plexon_file_path=plexon_file_path,
        events_file_path=events_mat_file_path,
        histology_source_data=histology_source_data,
        pose_estimation_source_data=pose_estimation_source_data,
        pose_estimation_conversion_options=pose_estimation_conversion_options,
        stub_test=stub_test,
    )
