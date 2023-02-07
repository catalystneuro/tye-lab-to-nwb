"""Primary script to run to convert an entire session for of data using the NWBConverter."""
from pathlib import Path
import datetime
from zoneinfo import ZoneInfo

from neuroconv.utils import load_dict_from_file, dict_deep_update, FilePathType

from tye_lab_to_nwb.neurotensin_valence import NeurotensinValenceNWBConverter


def session_to_nwb(source_dir_path: FilePathType, nwbfile_dir_path: FilePathType, stub_test: bool = False):
    source_dir_path = Path(source_dir_path)
    nwbfile_dir_path = Path(nwbfile_dir_path)
    if stub_test:
        nwbfile_dir_path = nwbfile_dir_path / "nwb_stub"
    nwbfile_dir_path.mkdir(parents=True, exist_ok=True)

    session_id = "subject_identifier_usually"
    nwbfile_path = nwbfile_dir_path / f"{session_id}.nwb"

    source_data = dict()
    conversion_options = dict()

    # Add Recording
    source_data.update(dict(Recording=dict()))
    conversion_options.update(dict(Recording=dict()))

    # Add Behavior
    source_data.update(dict(Behavior=dict()))
    conversion_options.update(dict(Behavior=dict()))

    converter = NeurotensinValenceNWBConverter(source_data=source_data)

    # Add datetime to conversion
    metadata = converter.get_metadata()
    date = datetime.datetime(year=2020, month=1, day=1, tzinfo=ZoneInfo("US/Eastern"))  # TO-DO: Get this from author
    metadata["NWBFile"]["session_start_time"] = date

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    # Run conversion
    converter.run_conversion(metadata=metadata, nwbfile_path=nwbfile_path, conversion_options=conversion_options)


if __name__ == "__main__":
    # Parameters for conversion
    data_dir_path = Path("/Directory/With/Raw/Formats/")
    output_dir_path = Path("~/conversion_nwb/")
    stub_test = False

    session_to_nwb(
        source_dir_path=data_dir_path,
        nwbfile_dir_path=output_dir_path,
        stub_test=stub_test,
    )
