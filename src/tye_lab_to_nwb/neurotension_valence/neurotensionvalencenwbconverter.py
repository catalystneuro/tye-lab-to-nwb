"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter
from neuroconv.datainterfaces import OpenEphysRecordingInterface


class NeurotensionValenceNWBConverter(NWBConverter):
    """Primary conversion class for the Neurotension valence experiment."""

    data_interface_classes = dict(
        Recording=OpenEphysRecordingInterface,
    )
