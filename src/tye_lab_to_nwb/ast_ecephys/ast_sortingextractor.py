from collections import defaultdict
from typing import Optional, List

import numpy as np
from scipy.io import loadmat
from spikeinterface import BaseSorting, BaseSortingSegment

from neuroconv.utils import FilePathType


class AStSortingExtractor(BaseSorting):
    extractor_name = "AStSorting"
    installed = True
    mode = "file"
    installation_mesg = ""
    name = "astsorting"

    def __init__(self, file_path: FilePathType):
        """
        Parameters
        ----------
        file_path : FilePathType
            The file path to the MAT file containing the clustered spike times.
        """

        mat = loadmat(file_path, squeeze_me=True)
        assert "u" in mat, f"The 'u' structure is missing from '{file_path}'."
        self._units_data = mat["u"]

        unit_ids = self._filter_units()
        assert unit_ids, "All units were filtered out, cannot proceed."
        spike_times = self._units_data["spikeTimes"].item()
        spike_times = spike_times[unit_ids]

        all_unit_properties = defaultdict(list)
        metric_key_to_property_name = dict(
            unitName="unit_name",
            peakMin="minimum_amplitude",
            peakMax="maximum_amplitude",
            nSpikes="spike_count",
            qualManual="quality_score",
        )
        for metric_key, property_name in metric_key_to_property_name.items():
            metric = self._units_data[metric_key].item()[unit_ids]
            all_unit_properties[property_name].extend(list(metric))

        assert "info" in mat, f"The 'info' structure is missing from '{file_path}'."
        self._header = mat["info"]["header"].item()
        sampling_frequency = float(self._header["sampleRate"].item())
        BaseSorting.__init__(self, sampling_frequency=sampling_frequency, unit_ids=list(np.arange(len(unit_ids))))
        sorting_segment = AStSortingSegment(
            sampling_frequency=sampling_frequency,
            spike_times=spike_times,
        )
        self.add_sorting_segment(sorting_segment)

        for property_name, values in all_unit_properties.items():
            self.set_property(key=property_name, values=values)

    def _filter_units(self) -> List[int]:
        # remove duplicated units
        # discard units where the value in this array equals to 1
        is_duplicate_units = self._units_data["xCorrDisc_wq"].item()
        # discard low quality units
        # Any units with quality 3 or greater are included
        unit_quality_scores = self._units_data["qualManual"].item()
        # discard low-firing units with less than 1000 total spikes
        unit_num_spikes = self._units_data["nSpikes"].item()
        units_logical_filter = (is_duplicate_units == 0) & (unit_quality_scores >= 3) & (unit_num_spikes >= 1000)

        return list(np.where(units_logical_filter)[0])


class AStSortingSegment(BaseSortingSegment):
    def __init__(self, sampling_frequency: float, spike_times: np.ndarray):
        BaseSortingSegment.__init__(self)
        self._spike_times = spike_times
        self._sampling_frequency = sampling_frequency

    def get_unit_spike_train(
        self,
        unit_id: int,
        start_frame: Optional[int] = None,
        end_frame: Optional[int] = None,
    ) -> np.ndarray:
        times = self._spike_times[unit_id]
        frames = (times * self._sampling_frequency).astype(int)
        if start_frame is not None:
            frames = frames[frames >= start_frame]
        if end_frame is not None:
            frames = frames[frames < end_frame]
        return frames
