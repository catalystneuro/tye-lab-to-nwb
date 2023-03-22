from datetime import datetime
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from neuroconv.utils import FilePathType, load_dict_from_file, dict_deep_update

from tye_lab_to_nwb.fiber_photometry import FiberPhotometryInterface


def session_to_nwb(
    file_path: FilePathType,
    output_dir_path: FilePathType,
):
    # Initalize interface with photometry source data
    interface = FiberPhotometryInterface(file_path=str(file_path))
    # Update metadata from interface
    metadata = interface.get_metadata()

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "metadata" / "general_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    # Add datetime to conversion
    if "session_start_time" not in metadata["NWBFile"]:
        date = datetime(year=2020, month=1, day=1, tzinfo=ZoneInfo("US/Eastern"))  # TO-DO: Get this from author
        metadata["NWBFile"].update(session_start_time=date)
    # Generate subject identifier if missing from metadata
    subject_id = "1"
    if "subject_id" not in metadata["Subject"]:
        metadata["Subject"].update(subject_id=subject_id)
    session_id = str(uuid4())
    if "session_id" not in metadata["NWBFile"]:
        metadata["NWBFile"].update(session_id=session_id)

    output_dir_path = Path(output_dir_path) / f"sub-{metadata['Subject']['subject_id']}"
    output_dir_path.mkdir(parents=True, exist_ok=True)
    nwbfile_name = f"sub-{subject_id}_ses-{session_id}.nwb"
    nwbfile_path = output_dir_path / nwbfile_name

    interface.run_conversion(nwbfile_path=nwbfile_path, metadata=metadata)


if __name__ == "__main__":
    # Parameters for conversion
    photometry_file_path = Path("/Volumes/t7-ssd/Hao_NWB/recording/Photometry_data0.csv")
    output_dir_path = Path(
        "/Users/weian/Library/Mobile Documents/com~apple~CloudDocs/catalystneuro/tye-lab-to-nwb/204134"
    )

    session_to_nwb(
        file_path=photometry_file_path,
        output_dir_path=output_dir_path,
    )
