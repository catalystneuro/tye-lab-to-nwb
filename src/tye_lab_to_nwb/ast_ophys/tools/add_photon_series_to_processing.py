from copy import deepcopy
from typing import Optional

import numpy as np
from hdmf.backends.hdf5 import H5DataIO
from neuroconv.tools import get_module
from neuroconv.tools.roiextractors import add_imaging_plane
from neuroconv.tools.roiextractors.imagingextractordatachunkiterator import ImagingExtractorDataChunkIterator
from pynwb import NWBFile
from pynwb.ophys import OnePhotonSeries
from roiextractors import ImagingExtractor

from neuroconv.utils import calculate_regular_series_rate


def add_processed_one_photon_series(
    nwbfile: NWBFile,
    imaging: ImagingExtractor,
    timestamps: np.ndarray,
    photon_series_index: Optional[int] = 1,
    metadata: Optional[dict] = None,
):
    add_imaging_plane(nwbfile=nwbfile, metadata=metadata, imaging_plane_index=0)
    imaging_plane_name = metadata["Ophys"]["ImagingPlane"][0]["name"]
    imaging_plane = nwbfile.get_imaging_plane(imaging_plane_name)

    photon_series_kwargs = deepcopy(metadata["Ophys"]["OnePhotonSeries"][photon_series_index])
    photon_series_kwargs.update(
        imaging_plane=imaging_plane,
        # H5DataIO wrap should be eventually removed
        data=H5DataIO(data=ImagingExtractorDataChunkIterator(imaging_extractor=imaging), compression=True),
        dimension=imaging.get_image_size()[::-1],
        unit="n.a.",
    )

    rate = calculate_regular_series_rate(timestamps)
    if rate is not None:
        photon_series_kwargs.update(rate=rate, starting_time=timestamps[0])
    else:
        photon_series_kwargs.update(timestamps=H5DataIO(data=timestamps, compression=True))

    one_photon_series = OnePhotonSeries(**photon_series_kwargs)
    ophys = get_module(nwbfile=nwbfile, name="ophys", description="contains optical physiology processed data")
    ophys.add(one_photon_series)
