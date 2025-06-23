import pandas as pd
import numpy as np
from flask import current_app
import os

# 旧的 gaze2npy 函数，保留以供参考
# def gaze2npy(file_path, participants):
#     print("start loading excel")
#     xls = pd.ExcelFile(file_path)
#     print("start loading the first sheet")
#     # Load the first sheet (assuming the data is there)
#     df = xls.parse(xls.sheet_names[0])

#     fixation_data_list = []
#     for participant in participants:
#         print("start loading ", participant)
#         df_participant = df[(df["Participant name"] == participant) & (df["Sensor"] == "Eye Tracker")]
#         df_participant = df_participant.sort_values(by="Recording timestamp")
        
#         if df_participant.empty:
#             print(f"Warning: No data for participant {participant}")
#             continue

#         start_time = df_participant["Recording timestamp"].iloc[0]
#         # 分组键转为 int，避免 float 问题
#         group_keys = (((df_participant["Recording timestamp"] - start_time) // 40) * 40).astype(int)
#         df_participant_resampled = df_participant.groupby(group_keys).first()

#         # Extract fixation points (X, Y) where valid fixation data exists
#         fixation_points = df_participant_resampled[["Fixation point X", "Fixation point Y"]].to_numpy()

#         # save as a dictionary with participant name
#         fixation_data = {
#             "participant": participant,
#             "fixation_points": fixation_points
#         }

#         fixation_data_list.append(fixation_data)

#         # 如需保存为 .npy 文件，取消注释以下代码
#         # npy_file_path = os.path.join(current_app.config["OUTPUT_FOLDER"], f"{participant}.npy")
#         # np.save(npy_file_path, fixation_points)
#     return fixation_data_list


# import numpy as np

def find_closest_indices(timestamps, interval=40):
    """
    返回一个列表 result，满足：
    result[i] 是 timestamps 中最接近 interval*i 的索引（最早出现）
    """
    result = []
    max_t = timestamps.iloc[-1]
    max_i = int(max_t // interval)

    for i in range(max_i + 1):
        target = interval * i
        # 计算所有时间点与目标的差的绝对值
        diffs = np.abs(timestamps - target)
        min_diff = diffs.min()
        # 找到差值最小的所有索引，取最小索引（最早出现）
        candidates = np.where(diffs == min_diff)[0]
        chosen_idx = candidates.min()
        result.append(chosen_idx)

    return result


def gaze2npy(file_path, participants):
    import pandas as pd
    import numpy as np

    print("start loading excel")
    xls = pd.ExcelFile(file_path)
    print("start loading the first sheet")
    df = xls.parse(xls.sheet_names[0])

    fixation_data_list = []
    for participant in participants:
        print("start loading ", participant)
        df_participant = df[(df["Participant name"] == participant) & (df["Sensor"] == "Eye Tracker")]
        df_participant = df_participant.sort_values(by="Recording timestamp")
        df_participant = df_participant.reset_index(drop=True)

        if df_participant.empty:
            print(f"Warning: No data for participant {participant}")
            continue

        timestamps = df_participant["Recording timestamp"]

        # 使用新函数，找出对应每个40*i的最接近索引
        closest_indices = find_closest_indices(timestamps, interval=40)
        
        # 用这些索引取对应行（保证顺序且不重复）
        df_participant_resampled = df_participant.loc[closest_indices]

        fixation_points = df_participant_resampled[["Fixation point X", "Fixation point Y"]].to_numpy()

        fixation_data = {
            "participant": participant,
            "fixation_points": fixation_points
        }

        fixation_data_list.append(fixation_data)

    return fixation_data_list

