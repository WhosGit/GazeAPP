import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend
import matplotlib.pyplot as plt
import io
import base64

def detect_markers(video_path):
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    parameters = cv2.aruco.DetectorParameters()
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    marker_0_presence = []
    marker_1_presence = []
    print("detecting now")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
        ids_list = ids.flatten().tolist() if ids is not None else []

        marker_0_presence.append(1 if ids_list.count(0) > 2 else 0)
        marker_1_presence.append(1 if ids_list.count(1) > 2 else 0)
    print("detection finished")
    cap.release()
    return marker_0_presence, marker_1_presence, fps

def merge_intervals(binary_list, gap=50):
    merged = binary_list[:]
    i = 0
    while i < len(merged):
        if merged[i] == 1:
            j = i + 1
            while j < len(merged) and merged[j] == 1:
                j += 1
            gap_start = j
            while j < len(merged) and merged[j] == 0:
                j += 1
            if j < len(merged) and (j - gap_start) <= gap:
                for k in range(gap_start, j):
                    merged[k] = 1
            i = j
        else:
            i += 1
    return merged

def compute_segment_indices(marker_0, marker_1):
    m0 = np.array(merge_intervals(marker_0))
    m1 = np.array(merge_intervals(marker_1))
    start_indices = np.where(np.diff(m0) < 0)[0] + 1
    end_indices = np.where(np.diff(m1) > 0)[0] + 1
    n = min(len(start_indices), len(end_indices))
    return m0, m1, start_indices[:n].tolist(), end_indices[:n].tolist()

def assign_labels(start_indices, light, head, media):
    light_map = {'A': 'On', 'B': 'Off', 'C': 'Dim'}
    head_map = {'A': 'Center', 'B': 'Below', 'C': 'Free'}
    media_map = {'A': 'Image', 'B': 'Video'}
    labels = ['cali']

    tags = ['cali']
    for i in range(len(light)):
        for j in range(len(head)):
            for k in range(len(media)):
                labels.append(f"{light_map[light[i]]}-{head_map[head[j]]}-{media_map[media[k]]}")

    return labels

def generate_plot(marker_0, marker_1):
    fig, ax = plt.subplots(figsize=(20, 3))
    ax.plot(marker_0, label='marker-0', color='blue')
    ax.plot(marker_1, label='marker-1', color='orange')
    ax.legend()
    ax.set_title("Marker Presence Timeline")

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plot_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return plot_base64

