from typing import Optional

import pandas as pd
from hdmf.common import DynamicTableRegion
from ndx_events import AnnotatedEventsTable
from ndx_photometry import FibersTable, FiberPhotometry, ExcitationSourcesTable, PhotodetectorsTable, FluorophoresTable
from pynwb import NWBFile
from pynwb.ophys import RoiResponseSeries


def add_photometry(photometry_dataframe: pd.DataFrame, nwbfile: NWBFile, metadata: Optional[dict]):
    # Create the ExcitationSourcesTable that holds metadata for the LED sources
    excitation_sources_table = ExcitationSourcesTable(description="The metadata for the excitation sources.")
    for source_metadata in metadata["ExcitationSourcesTable"]:
        excitation_sources_table.add_row(
            peak_wavelength=source_metadata["peak_wavelength"],
            source_type=source_metadata["source_type"],
        )

    # Create the PhotodetectorsTable that holds metadata for the photodetector.
    photodetectors_table = PhotodetectorsTable(description=metadata["PhotodetectorsTable"]["description"])
    photodetectors_table.add_row(type=metadata["PhotodetectorsTable"]["type"])

    # Create the FluorophoresTable that holds metadata for the fluorophores.
    fluorophores_table = FluorophoresTable(description=metadata["FluorophoresTable"]["description"])

    fluorophores_table.add_row(
        label=metadata["FluorophoresTable"]["label"],
        location=metadata["FluorophoresTable"]["location"],
        coordinates=metadata["FluorophoresTable"]["coordinates"],
    )

    # Create the FibersTable that holds metadata for fibers
    fibers_table = FibersTable(description=metadata["FibersTable"]["description"])
    fiber_photometry = FiberPhotometry(
        fibers=fibers_table,
        excitation_sources=excitation_sources_table,
        photodetectors=photodetectors_table,
        fluorophores=fluorophores_table,
    )

    # Add the metadata tables to the metadata section
    nwbfile.add_lab_meta_data(fiber_photometry)

    # Add row for each fiber defined in metadata
    fibers_table.add_fiber(
        excitation_source=0,
        photodetector=0,
        fluorophores=[0],
        location=metadata["FibersTable"]["location"],
        notes=metadata["FibersTable"]["notes"],
    )

    # Create reference for fibers
    rois = DynamicTableRegion(
        name="rois",
        data=[0],
        description="source fibers",
        table=fibers_table,
    )
    # Create the RoiResponseSeries that holds the intensity values
    for photometry_metadata in metadata["RoiResponseSeries"]:
        column = photometry_metadata["region"]
        roi_response_series_name = photometry_metadata["name"]
        roi_response_series = RoiResponseSeries(
            name=roi_response_series_name,
            description=photometry_metadata["description"],
            data=photometry_dataframe[column].values,
            unit=photometry_metadata["unit"],
            timestamps=photometry_dataframe["Timestamp"].values,
            rois=rois,
        )

        nwbfile.add_acquisition(roi_response_series)


def add_events_from_photometry(photometry_dataframe: pd.DataFrame, nwbfile: NWBFile, metadata: Optional[dict]):
    annotated_events = AnnotatedEventsTable(
        name=metadata["Events"]["name"],
        description=metadata["Events"]["description"],
    )
    for event_num, event_label in metadata["Events"]["labels"].items():
        annotated_events.add_event_type(
            label=event_label,
            event_description=f"The times when the {event_label} was on.",
            event_times=photometry_dataframe.loc[photometry_dataframe["Flags"] == event_num, "Timestamp"].values,
        )

    nwbfile.add_acquisition(annotated_events)
