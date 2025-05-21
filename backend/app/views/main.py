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

