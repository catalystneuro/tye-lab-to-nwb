"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter
from neuroconv.datainterfaces import OpenEphysRecordingInterface

from tye_lab_to_nwb.neurotensin_valence import NeurotensinValenceBehaviorInterface


class NeurotensinValenceNWBConverter(NWBConverter):
    """Primary conversion class for the OpenEphys and behavior dataset."""

    data_interface_classes = dict(
        Recording=OpenEphysRecordingInterface,
        Behavior=NeurotensinValenceBehaviorInterface,
    )
