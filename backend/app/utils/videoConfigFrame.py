import os
import cv2
import json
import numpy as np
from tqdm import tqdm
from pupil_apriltags import Detector
from itertools import combinations
from flask import current_app


# ========== HELPER FUNCTIONS ==========

def detect_apriltags(gray_frame):
    '''Detect AprilTags in a grayscale image.'''
    detector = Detector(families='tag36h11')
    detections = detector.detect(gray_frame)
    return {("apriltag", det.tag_id): det for det in detections}


def detect_arucos(gray_frame):
    '''Detect ArUco markers in a grayscale image.'''
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_ARUCO_ORIGINAL)
    parameters = cv2.aruco.DetectorParameters()
    corners, ids, _ = cv2.aruco.detectMarkers(gray_frame, aruco_dict, parameters=parameters)
    return {("aruco", int(i)): c[0] for i, c in zip(ids.flatten(), corners)} if ids is not None else {}


def match_tags_from_json(tag_data, apriltag_map, aruco_map):
    '''Match tags from JSON data with detected tags.'''
    matched = []

    for tag in tag_data.get("apriltags", []):
        key = ("apriltag", tag["id"])
        if key in apriltag_map:
            det = apriltag_map[key]
            matched.append({
                "type": "apriltag",
                "id": tag["id"],
                "ref": np.array([tag["center"]["x"], tag["center"]["y"]]),
                "img": np.mean(det.corners, axis=0),
                "center": tuple(int(c) for c in det.center)
            })

    for tag in tag_data.get("arucos", []):
        key = ("aruco", tag["id"])
        if key in aruco_map:
            corners = aruco_map[key]
            center = np.mean(corners, axis=0)
            matched.append({
                "type": "aruco",
                "id": tag["id"],
                "ref": np.array([tag["center"]["x"], tag["center"]["y"]]),
                "img": np.mean(corners, axis=0),
                "center": tuple(int(c) for c in center)
            })

    return matched


def calculate_polygon_area(points):
    '''Calculate the area of a polygon given its vertices.'''
    x, y = np.array(points).T
    return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


def are_three_points_almost_collinear(pts, tol=1000):
    '''Check if any three points are almost collinear.'''
    for i in range(4):
        for j in range(i + 1, 4):
            for k in range(j + 1, 4):
                p1, p2, p3 = pts[i], pts[j], pts[k]
                area = 0.5 * np.abs(
                    p1[0] * (p2[1] - p3[1]) +
                    p2[0] * (p3[1] - p1[1]) +
                    p3[0] * (p1[1] - p2[1])
                )
                if area < tol:
                    return True
    return False


def select_largest_quad(detected_tags):
    '''Select the largest quadrilateral from detected tags.'''
    best_quad = None
    best_area = 0

    for quad in combinations(detected_tags, 4):
        pts = [tag["center"] for tag in quad]
        area = calculate_polygon_area(pts)
        if area > best_area and not are_three_points_almost_collinear(np.array(pts)):
            best_quad = quad
            best_area = area

    return best_quad

def detect_tags_and_get_warp(frame, tag_data):
    '''Detect tags and compute the warp matrix.'''
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    apriltag_map = detect_apriltags(gray)
    aruco_map = detect_arucos(gray)

    detected_tags = match_tags_from_json(tag_data, apriltag_map, aruco_map)

    if len(detected_tags) < 4:
        return None, None

    best_quad = select_largest_quad(detected_tags)
    if best_quad is None:
        return None, None

    src_pts = [tag["img"] for tag in best_quad]
    dst_pts = [tag["ref"] for tag in best_quad]

    #print("Selected markers for warp:", [(tag["type"], tag["id"]) for tag in best_quad])

    return cv2.getPerspectiveTransform(np.array(src_pts, np.float32), np.array(dst_pts, np.float32)), tag_data

def warp_and_crop(frame, matrix, meta):
    '''Apply the warp matrix to the frame and crop it.'''
    b = meta["boundary"]
    w, h = meta["screen_width"], meta["screen_height"]
    warped = cv2.warpPerspective(frame, matrix, (w + 2*b, h + 2*b))
    return warped[b:h+b, b:w+b]


def gaze_process(video_path,gaze_path,segment_json,tag_json,output_dir):
    # Load gaze and segment info
    gaze = np.load(gaze_path, allow_pickle=True)
    with open(segment_json) as f:
        segments = json.load(f)
    with open(tag_json) as f:
        tag_data = json.load(f)

    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    for seg in segments[13:]:
        start, end, label = seg["start"], seg["end"], seg["label"]
        warped_points = []

        print(f"Processing segment: {label} ({start}-{end})")
        for frame_idx in tqdm(range(start, end)):
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                warped_points.append([-1, -1])
                continue

            gp = gaze[frame_idx]
            if np.isnan(gp[0]):
                warped_points.append([-1, -1])
                continue

            # Detect tags
            warp_matrix, meta = detect_tags_and_get_warp(frame, tag_data)
            
            if warp_matrix is None:
                warped_points.append([-1, -1])
                continue

            # Warp gaze
            gp_homo = np.array([[gp[0], gp[1], 1]]).T
            warped = warp_matrix @ gp_homo
            warped /= warped[2]
            xw, yw = int(warped[0]), int(warped[1])
            b = meta["boundary"]
            warped_points.append([xw - b, yw - b])
            # if 0 <= xw - b < meta["screen_width"] and 0 <= yw - b < meta["screen_height"]:
            #     warped_points.append([xw - b, yw - b])
            # else:
            #     warped_points.append([-1, -1])

        out_path = os.path.join(output_dir, f"{label}.npy")
        np.save(out_path, np.array(warped_points))
        print(f"Saved warped gaze: {out_path}")

    cap.release()
