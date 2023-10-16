from typing import Optional

import tifffile
from hdmf.backends.hdf5 import H5DataIO
from neuroconv import BaseDataInterface
from neuroconv.utils import FilePathType
from pynwb import NWBFile
from pynwb.base import Images
from pynwb.image import RGBImage


class AStNeuropixelsHistologyInterface(BaseDataInterface):
    """Primary interface for converting the histology image for the Ephys Neuropixels dataset."""

    def __init__(
        self,
        file_path: FilePathType,
    ):
        """
        Interface for converting the histology image that shows where the Neuropixel probes were insterted.

        Parameters
        ----------
        file_path : FilePathType
            path to the TIF image file.
        """

        self._tif = tifffile.TiffFile(file_path)
        super().__init__(file_path=file_path)

    def get_metadata(self):
        metadata = super().get_metadata()

        metadata["Images"] = dict(
            name="NeuropixelsHistologyImages",
            description="The container for histology images showing where the Neuropixel probes were inserted.",
        )
        metadata["Images"].update(
            images=[
                dict(
                    name="HistologyImage",
                    description="The RGB image showing where the Neuropixel probes were inserted.",
                )
            ]
        )

        return metadata

    def add_to_nwbfile(
        self,
        nwbfile: Optional[NWBFile] = None,
        metadata: Optional[dict] = None,
        overwrite: bool = False,
        verbose: bool = False,
    ):
        images = Images(name=metadata["Images"]["name"], description=metadata["Images"]["description"])

        # loads as height by width and color dimension
        image_data = self._tif.asarray()
        # transpose to width by height and color (NWB convention)
        image_data = image_data.transpose((1, 0, 2))
        image_metadata = metadata["Images"]["images"][0]
        images.add_image(
            RGBImage(
                name=image_metadata["name"],
                data=H5DataIO(image_data, compression=True),
                description=image_metadata["description"],
            )
        )

        nwbfile.add_acquisition(images)
