from neuroconv.datainterfaces.ecephys.basesortingextractorinterface import BaseSortingExtractorInterface
from neuroconv.utils import FilePathType
from tye_lab_to_nwb.ast_ecephys.ast_sortingextractor import AStSortingExtractor


class AstSortingInterface(BaseSortingExtractorInterface):
    Extractor = AStSortingExtractor

    def __init__(self, file_path: FilePathType, verbose: bool = True):
        """
        Parameters
        ----------
        file_path: FilePathType
            Path to the MAT file containing the spiking data.
        verbose: bool, default: True
            Allows verbosity.
        """
        super().__init__(file_path=file_path, verbose=verbose)
