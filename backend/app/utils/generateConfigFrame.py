import os
import cv2
import json
import numpy as np
from pupil_apriltags import Detector

output_json_path = "./uploads/frame_data.json"
output_image_path = "./uploads/warped_frame.jpg"

def extractFrame(image, points, save=True):
    display_width = 500
    scale = image.shape[1] / display_width

    source_points = np.array([[pt["x"], pt["y"]] for pt in points[:4]], dtype=np.float32) * scale
    screen_width, screen_height = 1920, 1080
    boundary = 800
    output_width, output_height = screen_width + 2 * boundary, screen_height + 2 * boundary

    destination_points = np.array([
        [boundary, boundary],
        [boundary + screen_width - 1, boundary],
        [boundary + screen_width - 1, boundary + screen_height - 1],
        [boundary, boundary + screen_height - 1]
    ], dtype=np.float32)

    matrix = cv2.getPerspectiveTransform(source_points, destination_points)
    warped_image = cv2.warpPerspective(image, matrix, (output_width, output_height))

    # Transform additional marker points if any
    transformed_marker_coords = []
    if len(points) >= 8:
        marker_points = np.array([[pt["x"], pt["y"]] for pt in points[4:8]], dtype=np.float32) * scale
        marker_points_homo = np.hstack([marker_points, np.ones((4, 1))])
        transformed = (matrix @ marker_points_homo.T).T
        transformed /= transformed[:, [2]]
        transformed_marker_coords = [{"x": float(p[0]), "y": float(p[1])} for p in transformed]

    # Convert to grayscale and enhance
    gray = cv2.cvtColor(warped_image, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    tag_data = {
        "boundary": boundary,
        "screen_width": screen_width,
        "screen_height": screen_height,
        "apriltags": [],
        "arucos": []
    }

    # === AprilTag detection ===
    detector = Detector(
        families='tag36h11',
        nthreads=1,
        quad_decimate=2.0,
        quad_sigma=0.0,
        refine_edges=1,
        decode_sharpening=0.25,
        debug=0
    )
    apriltags = detector.detect(gray, estimate_tag_pose=False)
    for tag in apriltags:
        tag_id = tag.tag_id
        center = (int(tag.center[0]), int(tag.center[1]))
        tag_data["apriltags"].append({
            "id": int(tag_id),
            "center": {"x": center[0], "y": center[1]}
        })
        corners = np.int32(tag.corners)
        cv2.polylines(warped_image, [corners], isClosed=True, color=(0, 255, 0), thickness=2)
        cv2.circle(warped_image, center, 5, (0, 0, 255), -1)
        cv2.putText(warped_image, f"April:{tag_id}", (center[0]-10, center[1]-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

    # === ArUco detection ===
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_ARUCO_ORIGINAL)
    aruco_params = cv2.aruco.DetectorParameters()
    aruco_detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)
    corners_list, ids, _ = aruco_detector.detectMarkers(gray)

    if ids is not None:
        for idx, corner in zip(ids.flatten(), corners_list):
            c = corner[0]
            center = np.mean(c, axis=0).astype(int)
            tag_data["arucos"].append({
                "id": int(idx),
                "center": {"x": int(center[0]), "y": int(center[1])}
            })
            cv2.polylines(warped_image, [np.int32(c)], isClosed=True, color=(255, 0, 255), thickness=2)
            cv2.circle(warped_image, tuple(center), 5, (0, 255, 255), -1)
            cv2.putText(warped_image, f"Aruco:{idx}", (center[0]-10, center[1]-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    # === Save results ===
    if save:
        with open(output_json_path, 'w') as f:
            json.dump(tag_data, f, indent=4)
        cv2.imwrite(output_image_path, warped_image)

    return {
        "warped_image": warped_image,
        "transformed_marker_coords": transformed_marker_coords,
        "tags": tag_data
    }
