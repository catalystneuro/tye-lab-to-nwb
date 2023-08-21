# Conversion notes

# Run conversion for multiple sessions in parallel

The `neurotensin_valence_convert_all_sessions.py` conversion script takes an Excel (.xlsx) file as an input
which contain all the necessary information to convert each session. The number of rows in the file
correspond to the number of sessions that will be converted.

The columns in the selected Excel (.xlsx) file should be named as:
- "`ecephys_folder_path`" : The path that points to the folder where the OpenEphys (.continuous) files are located.
- "`nwbfile_path`": The file path where the NWB file will be created. (e.g. "test.nwb")
- "`plexon_file_path`": The path that points to the Plexon file
- "`events_mat_file_path`": The file path that points to the events.mat file
- "`pose_estimation_csv_file_path`": The file path that points to the DLC output (.CSV file)
- "`pose_estimation_pickle_file_path`": The file path that points to the DLC configuration file (.pickle file), optional
- "`pose_estimation_sampling_rate`": If the pickle file is not available the sampling rate in units of Hz (e.g. 30.0) for the behavior data must be provided.
- "`session_start_time`": For sessions where only the pose estimation data is available the start time of the session must be provided. The session_start_time in YYYY-MM-DDTHH:MM:SS format (e.g. 2023-08-21T15:30:00).
- "`behavior_movie_file_path`": The file path that points to the behavior movie file
- "`behavior_labeled_movie_file_path`": The file path that points to the labeled behavior movie file
- "`confocal_images_oif_file_path`": The file path to the Olympus Image File (.oif)
- "`confocal_images_composite_tif_file_path`": The file path to the aggregated confocal images in TIF format.

Example with subject metadata columns (e.g. `subject_id`, `age`, `sex`, `genotype`, `strain`)

| ecephys_folder_path               | plexon_file_path                                               | events_mat_file_path                                       | pose_estimation_csv_file_path                             | pose_estimation_pickle_file_path                        | confocal_images_oif_file_path | confocal_images_composite_tif_file_path | behavior_movie_file_path | behavior_labeled_movie_file_path | nwbfile_path | subject_id | age | sex | genotype | strain | session_start_time      | pose_estimation_sampling_rate |
|-----------------------------------| -------------------------------------------------------------- | ---------------------------------------------------------- | -------------------------------------------------------- | ----------------------------------------------------- | ---------------------------- | -------------------------------------- | ------------------------ | ---------------------------------- | ------------ | ---------- | --- | --- | -------- | ------ | ------------------------ | ---------------------------- |
| H28_2020-02-19_14-27-39_Disc3_20k | H28_2020-02-19_14-27-39_Disc3_20k/0028_20200221_20k.plx       | H28_2020-02-19_14-27-39_Disc3_20k/0028_20200221_20k_events.mat | 28_Disc4DLC_resnet50_Hao_MedPC_ephysFeb9shuffle1_800000.csv | H028Disc4DLC_resnet50_Hao_MedPC_ephysFeb9shuffle1_800000includingmetadata.pickle | H31PVT_40x.oif               | H31_MAX_Composite.tif                | H028Disc4.mkv            |                                    | H28_Disc4.nwb | H28        | P7D | M   |          |        |                        |                              |
|                                   |                                                                |                                                              | 32_Disc4DLC_resnet50_Hao_MedPC_ephysFeb11shuffle1_800000.csv |                                                                   |                            |                                      |                        |                                  | H32_Disc4.nwb | H32        | P8D | M   |          |        | 2023-08-21T15:30:00     | 30.0                         |



```python
from tye_lab_to_nwb.neurotensin_valence.neurotensin_valence_convert_all_sessions import parallel_convert_sessions

# The file path to the conversion settings for each session
excel_file_path = "/Volumes/t7-ssd/Hao_NWB/session_config.xlsx"

parallel_convert_sessions(
    excel_file_path=excel_file_path,
    num_parallel_jobs=3,  # defines the number of sessions that will be converted in parallel.
)
```
