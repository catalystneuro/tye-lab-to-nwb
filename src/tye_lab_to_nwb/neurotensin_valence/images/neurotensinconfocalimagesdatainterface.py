import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
from hdmf.backends.hdf5 import H5DataIO
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.tools.nwb_helpers import make_or_load_nwbfile
from neuroconv.utils import FilePathType, dict_deep_update
from oiffile import OifFile, SettingsFile
from pynwb import NWBFile
from pynwb.base import Images
from pynwb.image import GrayscaleImage
from tifffile import tifffile


class NeurotensinConfocalImagesInterface(BaseDataInterface):
    """Primary interface for converting confocal images for the Neurotensin experiment."""

    def __init__(
        self,
        file_path: FilePathType,
        composite_tif_file_path: Optional[FilePathType] = None,
        verbose: bool = True,
    ):
        """
        Interface for converting confocal images from Olympus FluoView.

        Parameters
        ----------
        file_path : FilePathType
            path to the Olympus Image File (.OIF).
        composite_tif_file_path: FilePathType, optional
            path to the aggregated confocal images in TIF format.
        verbose: bool, default: True
            controls verbosity.
        """
        self.verbose = verbose
        self.oif = OifFile(file_path)
        self.composite_images = None
        if composite_tif_file_path:
            self.composite_images = tifffile.memmap(composite_tif_file_path, mode="r")

        super().__init__(file_path=file_path)

    def get_metadata(self) -> dict:
        metadata = super().get_metadata()

        metadata_from_oif_file = dict()
        settings = self.oif.filesystem.settings

        # Add session_start_time
        if "ImageCaputreDate" in settings["Acquisition Parameters Common"]:
            session_start_time = settings["Acquisition Parameters Common"]["ImageCaputreDate"]
            metadata["NWBFile"].update(session_start_time=datetime.fromisoformat(session_start_time))

        image_file_name = settings.name  # 'H28PVT_40x.oif'
        file_name_regex_result = re.search("([a-zA-Z]+\d+)([^_]+)", image_file_name)
        location = None
        if file_name_regex_result is not None:
            subject_id, location = re.search("([a-zA-Z]+\d+)([^_]+)", image_file_name).groups()
            metadata_from_oif_file["Subject"] = dict(subject_id=subject_id)

        software_name = settings["Version Info"]["SystemName"]  # 'FLUOVIEW FV1000'
        software_version = settings["Version Info"]["FileVersion"]  # '1.2.6.0'

        images_description = (
            f"The confocal images from {software_name} version {software_version} extracted from {image_file_name}."
        )
        if location:
            images_description = f"The {location} confocal images from {software_name} version {software_version} extracted from {image_file_name}."
        metadata_from_oif_file["Images"] = dict(
            name=self.oif.filesystem.name,
            description=images_description,
        )

        # Add metadata for images
        images_metadata = []
        for image_file_ind, image_file_name in enumerate(self.oif.series[0].files):
            image_settings_file_name = Path(image_file_name).with_suffix(".pty")
            image_settings_file_path = Path(self.source_data["file_path"]).parent / image_settings_file_name

            channel_num = self.oif.series[0].indices[image_file_ind][0]
            depth_num = self.oif.series[0].indices[image_file_ind][1]
            image_name = f"GrayScaleImage{channel_num + 1}Depth{depth_num + 1}"
            image_description = "The image intensity"
            if location:
                image_description += f" from {location} region"
            if image_settings_file_path.is_file():
                image_settings = SettingsFile(image_settings_file_path)
                depth = None
                if "Axis 3 Parameters" in image_settings:
                    if "AbsPositionValue" in image_settings["Axis 3 Parameters"]:
                        depth = float(image_settings["Axis 3 Parameters"]["AbsPositionValue"])
                        if "AbsPositionUnitName" in image_settings["Axis 3 Parameters"]:
                            if image_settings["Axis 3 Parameters"]["AbsPositionUnitName"] == "nm":
                                depth /= 1e9
                if depth:
                    image_description += f" at {depth} meters depth."
            images_metadata.append(dict(name=image_name, description=image_description))

        # Add metadata for composite images
        if self.composite_images is not None:
            for channel_num in range(self.composite_images.shape[0]):
                image_name = f"GrayScaleImage{channel_num + 1}Composite"
                image_description = "The image intensity aggregated over depth"
                if location:
                    image_description += f" from {location} region."
                images_metadata.append(dict(name=image_name, description=image_description))

        metadata_from_oif_file["Images"].update(images=images_metadata)
        metadata = dict_deep_update(metadata, metadata_from_oif_file)
        return metadata

    def add_to_nwbfile(
        self,
        nwbfile: NWBFile,
        metadata: Optional[dict] = None,
        conversion_options: Optional[dict] = None,
        overwrite: bool = False,
    ):
        images = Images(name=metadata["Images"]["name"], description=metadata["Images"]["description"])
        file_list = list(self.oif.series[0])

        for file_ind, file in enumerate(file_list):
            image = self.oif.series[0].imread(file)
            image_metadata = metadata["Images"]["images"][file_ind]

            images.add_image(
                GrayscaleImage(
                    name=image_metadata["name"],
                    data=H5DataIO(image.T, compression=True),
                    description=image_metadata["description"],
                )
            )

        # Add composite images
        if self.composite_images is not None:
            for image_ind in range(self.composite_images.shape[0]):
                image_metadata = metadata["Images"]["images"][len(file_list) + image_ind]
                images.add_image(
                    GrayscaleImage(
                        name=image_metadata["name"],
                        data=H5DataIO(self.composite_images[image_ind].T, compression=True),
                        description=image_metadata["description"],
                    )
                )

        nwbfile.add_acquisition(images)
