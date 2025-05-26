import pandas as pd
import numpy as np
from flask import current_app
import os

def gaze2npy(file_path, participants):
    print("start loading excel")
    xls = pd.ExcelFile(file_path)
    print("start loading the first sheet")
    # Load the first sheet (assuming the data is there)
    df = xls.parse(xls.sheet_names[0])
    for participant in participants:
        print("start loading ", participant)
        df_participant = df[(df["Participant name"] == participant) & (df["Sensor"] == "Eye Tracker")]
        df_participant = df_participant.sort_values(by="Recording timestamp")
        
        start_time = df_participant["Recording timestamp"].iloc[0]
        df_participant_resampled = df_participant.groupby(((df_participant["Recording timestamp"] - start_time) // 40) * 40).first()

        # Extract fixation points (X, Y) where valid fixation data exists
        fixation_data = df_participant_resampled[["Fixation point X", "Fixation point Y"]].to_numpy()

        # Save as an .npy file

        npy_file_path = os.path.join(current_app.config["OUTPUT_FOLDER"], f"{participant}.npy")  # Output file path
        np.save(npy_file_path, fixation_data)
    return True

# def gaze2npy(file_path, participants):
#     print("start loading excel")
#     xls = pd.ExcelFile(file_path)
#     print("start loading the first sheet")
#     # Load the first sheet (assuming the data is there)
#     df = xls.parse(xls.sheet_names[0])
#     for participant in participants:
#         print("start loading ", participant)
#         df_participant = df[(df["Participant name"] == participant) & (df["Sensor"] == "Eye Tracker")]
#         df_participant = df_participant.sort_values(by="Recording timestamp")
        
#         start_time = df_participant["Recording timestamp"].iloc[0]
#         df_participant_resampled = df_participant.groupby(((df_participant["Recording timestamp"] - start_time) // 40) * 40).first()

#         # Extract fixation points (X, Y) where valid fixation data exists
#         fixation_data = df_participant_resampled[["Fixation point X", "Fixation point Y"]].to_numpy()

#         # Save as an .npy file
#         npy_file_path = rf"./uploads/{participant}.npy"  # Output file path
#         np.save(npy_file_path, fixation_data)
#     return True