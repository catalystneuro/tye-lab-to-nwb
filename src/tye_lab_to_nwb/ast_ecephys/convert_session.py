from pathlib import Path
from typing import Optional, Dict

from neuroconv.utils import (
    FilePathType,
    FolderPathType,
    load_dict_from_file,
    dict_deep_update,
)
from tye_lab_to_nwb.ast_ecephys import AStEcephysNWBConverter


def session_to_nwb(
    nwbfile_path: FilePathType,
    ecephys_recording_folder_path: FolderPathType,
    plexon_file_path: Optional[FilePathType] = None,
    events_file_path: Optional[FilePathType] = None,
    sleap_file_path: Optional[FilePathType] = None,
    video_file_path: Optional[FilePathType] = None,
    subject_metadata: Optional[Dict[str, str]] = None,
    stub_test: Optional[bool] = False,
):
    """
    Converts a single session to NWB.

    Parameters
    ----------
    nwbfile_path : FilePathType
        The file path to the NWB file that will be created.
    ecephys_recording_folder_path: FolderPathType
        The path that points to the folder where the OpenEphys (.continuous) files are located.
    plexon_file_path: FilePathType, optional
        The path that points to the Plexon (.plx) file that contains the spike times.
    events_file_path: FilePathType, optional
        The path that points to the .mat file that contains the event onset and offset times.
    sleap_file_path: FilePathType, optional
        The path that points to the .slp file that contains the SLEAP output.
    video_file_path: FilePathType, optional
        The path that points to the video file for SLEAP input.
    subject_metadata: dict, optional
        The optional metadata for the experimental subject.
    stub_test: bool, optional
        For testing purposes, when stub_test=True only writes a subset of ecephys and plexon data.
        Default is to write the whole ecephys recording and plexon data to the file.
    """
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
    if sleap_file_path:
        sleap_source_data = dict(Behavior=dict(file_path=str(sleap_file_path)))
        source_data.update(sleap_source_data)
        if video_file_path:
            sleap_source_data["Behavior"].update(video_file_path=str(video_file_path))

    # Add video (optional)
    if video_file_path:
        source_data.update(dict(Video=dict(file_paths=[str(video_file_path)])))

    converter = AStEcephysNWBConverter(source_data=source_data)

    # Add datetime to conversion
    metadata = converter.get_metadata()

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "metadata" / "general_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    if subject_metadata:
        metadata = dict_deep_update(metadata, dict(Subject=subject_metadata))

    if "session_id" not in metadata["NWBFile"]:
        ecephys_folder_name = ecephys_recording_folder_path.name
        session_id = ecephys_folder_name.replace(" ", "").replace("_", "-")
        metadata["NWBFile"].update(session_id=session_id)

    nwbfile_path = Path(nwbfile_path)
    nwbfile_name = nwbfile_path.name
    if stub_test:
        nwbfile_path = nwbfile_path.parent / "nwb_stub" / nwbfile_name
    nwbfile_path.parent.mkdir(parents=True, exist_ok=True)

    # Run conversion
    converter.run_conversion(
        nwbfile_path=str(nwbfile_path),
        metadata=metadata,
        conversion_options=conversion_options,
    )


if __name__ == "__main__":
    # Parameters for conversion
    # The path that points to the folder where the OpenEphys (.continuous) files are located.
    ecephys_folder_path = Path(
        "/Volumes/t7-ssd/OpenEphys/3014_2018-06-26_14-21-37_illidanDiscD4",
    )

    # The path that points to the Plexon file (optional)
    # plexon_file_path = None
    plexon_file_path = ecephys_folder_path / "3014_20180626_illidanDiscD4_sort.plx"

    # Parameters for events data (optional)
    # The file path that points to the events.mat file
    # events_mat_file_path = None
    events_mat_file_path = ecephys_folder_path / "3014_20180626_illidanDiscD4_events.mat"

    # Parameters for pose estimation data (optional)
    # The file path that points to the SLEAP output (.slp) file
    # sleap_file_path = None
    sleap_file_path = Path("/Volumes/t7-ssd/SLEAP/predictions/3014illidan_20180926_DiscD4.predictions.slp")
    # The file path that points to the source video for pose estimation
    video_file_path = Path("/Volumes/t7-ssd/SLEAP/sourceVids/FFBatch/3014illidan_20180926_DiscD4.mp4")

    # The file path where the NWB file will be created.
    nwbfile_path = Path("/Volumes/t7-ssd/Fergil_NWB/nwbfiles/3014_illidanDiscD4_ecephys.nwb")

    # subject metadata (optional)
    subject_metadata = dict(sex="M", subject_id="3014")

    # For faster conversion, stub_test=True would only write a subset of ecephys and plexon data.
    # When running a full conversion, use stub_test=False.
    stub_test = False

    session_to_nwb(
        nwbfile_path=nwbfile_path,
        ecephys_recording_folder_path=ecephys_folder_path,
        plexon_file_path=plexon_file_path,
        events_file_path=events_mat_file_path,
        sleap_file_path=sleap_file_path,
        video_file_path=video_file_path,
        subject_metadata=subject_metadata,
        stub_test=stub_test,
    )