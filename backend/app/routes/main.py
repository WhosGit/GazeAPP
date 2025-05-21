import os
import cv2
import numpy as np
import json
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from app.utils.generateConfigFrame import extractFrame
from app.utils.extractRawGaze import gaze2npy
from app.utils.videoSegment import (
    detect_markers,
    compute_segment_indices,
    assign_labels,
    generate_plot
)
import base64
import tempfile 

routes = Blueprint("routes", __name__)

@routes.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Gaze Processing API is running!"})

@routes.route("/process_gaze", methods=["POST"])
def process_gaze():
    data = request.json  # Expecting JSON input
    return jsonify({"processed_gaze": 'test'})

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def encode_image_to_base64(img):
    _, buffer = cv2.imencode('.png', img)
    return base64.b64encode(buffer).decode('utf-8')

@routes.route("/frame_config", methods=["POST"])
def frame_config():
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files["image"]
    filename = secure_filename(image_file.filename)
    image_path = os.path.join(UPLOAD_FOLDER, filename)
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
    encoded_img = encode_image_to_base64(result["warped_image"])
    return jsonify({
        "message": "Frame processed",
        "transformed_image": encoded_img,
        "transformed_points": result["transformed_marker_coords"],
        "apriltags": result["tags"]["apriltags"],
        "arucos": result["tags"]["arucos"]
    })


@routes.route("/extract_raw_gaze", methods=["POST"])
def extract_raw_gaze():
    """Handle Excel file upload for extracting gaze data"""
    if "excel" not in request.files or "participant" not in request.form:
        return jsonify({"error": "Invalid request"}), 400

    excel_file = request.files["excel"]
    participant_name = request.form.get("participant")
    
    filename = secure_filename(excel_file.filename)
    excel_path = os.path.join('uploads', filename)
    excel_file.save(excel_path)
    participants = participant_name.split(', ')
    gaze2npy(excel_path, participants)
    return jsonify({
        "message": f"Gaze data extracted for {participant_name}",
        "excel_file": excel_path
    })

@routes.route("/detect_segments", methods=["POST"])
def detect_segments():
    video_file = request.files.get("video")
    light = request.form.get("light", "")
    head = request.form.get("head", "")
    media = request.form.get("media", "")

    if not video_file:
        return jsonify({"error": "No video file provided"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        video_path = tmp.name
        video_file.save(video_path)

    try:
        marker_0, marker_1, fps = detect_markers(video_path)
        m0_merged, m1_merged, starts, ends = compute_segment_indices(marker_0, marker_1)
        labels = assign_labels(starts, light, head, media)
        plot_base64 = generate_plot(m0_merged, m1_merged)

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
@routes.route("/submit_segments", methods=["POST"])
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

    with open("segments_25fps.json", "w") as f:
        json.dump(adjusted_segments, f, indent=2)

    return jsonify({
        "message": "Segments saved successfully.",
        "segment_count": len(adjusted_segments)
    })
