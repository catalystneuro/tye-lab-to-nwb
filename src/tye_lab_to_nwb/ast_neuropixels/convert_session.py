import traceback
from pathlib import Path
from typing import Optional, Dict
from warnings import warn

from nwbinspector import inspect_nwbfile
from nwbinspector.inspector_tools import format_messages, save_report

from neuroconv.utils import (
    FilePathType,
    FolderPathType,
    load_dict_from_file,
    dict_deep_update,
    OptionalFolderPathType,
    OptionalFilePathType,
)
from tye_lab_to_nwb.ast_neuropixels import AStNeuroPixelsNNWBConverter
from tye_lab_to_nwb.tools import read_session_config


def session_to_nwb(
    nwbfile_path: FilePathType,
    neuropixels_file_path: FolderPathType,
    phy_sorting_folder_path: OptionalFolderPathType,
    histology_image_file_path: OptionalFilePathType,
    subject_metadata: Optional[Dict[str, str]] = None,
    stub_test: Optional[bool] = False,
):
    """
    Converts a single session to NWB.

    Parameters
    ----------
    nwbfile_path : FilePathType
        The file path to the NWB file that will be created.
    neuropixels_file_path: FilePathType
        The path that points the raw Neuropixels .ap.bin file.
    phy_sorting_folder_path: FolderPathType, optional
        The path that points to the folder where the Phy sorting output files are located.
    histology_image_file_path: FilePathType, optional
        The path that points to the TIF image file showing where the probes were inserted.
    subject_metadata: dict, optional
        The optional metadata for the experimental subject.
    stub_test: bool, optional
        For testing purposes, when stub_test=True only writes a subset of ecephys data.
        Default is to write the whole ecephys recording to the file.
    """

    source_data = dict()
    conversion_options = dict()

    # Add Recording
    spike_glx_ap_bin_file_path = Path(neuropixels_file_path)
    assert "ap.bin" in spike_glx_ap_bin_file_path.name, "The 'neuropixels_file_path' should point to an 'ap.bin' file."

    spike_glx_lf_bin_file_path = str(spike_glx_ap_bin_file_path).replace("ap", "lf")
    assert Path(spike_glx_lf_bin_file_path).is_file(), f"The 'lf.bin' file is missing from {neuropixels_file_path}."

    source_data.update(
        dict(
            RecordingAP=dict(file_path=str(spike_glx_ap_bin_file_path)),
            RecordingLF=dict(file_path=str(spike_glx_lf_bin_file_path)),
        )
    )
    conversion_options.update(
        dict(
            RecordingAP=dict(stub_test=stub_test),
            RecordingLF=dict(stub_test=stub_test),
        )
    )

    # Add sorting
    if phy_sorting_folder_path:
        source_data.update(dict(Sorting=dict(folder_path=str(phy_sorting_folder_path))))
        conversion_options.update(dict(Sorting=dict(stub_test=stub_test)))

    if histology_image_file_path:
        source_data.update(dict(Image=dict(file_path=str(histology_image_file_path))))

    converter = AStNeuroPixelsNNWBConverter(source_data=source_data)

    # Add datetime to conversion
    metadata = converter.get_metadata()

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "metadata" / "general_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    if subject_metadata:
        metadata = dict_deep_update(metadata, dict(Subject=subject_metadata))

    if "session_id" not in metadata["NWBFile"]:
        ecephys_folder_name = spike_glx_ap_bin_file_path.parent.name
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
    # The path to the Excel (.xlsx) file that contains the file paths for each data stream.
    # The number of rows in the file corresponds to the number of sessions that can be converted.
    excel_file_path = Path("/Volumes/t7-ssd/Raw_NPX/session_config.xlsx")
    config = read_session_config(excel_file_path=excel_file_path)
    # Choose which session will be converted by specifying the index of the row
    row_index = 0

    # Add subject metadata (optional)
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
        neuropixels_file_path=config["neuropixels_file_path"][row_index],
        phy_sorting_folder_path=config["phy_folder_path"][row_index],
        histology_image_file_path=config["histology_image_file_path"][row_index],
        subject_metadata=subject_metadata,
        stub_test=stub_test,
    )
