from neuroconv.utils import FilePathType
from pymatreader import read_mat


def load_timestamps_from_mat(file_path: FilePathType):
    mat_file = read_mat(str(file_path))
    assert "timestampsMsAllCumul" in mat_file, f"Unable to find the expected 'timestampsMsAllCumul' in {file_path}"
    return mat_file["timestampsMsAllCumul"]
