from pathlib import Path
from typing import Optional

import numpy as np
from pynwb import NWBFile

from neuroconv import NWBConverter
from neuroconv.datainterfaces import (
    SpikeGLXRecordingInterface,
    PhySortingInterface,
)
from neuroconv.utils import DeepDict, load_dict_from_file, dict_deep_update
from tye_lab_to_nwb.ast_neuropixels.ast_neuropixelshistologyinterface import AStNeuropixelsHistologyInterface


class AStNeuroPixelsNNWBConverter(NWBConverter):
    """Primary conversion class for the ASt Neuropixels dataset."""

    data_interface_classes = dict(
        RecordingAP=SpikeGLXRecordingInterface,
        RecordingLF=SpikeGLXRecordingInterface,
        Sorting=PhySortingInterface,
        Image=AStNeuropixelsHistologyInterface,
    )

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()
        # Update unit property names and add descriptions from the yaml file.
        ecephys_metadata_path = Path(__file__).parent / "metadata" / "ecephys.yaml"
        ecephys_metadata = load_dict_from_file(ecephys_metadata_path)
        metadata = dict_deep_update(metadata, ecephys_metadata)
        return metadata

    def run_conversion(
        self,
        nwbfile_path: Optional[str] = None,
        nwbfile: Optional[NWBFile] = None,
        metadata: Optional[dict] = None,
        overwrite: bool = False,
        conversion_options: Optional[dict] = None,
    ):
        recording_interfaces = ["RecordingAP", "RecordingLF"]
        for recording_interface_name in recording_interfaces:
            recording_interface = self.data_interface_objects[recording_interface_name]
            recording_extractor = recording_interface.recording_extractor
            num_channels = recording_extractor.get_num_channels()
            recording_extractor.set_property(
                # SpikeInterface refers to this as 'brain_area', NeuroConv remaps to 'location'
                key="brain_area",
                values=["ASt"] * num_channels,
            )

        sorting_interface = self.data_interface_objects["Sorting"]
        sorting_extractor = sorting_interface.sorting_extractor
        # Rename unit properties to have descriptive names
        unit_properties_mapping = dict(
            amplitude="spike_amplitudes",
            ContamPct="contamination",
            contam_rate="contamination_rate",
            KSLabel="label",
            PT_ratio="pt_ratio",
            quality="unit_quality",
            halfwidth="halfwidth_amplitude",
            isi_viol="isi_violation",
            num_viol="isi_violation_count",
            max_drift="maximum_drift",
            n_spikes="spike_count",
            depth="probe_depth",
            spread="spread_of_unit_in_probe_depth",
        )
        unit_properties = {
            unit_properties_mapping.get(key, key): value for key, value in sorting_extractor._properties.items()
        }

        # "fr" and "firing_rate" is duplicated
        unit_properties.pop("fr", None)
        # "ch" and "peak_channel" is duplicated, they mean neuropixel channel (not a unit property)
        unit_properties.pop("ch", None)
        unit_properties.pop("peak_channel", None)

        unit_properties.pop("sh", None)

        # "epoch_name" and "epoch_name_quality_metrics" and "epoch_name_waveform_metrics" are duplicated
        unit_properties.pop("epoch_name_quality_metrics", None)
        unit_properties.pop("epoch_name_waveform_metrics", None)

        sorting_extractor._properties = unit_properties

        remove_unit_ids = np.where(unit_properties["unit_quality"] == "noise")
        sorting_interface.sorting_extractor = sorting_extractor.remove_units(remove_unit_ids)

        super().run_conversion(
            nwbfile_path=nwbfile_path,
            nwbfile=nwbfile,
            metadata=metadata,
            conversion_options=conversion_options,
        )
