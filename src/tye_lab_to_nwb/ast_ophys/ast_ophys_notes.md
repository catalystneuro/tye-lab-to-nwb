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
