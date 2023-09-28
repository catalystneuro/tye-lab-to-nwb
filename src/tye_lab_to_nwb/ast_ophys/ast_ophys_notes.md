# Conversion notes

`miniscope_folder_path`: The folder that contains the *raw* Miniscope data.
The main Miniscope folder is expected to contain both data streams organized as follows:
```
C6-J588_Disc5/ (Main Folder)
├── 15_03_28/ (Recording Timestamp)
│   ├── Miniscope/ (Microscope Video Stream)
│   │   ├── 0.avi (Microscope Video)
│   │   ├── metaData.json (Microscope Metadata)
│   │   └── timeStamps.csv (Microscope Timing)
│   ├── BehavCam_2/ (Behavioral Video Stream)
│   │   ├── 0.avi (Behavioral Video)
│   │   ├── metaData.json (Behavioral Camera Metadata)
│   │   └── timeStamps.csv (Behavioral Timing)
│   └── metaData.json (Recording Metadata, Start Time)
├── 15_06_28/ (Another Recording Timestamp)
│   ├── Miniscope/
│   ├── BehavCam_2/
│   └── metaData.json
└── 15_12_28/ (Yet Another Recording Timestamp)
```

`segmentation_mat_file_path`: The .mat file that holds the contents of the "neuron" struct.

To open `C6-J588_Disc5_msCamComb_MC_curated_20220605_1722.mat` in Python there is an extra step necessary.
Run this helper function (`save_neuron.m`) in MATLAB to load the file that was produced CNMF_E (also adding that folder to the path so MATLAB too can see the 'neuron' struct) and save it in a new file that can be read by Python:

```matlab
% This is a helper function for repacking a .mat file produced by CNMF_E
% The 'neuron' struct is a Matlab class called Sources2D, so they cannot be directly loaded into Python for further analysis.

function save_neuron(CNMF_E_folder_path, source_filepath, destination_filepath)

    % Add CNMF_E folder and its subfolders to MATLAB search path
    addpath(genpath(CNMF_E_folder_path));

    % Load the file
    load(source_filepath, 'neuron');

    neuron = struct(neuron);

    % Save the 'neuron' struct in v7 format
    save(destination_filepath, '-v7', '-struct', 'neuron');

end
```

# Run conversion for multiple sessions in parallel

The `convert_all_sessions.py` conversion script takes an Excel (.xlsx) file as an input
which contain all the necessary information to convert each session. The number of rows in the file
correspond to the number of sessions that will be converted.

The columns in the selected Excel (.xlsx) file should be named as:
- "`miniscope_folder_path`" : The path that points to the folder where the raw Miniscope data is located (see description about folder structure above).
- "`nwbfile_path`": The file path where the NWB file will be created. (e.g. "test.nwb")
- "`processed_miniscope_avi_file_path`": The file path that points to the concatenated and first frames deleted "ffd" Miniscope video (.avi).
- "`motion_corrected_mat_file_path`": The file path that points to the motion corrected Miniscope video (.mat).
  - "`timestamps_mat_file_path`": The file path that points to the MATLAB file that contains the Miniscope and trial timings.
        Required for the processed and motion corrected Miniscope data.
- "`reward_trials_indices`": The list of trials that correspond to the CS-Reward trials.
- "`segmentation_mat_file_path`": The file path that points to the MATLAB file containing the data structures from "neuron".
- "`session_start_time`": For sessions where the raw Miniscope data is not available the recording start time must be provided.
        The session_start_time should be in YYYY-MM-DDTHH:MM:SS format (e.g. 2023-08-21T15:30:00).

Example with subject metadata columns (e.g. `subject_id`, `age`, `sex`, `genotype`, `strain`)

| nwbfile_path      | miniscope_folder_path                   | processed_miniscope_avi_file_path | motion_corrected_mat_file_path | timestamps_mat_file_path | reward_trials_indices                                      | segmentation_mat_file_path | session_start_time      | subject_id | age | sex | genotype | strain   |
|-------------------|-----------------------------------------|----------------------------------|-------------------------------|-------------------------|-------------------------------------------------------------|----------------------------|-------------------------|------------|-----|-----|----------|----------|
| C6-J588-Disc5.nwb | /Volumes/t7-ssd/Miniscope/C6-J588_Disc5 | /Volumes/t7-ssd/Miniscope/C6-J588_Disc5_msCamAll_ffd.avi | /Volumes/t7-ssd/Miniscope/C6-J588_Disc5_msCamComb_MC.mat | /Volumes/t7-ssd/Miniscope/C6-J588_Disc5_timestampsAllCumulData.mat |                                             | /Volumes/t7-ssd/Miniscope/neuron.mat  | 2023-08-21T15:30:00 | test       | P7D | M   |          |          |
| test9.nwb         |                                         | /Volumes/t7-ssd/Miniscope/C6-J588_Disc5_msCamAll_ffd.avi | /Volumes/t7-ssd/Miniscope/C6-J588_Disc5_msCamComb_MC.mat | /Volumes/t7-ssd/Miniscope/C6-J588_Disc5_timestampsAllCumulData.mat |                                             | /Volumes/t7-ssd/Miniscope/neuron.mat  | 2023-08-21T15:30:00 | test       | P7D | M   |          |          |
