from neuroconv import NWBConverter
from neuroconv.datainterfaces import OpenEphysRecordingInterface, PlexonSortingInterface
from tye_lab_to_nwb.neurotensin_valence.behavior import NeurotensinEventsInterface


class AStEcephysNWBConverter(NWBConverter):
    """Primary conversion class for the ASt electrophysiology dataset."""

    data_interface_classes = dict(
        Events=NeurotensinEventsInterface,
        Recording=OpenEphysRecordingInterface,
        Sorting=PlexonSortingInterface,
    )
