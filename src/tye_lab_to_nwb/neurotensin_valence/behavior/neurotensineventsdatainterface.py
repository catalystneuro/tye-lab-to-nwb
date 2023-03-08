from typing import Optional

import pandas as pd
from scipy.io import loadmat

from neuroconv.datainterfaces.text.timeintervalsinterface import TimeIntervalsInterface
from neuroconv.utils import FilePathType


class NeurotensinEventsInterface(TimeIntervalsInterface):
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
            The file path to the .mat file that contains the event onset and offset times.
        read_kwargs : dict, optional
        verbose : bool, default: True
        """
        super().__init__(file_path=file_path, verbose=verbose, read_kwargs=read_kwargs)

    def _read_file(self, file_path: FilePathType, **read_kwargs):
        mat = loadmat(file_path, struct_as_record=True, squeeze_me=True)
        assert "ev" in mat, "The events struct is not in the file."
        events = pd.DataFrame(mat["ev"])[["onset", "offset"]]
        events.index.name = "trial_type"
        events = events.reset_index()

        event_names_mapping = {
            0: "reward_stimulus_presentation",
            1: "phototagging",
            2: "shock_stimulus_presentation",
            3: "reward_delivery",
            4: "shock_relay",
            5: "port_entry",
            6: "neutral_stimulus_presentation",
            7: "session_start",
        }
        events["trial_type"] = events["trial_type"].map(event_names_mapping)

        # unpack list of lists in onset and offset columns
        events = events.explode(column=["onset", "offset"])

        # sort timestamps in ascending order
        events = events.sort_values(by="onset", ascending=True)

        # drop empty phototagging event
        events = events.dropna(axis=0)
        # drop session start cue
        events = events[events["trial_type"] != "session_start"]

        return events
