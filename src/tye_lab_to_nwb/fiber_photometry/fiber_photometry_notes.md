# Conversion notes

## Run conversion for multiple sessions in parallel

The `convert_all_sessions.py` conversion script takes an Excel (.xlsx) file as an input
which contain all the necessary information to convert each session. The number of rows in the file
correspond to the number of sessions that will be converted.

The columns in the selected Excel (.xlsx) file should be named as:
- "`nwbfile_path`": The file path where the NWB file will be created. (e.g. "test.nwb")
- "`data_file_path`": The path that points to the .csv file containing the photometry intensity values.
- "`session_start_time`": The recording start time for the photometry session in YYYY-MM-DDTHH:MM:SS format (e.g. 2023-08-21T15:30:00).
