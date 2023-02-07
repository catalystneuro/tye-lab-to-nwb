"""Primary script to run to convert an entire session for of data using the NWBConverter."""
from pathlib import Path
import datetime
from zoneinfo import ZoneInfo

from neuroconv.utils import load_dict_from_file, dict_deep_update, FilePathType

from tye_lab_to_nwb.neurotensin_valence import NeurotensinValenceNWBConverter


def session_to_nwb(
    data_dir_path: FilePathType,
    pose_estimation_file_path: FilePathType,
    pose_estimation_config_file_path: FilePathType,
    original_video_file_path: FilePathType,
    labeled_video_file_path: FilePathType,
    output_dir_path: FilePathType,
    stub_test: bool = False,
):
    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    source_data = dict()
    conversion_options = dict()

    # Add Recording
    source_data.update(dict(Recording=dict()))
    conversion_options.update(dict(Recording=dict()))

    # Add LFP
    source_data.update(dict(LFP=dict()))
    conversion_options.update(dict(LFP=dict()))

    # Add Sorting
    source_data.update(dict(Sorting=dict()))
    conversion_options.update(dict(Sorting=dict()))

    # Add Behavior
    source_data.update(
        dict(
            Behavior=dict(
                file_path=str(pose_estimation_file_path),
                config_file_path=str(pose_estimation_config_file_path),
            )
        )
    )

    conversion_options.update(
        dict(
            Behavior=dict(
                original_video_file_path=str(original_video_file_path),
                labeled_video_file_path=str(labeled_video_file_path),
            )
        )
    )

    converter = NeurotensinValenceNWBConverter(source_data=source_data)

    # Add datetime to conversion
    metadata = converter.get_metadata()
    date = datetime.datetime(year=2020, month=1, day=1, tzinfo=ZoneInfo("US/Eastern"))  # TO-DO: Get this from author
    metadata["NWBFile"]["session_start_time"] = date

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "neurotensin_valence_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    session_id = "subject_identifier_usually"
    if "session_id" in metadata["NWBFile"]:
        session_id = metadata["NWBFile"]["session_id"]
    nwbfile_path = output_dir_path / f"{session_id}.nwb"

    # Run conversion
    converter.run_conversion(metadata=metadata, nwbfile_path=nwbfile_path, conversion_options=conversion_options)


if __name__ == "__main__":
    # Parameters for conversion
    data_dir_path = Path("/Directory/With/Raw/Formats/")

    # Parameters for pose estimation data
    pose_estimation_file_path = Path(
        "Hao_NWB/behavior/freezing_DLC/28_Disc4DLC_resnet50_Hao_MedPC_ephysFeb9shuffle1_800000.csv"
    )
    pose_estimation_config_file_path = Path(
        "Hao_NWB/behavior/freezing_DLC/H028Disc4DLC_resnet50_Hao_MedPC_ephysFeb9shuffle1_800000includingmetadata.pickle"
    )
    raw_video_file_path = Path("H028Disc4.mkv")
    labeled_video_file_path = Path("H028Disc4DLC_resnet50_Hao_MedPC_ephysFeb9shuffle1_800000_labeled.mp4")

    output_dir_path = Path("Hao_NWB/nwbfiles")
    stub_test = False

    session_to_nwb(
        data_dir_path=data_dir_path,
        pose_estimation_file_path=pose_estimation_file_path,
        pose_estimation_config_file_path=pose_estimation_config_file_path,
        original_video_file_path=raw_video_file_path,
        labeled_video_file_path=labeled_video_file_path,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
    )
