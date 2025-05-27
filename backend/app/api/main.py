from app.utils import (
    extractFrame,
    gaze2npy,
    detect_markers,
    compute_segment_indices,
    assign_labels,
    generate_plot,
    gaze_process
)
from app.model import (
    get_session_folder,
    create_session_folder
)
import os
import numpy as np
import cv2
import json
from flask import Blueprint, request, jsonify, current_app, send_from_directory
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
    session_folder = get_session_folder()

    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files["image"]
    filename = secure_filename(image_file.filename)
    image_path = os.path.join(session_folder, filename)
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
    output_json_path = os.path.join(session_folder, f"{Path(filename).stem}.json")
    output_marker_path = os.path.join(session_folder, f"{Path(filename).stem}_marker.json")
    output_image_path = os.path.join(session_folder,  filename)
    with open(output_marker_path, 'w') as f:
        json.dump(result["transformed_marker_coords"], f, indent=4)
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
    session_folder = get_session_folder()

    """Handle Excel file upload for extracting gaze data"""
    if "excel" not in request.files or "participant" not in request.form:
        return jsonify({"error": "Invalid request"}), 400

    excel_file = request.files["excel"]
    participant_name = request.form.get("participant")
    
    filename = secure_filename(excel_file.filename)
    excel_path = os.path.join(session_folder, filename)
    excel_file.save(excel_path)
    participants = participant_name.split(', ')
    fixation_data_list = gaze2npy(excel_path, participants)

    # Save the fixation data as .npy files
    raw_gaze_folder = os.path.join(session_folder, "raw_gaze")
    os.makedirs(raw_gaze_folder, exist_ok=True)
    for fixation_data in fixation_data_list:
        npy_file_path = os.path.join(raw_gaze_folder, f"{fixation_data['participant']}.npy")  # 修正引号
        np.save(npy_file_path, fixation_data["fixation_points"])

    return jsonify({
        "message": f"Gaze data extracted for {participant_name}",
        "excel_file": excel_path
    })

@api.route("/detect_segments", methods=["POST"])
def detect_segments():
    session_folder = get_session_folder()
    
    video_file = request.files.get("video")
    light = request.form.get("light", "")
    head = request.form.get("head", "")
    media = request.form.get("media", "")

    if video_file:
        # Save the video file
        video_path = os.path.join(session_folder, "video.mp4")
        video_file.save(video_path)
    else:
        return jsonify({"error": "No video file provided"}), 400

    # with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
    #     video_path = tmp.name
    #     video_file.save(video_path)

    

    try:
        marker_0, marker_1, fps = detect_markers(video_path)
        m0_merged, m1_merged, starts, ends = compute_segment_indices(marker_0, marker_1)
        labels = assign_labels(starts, light, head, media)
        plot_base64 = generate_plot(m0_merged, m1_merged)

        # Save the segments to a JSON file
        segmentation_path = os.path.join(session_folder, "segments.json")
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
        if os.path.exists(video_path):  # 防止文件不存在时报错
            # os.remove(video_path)
            pass

# Re-execute to restore Flask endpoint in the new kernel context

# Re-execute to restore Flask endpoint in the new kernel context
@api.route("/submit_segments", methods=["POST"])
def submit_segments():
    session_folder = get_session_folder()


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

    segmentation_path = os.path.join(session_folder, "segments_25fps.json")
    with open(segmentation_path, "w") as f:
        json.dump(adjusted_segments, f, indent=2)

    return jsonify({
        "message": "Segments saved successfully.",
        "segment_count": len(adjusted_segments)
    })

@api.route("/results/<filename>")
def get_results(filename):
    session_folder = get_session_folder()   
    
    if not os.path.exists(os.path.join(session_folder, filename)):
        if filename == "gaze.npy":
            # 如果没有gaze.npy文件，尝试从raw_gaze目录中获取
            raw_gaze_folder = os.path.join(session_folder, "raw_gaze")
            if os.path.exists(raw_gaze_folder):
                for file in os.listdir(raw_gaze_folder):
                    if file.endswith(".npy"):
                        return send_from_directory(raw_gaze_folder, file)
        return jsonify({"error": "File not found"}), 404

    return send_from_directory(session_folder, filename)

# 新增：返回实际可下载的URL
@api.route("/results_url/<filename>")
def get_results_url(filename):
    session_folder = get_session_folder()
    if not os.path.exists(os.path.join(session_folder, filename)):
        return jsonify({"error": "File not found"}), 404
    # 返回带 session 路径的下载URL
    return jsonify({
        "url": f"/api/results/{filename}"
    })

RESULT_EXT = [".mp4", ".npy", ".json", ".json"]
RESULT_FILENAME = ["video.mp4", "gaze.npy", "segments_25fps.json", "tags.json"]   

@api.route("/upload_user_result/<int:index>", methods=["POST"])
def upload_user_result(index):
    session_folder = get_session_folder()

    if index < 0 or index >= len(RESULT_EXT):
        return jsonify({"error": "Invalid index"}), 400

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    # 只检查扩展名
    if not file.filename.lower().endswith(RESULT_EXT[index]):
        return jsonify({"error": f"File must be a {RESULT_EXT[index]} file"}), 400

    filename = RESULT_FILENAME[index]
    file_path = os.path.join(session_folder, filename)
    file.save(file_path)

    return jsonify({"message": f"{filename} uploaded successfully."})

@api.route("/submit_final_results", methods=["POST"])
def submit_final_results():
    session_folder = get_session_folder()

    # 获取 output_folder 参数，默认为 session_folder/processed_gaze
    if request.is_json:
        output_folder = request.json.get("output_folder")
    else:
        output_folder = None
    if not output_folder:
        output_folder = os.path.join(session_folder, "processed_gaze")
    # 若为相对路径，自动补全为 OUTPUT_FOLDER 下的子目录
    if not os.path.isabs(output_folder):
        output_folder = os.path.join(current_app.config['OUTPUT_FOLDER'], output_folder) if not output_folder.startswith(session_folder) else output_folder
    print(f"Output folder: {output_folder}")
    os.makedirs(output_folder, exist_ok=True)

    # process_gaze
    video_path = os.path.join(session_folder, "video.mp4")
    gaze_folder = os.path.join(session_folder, "raw_gaze")
    tag_json = os.path.join(session_folder, "tags.json")
    if not os.path.exists(tag_json):
        tag_json = os.path.join(current_app.config.get("UPLOAD_FOLDER", session_folder), "tags.json")
    segmentation_path = os.path.join(session_folder, "segments_25fps.json")
    gaze_path = os.path.join(session_folder, "gaze.npy")

    # Process gaze data
    processed = False
    if os.path.exists(gaze_path):
        gaze_process(video_path, gaze_path, segmentation_path, tag_json, output_folder)
        processed = True
    elif os.path.exists(gaze_folder):
        for file in os.listdir(gaze_folder):
            if file.endswith(".npy"):
                gaze_path = os.path.join(gaze_folder, file)
                gaze_process(video_path, gaze_path, segmentation_path, tag_json, output_folder)
                processed = True

    if not processed:
        return jsonify({
            "error": "No gaze data found to process."
        }), 400

    return jsonify({
        "message": "Final results submitted successfully.",
        "output_folder": output_folder
    })

@api.route("/view_json/<filename>")
def view_json(filename):
    if not filename.endswith(".json"):
        return "仅支持json文件预览", 400

    session_folder = get_session_folder()
    file_path = os.path.join(session_folder, filename)
    if not os.path.exists(file_path):
        return "文件未找到", 404
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 生成简单的 HTML 展示
        html = f"""
        <html>
        <head>
            <title>{filename} 内容查看</title>
            <meta charset="utf-8">
            <style>
                body {{ background: #222; color: #fff; font-family: monospace; padding: 2em; }}
                pre {{ background: #111; padding: 1em; border-radius: 6px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <h2>{filename}</h2>
            <pre>{json.dumps(data, indent=2, ensure_ascii=False)}</pre>
        </body>
        </html>
        """
        return html
    except Exception as e:
        return f"读取文件失败: {str(e)}", 500
