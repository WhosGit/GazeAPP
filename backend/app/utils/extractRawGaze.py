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

    fixation_data_list = []
    for participant in participants:
        print("start loading ", participant)
        df_participant = df[(df["Participant name"] == participant) & (df["Sensor"] == "Eye Tracker")]
        df_participant = df_participant.sort_values(by="Recording timestamp")
        
        if df_participant.empty:
            print(f"Warning: No data for participant {participant}")
            continue

        start_time = df_participant["Recording timestamp"].iloc[0]
        # 分组键转为 int，避免 float 问题
        group_keys = (((df_participant["Recording timestamp"] - start_time) // 40) * 40).astype(int)
        df_participant_resampled = df_participant.groupby(group_keys).first()

        # Extract fixation points (X, Y) where valid fixation data exists
        fixation_points = df_participant_resampled[["Fixation point X", "Fixation point Y"]].to_numpy()

        # save as a dictionary with participant name
        fixation_data = {
            "participant": participant,
            "fixation_points": fixation_points
        }

        fixation_data_list.append(fixation_data)

        # 如需保存为 .npy 文件，取消注释以下代码
        # npy_file_path = os.path.join(current_app.config["OUTPUT_FOLDER"], f"{participant}.npy")
        # np.save(npy_file_path, fixation_points)
    return fixation_data_list
