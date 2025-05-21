import React, { useState } from "react";

const VideoSegmentation = () => {
  const [videoFile, setVideoFile] = useState(null);
  const [fps, setFps] = useState(25);
  const [starts, setStarts] = useState([]);
  const [ends, setEnds] = useState([]);
  const [labels, setLabels] = useState([]);
  const [lightCondition, setLightCondition] = useState("");
  const [headCondition, setHeadCondition] = useState("");
  const [mediaCondition, setMediaCondition] = useState("");
  const [serverResponse, setServerResponse] = useState("");
  const [plotUrl, setPlotUrl] = useState("");

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) setVideoFile(file);
  };

  const convertToTimestamp = (frameId) => {
    const totalSeconds = frameId / fps;
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = Math.floor(totalSeconds % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const handleFetchSegments = async () => {
    const formData = new FormData();
    formData.append("video", videoFile);
    formData.append("light", lightCondition);
    formData.append("head", headCondition);
    formData.append("media", mediaCondition);

    const response = await fetch("/api/detect_segments", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    setStarts(data.starts || []);
    setEnds(data.ends || []);
    setLabels(data.labels || []);
    if (data.plot_base64) {
      setPlotUrl(`data:image/png;base64,${data.plot_base64}`);
    }
    if (data.fps) {
      setFps(data.fps);
    }
  };

  const handleAddItem = (listSetter, list, index) => {
    const updated = [...list];
    updated.splice(index + 1, 0, "");
    listSetter(updated);
  };

  const handleRemoveItem = (listSetter, list, index) => {
    const updated = [...list];
    updated.splice(index, 1);
    listSetter(updated);
  };

  const handleChangeItem = (listSetter, list, index, value) => {
    const updated = [...list];
    updated[index] = value;
    listSetter(updated);
  };

  const handleSubmit = async () => {
    if (starts.length !== ends.length || ends.length !== labels.length) {
      alert("Starts, ends, and labels must have the same length.");
      return;
    }
    if (starts.some((s, i) => parseInt(s) > parseInt(ends[i]))) {
      alert("Each start frame must be less than or equal to its corresponding end frame.");
      return;
    }

    const payload = {
      starts: starts.map(Number),
      ends: ends.map(Number),
      labels,
      fps: parseFloat(fps)
    };

    const response = await fetch("/submit_segments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    setServerResponse(data.message);
  };

  return (
    <div>
      <h2>Video Segmentation Tool</h2>

      <label>Upload Video: </label>
      <input type="file" accept="video/*" onChange={handleFileChange} /><br /><br />

      <label>FPS (auto-filled): </label>
      <input type="number" value={fps} disabled style={{ backgroundColor: '#f0f0f0' }} /><br /><br />

      <label>Lighting Condition: </label>
      <input type="text" value={lightCondition} onChange={e => setLightCondition(e.target.value)} /><br />

      <label>Head Condition: </label>
      <input type="text" value={headCondition} onChange={e => setHeadCondition(e.target.value)} /><br />

      <label>Media Condition: </label>
      <input type="text" value={mediaCondition} onChange={e => setMediaCondition(e.target.value)} /><br /><br />

      <button onClick={handleFetchSegments} disabled={!videoFile}>Detect Segments</button><br /><br />

      {plotUrl && (
        <div>
          <h4>Marker Presence Plot</h4>
          <img src={plotUrl} alt="Marker Presence Plot" style={{ width: "100%", maxWidth: "800px" }} />
        </div>
      )}

      <h3>Segments</h3>
      {Array(Math.max(starts.length, ends.length, labels.length)).fill(null).map((_, idx) => (
        <div key={`seg-${idx}`} style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
          <div>
            <input
              placeholder="Start"
              value={starts[idx] || ""}
              onChange={e => handleChangeItem(setStarts, starts, idx, e.target.value)}
              style={{ width: "80px" }}
            />
            <span>{starts[idx] !== undefined ? convertToTimestamp(starts[idx]) : ""}</span>
            <button onClick={() => handleRemoveItem(setStarts, starts, idx)}>✕</button>
            <button onClick={() => handleAddItem(setStarts, starts, idx)}>＋</button>
          </div>

          <div>
            <input
              placeholder="End"
              value={ends[idx] || ""}
              onChange={e => handleChangeItem(setEnds, ends, idx, e.target.value)}
              style={{ width: "80px" }}
            />
            <span>{ends[idx] !== undefined ? convertToTimestamp(ends[idx]) : ""}</span>
            <button onClick={() => handleRemoveItem(setEnds, ends, idx)}>✕</button>
            <button onClick={() => handleAddItem(setEnds, ends, idx)}>＋</button>
          </div>

          <div>
            <input
              placeholder="Label"
              value={labels[idx] || ""}
              onChange={e => handleChangeItem(setLabels, labels, idx, e.target.value)}
              style={{ width: "200px" }}
            />
            <button onClick={() => handleRemoveItem(setLabels, labels, idx)}>✕</button>
            <button onClick={() => handleAddItem(setLabels, labels, idx)}>＋</button>
          </div>
        </div>
      ))}

      <br /><br />
      <button onClick={handleSubmit} disabled={starts.length !== ends.length || labels.length !== starts.length}>Submit Final Segments</button>

      {serverResponse && <p>Server: {serverResponse}</p>}
    </div>
  );
};

export default VideoSegmentation;