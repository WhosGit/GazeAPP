import React, { useState } from "react";

const FrameConfig = () => {
  const [points, setPoints] = useState([]);
  const [imagePath, setImagePath] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [responseMessage, setResponseMessage] = useState("");
  const [transformedImage, setTransformedImage] = useState(null);
  const [transformedPoints, setTransformedPoints] = useState([]);

  const labels = [
    "Screen Top-Left",
    "Screen Top-Right",
    "Screen Bottom-Right",
    "Screen Bottom-Left",
    "Marker Top-Left",
    "Marker Top-Right",
    "Marker Bottom-Left",
    "Marker Bottom-Right"
  ];

  const handleImageClick = (e) => {
    if (points.length < 8) {
      const newPoint = { x: e.nativeEvent.offsetX, y: e.nativeEvent.offsetY };
      setPoints([...points, newPoint]);
    }
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      const imageUrl = URL.createObjectURL(file);
      setImagePath(imageUrl);
      setPoints([]);
      setTransformedImage(null);
      setTransformedPoints([]);

      // Optional: send image to backend for marker recognition
      const formData = new FormData();
      formData.append("image", file);
      const res = await fetch("/api/marker_recognition", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data.message) {
        setResponseMessage(data.message);
      }
    }
  };

  const handleUndo = () => {
    setPoints(points.slice(0, -1));
  };

  const handleSubmit = async () => {
    const formData = new FormData();
    formData.append("image", selectedFile);
    formData.append("points", JSON.stringify(points));

    const response = await fetch("/api/frame_config", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    setResponseMessage(data.message || "Submitted successfully");
    if (data.transformed_image) {
      setTransformedImage("data:image/png;base64," + data.transformed_image);
    }
    if (data.transformed_points) {
      setTransformedPoints(data.transformed_points);
    }
  };

  return (
    <div>
      <h2>Frame Configuration</h2>
      <p style={{ color: "#636e72" }}>Upload an image and click to mark 8 points in order:</p>
      <ul style={{ marginBottom: 10 }}>
        {labels.map((label, i) => (
          <li key={i}>{label}</li>
        ))}
      </ul>
      <input type="file" accept="image/*" onChange={handleFileChange} />
      <br />
      {imagePath && (
        <div style={{ position: "relative", display: "inline-block", margin: "18px 0" }}>
          <img
            src={imagePath}
            alt="Annotate"
            onClick={handleImageClick}
            style={{
              cursor: "crosshair",
              width: "500px",
              height: "auto",
              borderRadius: "10px",
              boxShadow: "0 2px 10px rgba(44,62,80,0.08)"
            }}
          />
          {points.map((point, index) => (
            <div
              key={index}
              title={labels[index]}
              style={{
                position: "absolute",
                top: point.y,
                left: point.x,
                width: "16px",
                height: "16px",
                backgroundColor: "#e74c3c",
                border: "2px solid #fff",
                borderRadius: "50%",
                transform: "translate(-50%, -50%)",
                zIndex: 2,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                boxShadow: "0 1px 4px rgba(0,0,0,0.13)"
              }}
            >
              <span
                style={{
                  color: "#fff",
                  fontWeight: "bold",
                  fontSize: "11px",
                  textShadow: "0 1px 2px #000"
                }}
              >
                {index + 1}
              </span>
            </div>
          ))}
        </div>
      )}
      <div>
        <p style={{ margin: "10px 0 4px 0" }}>Selected points:</p>
        <ul>
          {points.map((point, index) => (
            <li key={index}>
              {labels[index]}: ({point.x}, {point.y})
            </li>
          ))}
        </ul>
      </div>
      <div style={{ margin: "10px 0" }}>
        <button onClick={handleUndo} disabled={points.length === 0}>
          Undo
        </button>
        <button onClick={handleSubmit} disabled={points.length !== 8}>
          Submit
        </button>
      </div>
      {responseMessage && <p style={{ color: "#0984e3" }}>Server response: {responseMessage}</p>}
      {transformedImage && (
        <div style={{ marginTop: 18 }}>
          <h3>Transformed Image</h3>
          <img
            src={transformedImage}
            alt="Transformed"
            style={{
              width: "500px",
              height: "auto",
              borderRadius: "10px",
              boxShadow: "0 2px 10px rgba(44,62,80,0.08)"
            }}
          />
          <h4>Transformed Marker Points</h4>
          <ul>
            {transformedPoints.map((pt, i) => (
              <li key={i}>
                {labels[i + 4]}: ({pt.x.toFixed(1)}, {pt.y.toFixed(1)})
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default FrameConfig;
