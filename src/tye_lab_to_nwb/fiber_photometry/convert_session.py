from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from neuroconv.utils import FilePathType

from tye_lab_to_nwb.fiber_photometry import FiberPhotometryInterface


def session_to_nwb(
    file_path: FilePathType,
    output_dir_path: FilePathType,
    stub_test: bool = False,
):
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    interface = FiberPhotometryInterface(file_path=str(file_path))
    metadata = interface.get_metadata()

    nwbfile_path = output_dir_path / "fiber_photometry.nwb"

    # Add datetime to conversion
    date = datetime(year=2020, month=1, day=1, tzinfo=ZoneInfo("US/Eastern"))  # TO-DO: Get this from author
    metadata["NWBFile"]["session_start_time"] = date

    interface.run_conversion(nwbfile_path=nwbfile_path, metadata=metadata, stub_test=stub_test)


if __name__ == "__main__":
    # Parameters for conversion
    photometry_file_path = Path("/Volumes/t7-ssd/Hao_NWB/recording/Photometry_data0.csv")
    output_dir_path = Path("/Volumes/t7-ssd/Hao_NWB/nwbfiles")
    stub_test = False

    session_to_nwb(
        file_path=photometry_file_path,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
    )
