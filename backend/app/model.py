import os
import uuid
from flask import session, current_app


def create_session_folder():
    UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
    session_id = f"{uuid.uuid4().hex}"
    session['session_id'] = session_id
    session_folder = os.path.join(UPLOAD_FOLDER, session_id)
    os.makedirs(session_folder, exist_ok=True)
    return session_folder

def get_session_folder():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    session_id = session["session_id"]
    folder = os.path.join(current_app.config['UPLOAD_FOLDER'], session_id)
    os.makedirs(folder, exist_ok=True)
    return folder