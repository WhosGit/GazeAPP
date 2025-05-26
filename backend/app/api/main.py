from app.utils import (
    extractFrame,
    gaze2npy,
    detect_markers,
    compute_segment_indices,
    assign_labels,
    generate_plot,
    gaze_process
)
import os
import numpy as np
import cv2
import json
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import base64
import tempfile
from pathlib import Path


# url prefix: /api
api = Blueprint("api", __name__)

@api.route("/process_gaze", methods=["POST"])
def process_gaze():
    data = request.json  # Expecting JSON input
    return jsonify({"processed_gaze": 'test'})

# UPLOAD_FOLDER = "uploads"
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def encode_image_to_base64(img):
    _, buffer = cv2.imencode('.png', img)
    return base64.b64encode(buffer).decode('utf-8')

@api.route("/frame_config", methods=["POST"])
def frame_config():
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files["image"]
    filename = secure_filename(image_file.filename)
    dir_path = current_app.config['UPLOAD_FOLDER']
    image_path = os.path.join(dir_path, filename)
    image_file.save(image_path)

    image = cv2.imread(image_path)
    if image is None:
        return jsonify({"error": "Failed to read image"}), 400

    points_str = request.form.get("points")
    try:
        points = eval(points_str)  # Be cautious with eval in production
        if len(points) != 8:
            return jsonify({"error": "Exactly 8 points required"}), 400
    except Exception as e:
        return jsonify({"error": "Invalid points format"}), 400

    result = extractFrame(image, points)

    # === Save results ===
    output_json_path = os.path.join(current_app.config['OUTPUT_FOLDER'], f"{Path(filename).stem}.json")
    output_marker_path = os.path.join(current_app.config['OUTPUT_FOLDER'], f"{Path(filename).stem}_marker.json")
    with open(output_marker_path, 'w') as f:
        json.dump(result["transformed_marker_coords"], f, indent=4)
    output_image_path = os.path.join(current_app.config['OUTPUT_FOLDER'],  filename)
    with open(output_json_path, 'w') as f:
        json.dump(result["tags"], f, indent=4)
    cv2.imwrite(output_image_path, result["warped_image"])

    encoded_img = encode_image_to_base64(result["warped_image"])
    return jsonify({
        "message": "Frame processed",
        "transformed_image": encoded_img,
        "transformed_points": result["transformed_marker_coords"],
        "apriltags": result["tags"]["apriltags"],
        "arucos": result["tags"]["arucos"]
    })


@api.route("/extract_raw_gaze", methods=["POST"])
def extract_raw_gaze():
    """Handle Excel file upload for extracting gaze data"""
    if "excel" not in request.files or "participant" not in request.form:
        return jsonify({"error": "Invalid request"}), 400

    excel_file = request.files["excel"]
    participant_name = request.form.get("participant")
    
    filename = secure_filename(excel_file.filename)
    excel_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    excel_file.save(excel_path)
    participants = participant_name.split(', ')
    gaze2npy(excel_path, participants)

    # # Save the fixation data as .npy files
    # for participant in participants:
    #     npy_file_path = os.path.join(current_app.config["OUTPUT_FOLDER"], f"p12-2.npy")
    #     np.save(npy_file_path, fixation_data)

    return jsonify({
        "message": f"Gaze data extracted for {participant_name}",
        "excel_file": excel_path
    })

@api.route("/detect_segments", methods=["POST"])
def detect_segments():
    
    video_file = request.files.get("video")
    light = request.form.get("light", "")
    head = request.form.get("head", "")
    media = request.form.get("media", "")

    if not video_file:
        return jsonify({"error": "No video file provided"}), 400

    # with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
    #     video_path = tmp.name
    #     video_file.save(video_path)

    # Save the video file
    video_path = os.path.join(current_app.config['UPLOAD_FOLDER'], "video.mp4")
    video_file.save(video_path)

    try:
        marker_0, marker_1, fps = detect_markers(video_path)
        m0_merged, m1_merged, starts, ends = compute_segment_indices(marker_0, marker_1)
        labels = assign_labels(starts, light, head, media)
        plot_base64 = generate_plot(m0_merged, m1_merged)

        # Save the segments to a JSON file
        segmentation_path = os.path.join(current_app.config['OUTPUT_FOLDER'], "segments.json")
        with open(segmentation_path, "w") as f:
            json.dump({
                "starts": starts,
                "ends": ends,
                "labels": labels
            }, f, indent=2)

        return jsonify({
            "starts": starts,
            "ends": ends,
            "labels": labels,
            "plot_base64": plot_base64,
            "fps": fps
        })
    finally:
        os.remove(video_path)

# Re-execute to restore Flask endpoint in the new kernel context

# Re-execute to restore Flask endpoint in the new kernel context
@api.route("/submit_segments", methods=["POST"])
def submit_segments():


    data = request.get_json()
    starts = data.get("starts", [])
    ends = data.get("ends", [])
    labels = data.get("labels", [])
    fps = float(data.get("fps", 25))

    if not (len(starts) == len(ends) == len(labels)):
        return jsonify({"error": "Starts, ends, and labels must be of equal length."}), 400

    def adjust_interval(start, end, target_frames, fps):
        if fps != 25:
            start = int(start / fps * 25)
            end = int(end / fps * 25)
        center_time = ((start + end) / 2) / fps
        new_start = int((center_time - (target_frames / 2) / 25) * 25)
        new_end = new_start + target_frames
        return new_start, new_end

    adjusted_segments = []

    for i in range(len(starts)):
        label = labels[i].lower()
        start = starts[i]
        end = ends[i]

        
        if "cali" in label:
            start, end = adjust_interval(start, end, 27*25, fps)
        elif "image" in label:
            print(label)
            start, end = adjust_interval(start, end, 10*25, fps)
        elif "video" in label:
            start, end = adjust_interval(start, end, 30*25, fps)
        

        adjusted_segments.append({
            "start": start,
            "end": end,
            "label": labels[i]
        })

    segmentation_path = os.path.join(current_app.config['OUTPUT_FOLDER'], "segments_25fps.json")
    with open(segmentation_path, "w") as f:
        json.dump(adjusted_segments, f, indent=2)

    # process_gaze
    video_path = os.path.join(current_app.config['UPLOAD_FOLDER'], "video.mp4")
    gaze_path = os.path.join(current_app.config['OUTPUT_FOLDER'], "p12-2 (2).npy")
    tag_json = os.path.join(current_app.config['OUTPUT_FOLDER'], "may17.json")
    output_dir = current_app.config['OUTPUT_FOLDER']

    # Process gaze data
    gaze_process(video_path, gaze_path, segmentation_path, tag_json, output_dir)


    return jsonify({
        "message": "Segments saved successfully.",
        "segment_count": len(adjusted_segments)
    })

