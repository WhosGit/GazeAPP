// frontend/src/components/ExtractRawGaze.js
import React, { useState } from "react";

const ExtractRawGaze = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [participantName, setParticipantName] = useState("");

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    setSelectedFile(file);
  };

  const handleSubmit = async () => {
    const formData = new FormData();
    if (selectedFile) {
      formData.append("excel", selectedFile);
    }
    formData.append("participant", participantName);

    const response = await fetch("/api/extract_raw_gaze", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    console.log("Response from backend:", data);
  };

  return (
    <div>
      <h2>Extract Raw Gaze</h2>
      <input type="file" accept=".xlsx,.xls" onChange={handleFileChange} />
      <input
        type="text"
        placeholder="Enter participant name"
        value={participantName}
        onChange={(e) => setParticipantName(e.target.value)}
      />
      <button onClick={handleSubmit} disabled={!selectedFile || !participantName}>
        Submit
      </button>
    </div>
  );
};

export default ExtractRawGaze;