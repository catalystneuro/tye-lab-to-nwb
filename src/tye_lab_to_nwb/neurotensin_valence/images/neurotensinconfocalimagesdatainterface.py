import re
from datetime import datetime
from typing import Optional

import numpy as np
from hdmf.backends.hdf5 import H5DataIO
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.tools.nwb_helpers import make_or_load_nwbfile
from neuroconv.utils import FilePathType, dict_deep_update
from oiffile import OifFile
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
        composite_tif_file_path: FilePathType
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
        session_start_time = settings["Acquisition Parameters Common"]["ImageCaputreDate"]
        metadata["NWBFile"].update(session_start_time=datetime.fromisoformat(session_start_time))

        image_file_name = settings.name  # 'H28PVT_40x.oif'
        file_name_regex_result = re.search("([a-zA-Z]+\d+)([^_]+)", image_file_name)
        if file_name_regex_result is not None:
            subject_id, location = re.search("([a-zA-Z]+\d+)([^_]+)", image_file_name).groups()
            metadata_from_oif_file["Subject"] = dict(subject_id=subject_id)

        software_name = settings["Version Info"]["SystemName"]  # 'FLUOVIEW FV1000'
        software_version = settings["Version Info"]["FileVersion"]  # '1.2.6.0'
        # num_axis = settings["Axis Parameter Common"]["AxisCount"]  # 4
        # axis_order = self.oif.axes  # 'ZCYX' depth, ch, width, height

        depth_settings = settings["Axis 3 Parameters Common"]
        depth_range = []
        if all([pos in depth_settings for pos in ["StartPosition", "EndPosition", "Interval"]]):
            start = depth_settings["StartPosition"]
            stop = depth_settings["EndPosition"]
            step = depth_settings["Interval"]
            if start > stop:
                step = -step

            depth_range = np.arange(start, stop + step, step)
            if "UnitName" in depth_settings:
                if depth_settings["UnitName"] == "nm":
                    depth_range /= 1e9  # nm to m

        metadata_from_oif_file["Images"] = dict(
            name=self.oif.filesystem.name,
            description=f"The {location} confocal images from {software_name} version {software_version} extracted from {image_file_name}.",
        )

        images_metadata = []
        num_depths = len(set([indices[1] for indices in self.oif.series[0].indices]))
        for channel_num, depth_num in self.oif.series[0].indices:
            image_name = f"GrayScaleImage{channel_num+1}Depth{depth_num+1}"
            image_description = f"The image intensity from {location} region"
            if len(depth_range) == num_depths:
                image_description += f" at {depth_range[depth_num]} meters depth."
            images_metadata.append(dict(name=image_name, description=image_description))

        # Add metadata for composite images
        if self.composite_images is not None:
            for channel_num in range(self.composite_images.shape[0]):
                image_name = f"GrayScaleImage{channel_num + 1}Composite"
                image_description = f"The image intensity from {location} region aggregated over depth."
                images_metadata.append(dict(name=image_name, description=image_description))

        metadata_from_oif_file["Images"].update(images=images_metadata)
        metadata = dict_deep_update(metadata, metadata_from_oif_file)
        return metadata

    def align_timestamps(self, aligned_timestamps: np.ndarray):
        pass

    def get_original_timestamps(self) -> np.ndarray:
        pass

    def get_timestamps(self) -> np.ndarray:
        pass

    def run_conversion(
        self,
        nwbfile_path: Optional[str] = None,
        nwbfile: Optional[NWBFile] = None,
        metadata: Optional[dict] = None,
        conversion_options: Optional[dict] = None,
        overwrite: bool = False,
    ):
        with make_or_load_nwbfile(
            nwbfile_path=nwbfile_path, nwbfile=nwbfile, metadata=metadata, overwrite=overwrite, verbose=self.verbose
        ) as nwbfile_out:
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

            nwbfile_out.add_acquisition(images)
