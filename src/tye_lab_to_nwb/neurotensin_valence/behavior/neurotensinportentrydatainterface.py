from datetime import datetime
import re
from typing import Optional

import pandas as pd

from neuroconv.datainterfaces.text.timeintervalsinterface import TimeIntervalsInterface
from neuroconv.utils import FilePathType


class NeurotensinPortEntryInterface(TimeIntervalsInterface):
    """The interface for converting the port entry times for the Neurotensin experiment."""

    def __init__(
        self,
        file_path: FilePathType,
        read_kwargs: Optional[dict] = None,
        verbose: bool = True,
    ):
        """
        Parameters
        ----------
        file_path : FilePath
            The file path to the .txt file that contains the port enry and exit times.
        read_kwargs : dict, optional
        verbose : bool, default: True
        """
        super().__init__(file_path=file_path, verbose=verbose, read_kwargs=read_kwargs)

    def _read_file(self, file_path: FilePathType, **read_kwargs):
        dataframe = pd.DataFrame()
        with open(file_path, "r") as f:
            port_data = f.read()
            port_split_data = re.split(r"^([A-Z]:)", port_data, flags=re.MULTILINE)

        port_entry_index = port_split_data.index("P:")
        dataframe["start_time"] = port_split_data[port_entry_index + 1].strip().split("\n")

        port_exit_index = port_split_data.index("N:")
        dataframe["stop_time"] = port_split_data[port_exit_index + 1].strip().split("\n")
        dataframe = dataframe.applymap(lambda x: x.split(":")[1].strip())
        dataframe = dataframe.astype(float)

        return dataframe

    def get_metadata(self):
        metadata = super().get_metadata()

        metadata["TimeIntervals"]["trials"].update(
            table_description=f"The port entry and and port exit times from {self.source_data['file_path']}.",
        )
        with open(self.source_data["file_path"], "r") as f:
            port_data = f.read()
            port_header_data = re.split(r"^([A-Z]:)", port_data, flags=re.MULTILINE)[0]

        sections = [header.split(":", 1)[-1] for header in port_header_data.split("\n")]
        # add subject_id to nwb
        metadata["Subject"] = dict(subject_id=sections[6].strip())

        # add session_id to nwb
        metadata["NWBFile"] = dict(session_id=sections[7].strip())

        # add session_start_time to nwb
        start_date = sections[4].strip()
        start_date += sections[10]
        date = datetime.strptime(start_date, "%m/%d/%y %H:%M:%S")

        # TODO: synchronize with ecephys times
        metadata["NWBFile"].update(session_start_time=date)

        return metadata
