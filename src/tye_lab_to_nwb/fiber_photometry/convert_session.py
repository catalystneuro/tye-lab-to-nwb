from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4
from zoneinfo import ZoneInfo

from dateutil import tz
from dateutil.parser import parse

from neuroconv.utils import FilePathType, load_dict_from_file, dict_deep_update
from nwbinspector import inspect_nwbfile
from nwbinspector.inspector_tools import save_report, format_messages

from tye_lab_to_nwb.fiber_photometry import FiberPhotometryInterface


def session_to_nwb(
    nwbfile_path: FilePathType,
    data_file_path: FilePathType,
    session_start_time: str,
    subject_metadata: Optional[dict] = None,
):
    """
    Converts a single session to NWB.

    Parameters
    ----------
    nwbfile_path : FilePathType
        The file path to the NWB file that will be created.
    data_file_path: FilePathType
        The path that points to the .csv file containing the photometry intensity values.
    session_start_time: str
        The recording start time for the photometry session in YYYY-MM-DDTHH:MM:SS format (e.g. 2023-08-21T15:30:00).
    """
    nwbfile_path = Path(nwbfile_path)

    # Initalize interface with photometry source data
    interface = FiberPhotometryInterface(file_path=str(data_file_path))
    # Update metadata from interface
    metadata = interface.get_metadata()

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "metadata" / "general_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    if subject_metadata:
        metadata = dict_deep_update(metadata, dict(Subject=subject_metadata))

    # For data provenance we can add the time zone information to the conversion if missing
    if "session_start_time" not in metadata["NWBFile"]:
        if not session_start_time:
            raise ValueError(
                "The start time of the photometry session must be provided. "
                "Use the 'session_start_time' keyword argument to provide in YYYY-MM-DDTHH:MM:SS format (e.g. 2023-08-21T15:30:00)."
            )
        session_start_time_dt = parse(session_start_time)
        metadata["NWBFile"].update(session_start_time=session_start_time_dt)

    tzinfo = tz.gettz("US/Pacific")
    metadata["NWBFile"].update(session_start_time=metadata["NWBFile"]["session_start_time"].replace(tzinfo=tzinfo))

    if "session_id" not in metadata["NWBFile"]:
        metadata["NWBFile"].update(session_id=nwbfile_path.stem)

    try:
        interface.run_conversion(nwbfile_path=str(nwbfile_path), metadata=metadata, overwrite=True)

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
    # Parameters for conversion
    photometry_file_path = Path("/Volumes/t7-ssd/Hao_NWB/recording/Photometry_data0.csv")

    # The file path where the NWB file will be created.
    nwbfile_path = Path("/Volumes/t7-ssd/Hao_NWB/nwbfiles/photometry.nwb")

    # The recording start time for the photometry session has to be provided manually
    # in YYYY-MM-DDTHH:MM:SS format (e.g. 2023-08-21T15:30:00).
    session_start_time = "2023-08-21T15:30:00"

    # Provide the metadata for the subject ("U" is for unknown, "M" is for male, "F" is for female)
    subject_metadata = dict(subject_id="H28", sex="U")

    session_to_nwb(
        nwbfile_path=nwbfile_path,
        data_file_path=photometry_file_path,
        session_start_time=session_start_time,
        subject_metadata=subject_metadata,
    )
