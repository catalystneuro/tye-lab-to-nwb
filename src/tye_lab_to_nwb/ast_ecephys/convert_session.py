import traceback
from pathlib import Path
from typing import Optional, Dict
from warnings import warn

from importlib.metadata import version
from packaging.version import Version

from nwbinspector import inspect_nwb
from nwbinspector.inspector_tools import format_messages, save_report

from neuroconv.utils import (
    FilePathType,
    FolderPathType,
    load_dict_from_file,
    dict_deep_update,
)
from tye_lab_to_nwb.ast_ecephys import AStEcephysNWBConverter
from tye_lab_to_nwb.tools import read_session_config


def session_to_nwb(
    nwbfile_path: FilePathType,
    ecephys_recording_folder_path: FolderPathType,
    plexon_file_path: Optional[FilePathType] = None,
    group_mat_file_path: Optional[FilePathType] = None,
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
    group_mat_file_path: FilePathType, optional
        The path that points to the MAT file with the manually clustered spikes and
        the filtering criteria for the units.
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
    recording_source_data = dict(folder_path=str(ecephys_recording_folder_path), stream_name="Signals CH")
    if Version(version("neo")) > Version("0.12.0"):
        recording_source_data.update(ignore_timestamps_errors=True)

    source_data.update(dict(Recording=recording_source_data))
    conversion_options.update(dict(Recording=dict(stub_test=stub_test)))

    # Add Sorting (optional)
    if plexon_file_path:
        source_data.update(dict(Sorting=dict(file_path=str(plexon_file_path))))
        conversion_options.update(
            dict(
                Sorting=dict(
                    stub_test=stub_test,
                    write_as="processing",
                    units_name="uncurated_units",
                    units_description="The uncurated units exported from the offline Plexon spike sorter.",
                )
            )
        )

    if group_mat_file_path:
        source_data.update(dict(FilteredSorting=dict(file_path=str(group_mat_file_path))))
        conversion_options.update(
            dict(
                FilteredSorting=dict(
                    stub_test=stub_test,
                    units_description="The clustered units after exluding duplicated, low-quality (any units with 2 or lower excluded) and low-firing (units with less than 1000 spikes) units.",
                )
            )
        )

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

    try:
        # Run conversion
        converter.run_conversion(
            nwbfile_path=str(nwbfile_path), metadata=metadata, conversion_options=conversion_options
        )

        # Run inspection for nwbfile
        results = list(inspect_nwb(nwbfile_path=nwbfile_path))
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
    # Parameters for converting a single session
    # The path to the Excel (.xlsx) file that contains the file paths for each data stream.
    # The number of rows in the file corresponds to the number of sessions that can be converted.
    excel_file_path = Path("/Volumes/t7-ssd/OpenEphys/session_config.xlsx")
    config = read_session_config(excel_file_path=excel_file_path)
    # Choose which session will be converted by specifying the index of the row
    row_index = 0

    # # Add subject metadata (optional)
    subject_metadata = dict()
    for subject_field in ["sex", "subject_id", "age", "genotype", "strain"]:
        if config[subject_field][row_index]:
            subject_metadata[subject_field] = str(config[subject_field][row_index])

    # For faster conversion, stub_test=True would only write a subset of ecephys and plexon data.
    # When running a full conversion, use stub_test=False.
    stub_test = False

    # Run conversion for a single session
    session_to_nwb(
        nwbfile_path=config["nwbfile_path"][row_index],
        ecephys_recording_folder_path=config["ecephys_folder_path"][row_index],
        plexon_file_path=config["plexon_file_path"][row_index],
        group_mat_file_path=config["group_mat_file_path"][row_index],
        events_file_path=config["events_mat_file_path"][row_index],
        sleap_file_path=config["sleap_file_path"][row_index],
        video_file_path=config["video_file_path"][row_index],
        subject_metadata=subject_metadata,
        stub_test=stub_test,
    )
