import React, { useEffect, useState } from "react";

const RESULT_FILES = [
  { name: "video.mp4", label: "Video Result", type: "video" },
  { name: "gaze.npy", label: "Gaze NPY", type: "binary" },
  { name: "segments_25fps.json", label: "Segment JSON", type: "json" },
  { name: "tags.json", label: "Tag JSON", type: "json" }
];

export function Gazeprocess() {
  const [results, setResults] = useState({});
  const [customFiles, setCustomFiles] = useState({});
  const [submitMsg, setSubmitMsg] = useState("");
  const [outputFolder, setOutputFolder] = useState("session_folder/processed_gaze");

  // 检查单个文件是否存在
  const checkFile = async (file) => {
    try {
      const res = await fetch(`/api/results/${file.name}`);
      if (res.status === 404) {
        setResults(prev => ({
          ...prev,
          [file.name]: null
        }));
      } else {
        setResults(prev => ({
          ...prev,
          [file.name]: true
        }));
      }
    } catch {
      setResults(prev => ({
        ...prev,
        [file.name]: null
      }));
    }
  };

  // 加载后端输出的结果
  useEffect(() => {
    RESULT_FILES.forEach(checkFile);
    // 监听 gaze.npy 生成事件
    const gazeHandler = () => {
      const gazeFile = RESULT_FILES.find(f => f.name === "gaze.npy");
      if (gazeFile) checkFile(gazeFile);
    };
    window.addEventListener("gaze_npy_uploaded", gazeHandler);

    // 监听 video.mp4 生成事件
    const videoHandler = () => {
      const videoFile = RESULT_FILES.find(f => f.name === "video.mp4");
      if (videoFile) checkFile(videoFile);
    };
    window.addEventListener("video_uploaded", videoHandler);

    // 监听 segments_25fps.json 生成事件
    const segHandler = () => {
      const segFile = RESULT_FILES.find(f => f.name === "segments_25fps.json");
      if (segFile) checkFile(segFile);
    };
    window.addEventListener("segments_25fps_uploaded", segHandler);

    return () => {
      window.removeEventListener("gaze_npy_uploaded", gazeHandler);
      window.removeEventListener("video_uploaded", videoHandler);
      window.removeEventListener("segments_25fps_uploaded", segHandler);
    };
    // eslint-disable-next-line
  }, []);

  // 处理用户自定义上传
  const handleCustomFile = (e, fileName) => {
    setCustomFiles({
      ...customFiles,
      [fileName]: e.target.files[0]
    });
  };

  // 上传单个自定义 result 到后端
  const uploadCustomResult = async (idx) => {
    const fileInfo = RESULT_FILES[idx];
    const file = customFiles[fileInfo.name];
    if (!file) return alert("请选择文件");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch(`/api/upload_user_result/${idx}`, {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      if (!res.ok) {
        alert(data.error || "上传失败");
      } else {
        alert(data.message);
        // 上传成功后重新检查该文件
        checkFile(fileInfo);
      }
    } catch (err) {
      alert("Upload failed: " + err.message);
    }
  };

  // 提交所有 result 进行后端处理
  const handleSubmitAll = async () => {
    setSubmitMsg("Uploading...");
    try {
      const res = await fetch("/api/submit_final_results", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ output_folder: outputFolder })
      });
      const data = await res.json();
      setSubmitMsg(data.message || "Upload successful");
    } catch {
      setSubmitMsg("Upload failed");
    }
  };

  return (
    <div>
      <h2>Backend Output Results</h2>
      {RESULT_FILES.map((file, idx) => (
        <div key={file.name} style={{
          marginBottom: "1em",
          border: "1px solid #e1e8ed",
          padding: 14,
          borderRadius: 8,
          background: "#f8fafd"
        }}>
          <h4 style={{ margin: 0, color: "#636e72" }}>{file.label} <span style={{ fontWeight: "normal", color: "#b2bec3" }}>({file.name})</span></h4>
          {results[file.name] === undefined
            ? <span style={{ color: "#636e72" }}>Loading...</span>
            : results[file.name] === null
              ? <span style={{ color: "#e17055" }}>Please upload file</span>
              : <span style={{ color: "#00b894" }}>Uploaded</span>
          }
          <div style={{ marginTop: 8 }}>
            <input
              type="file"
              onChange={e => handleCustomFile(e, file.name)}
              style={{ marginRight: 8 }}
            />
            <button onClick={() => uploadCustomResult(idx)}>
              Upload custom {file.label}
            </button>
          </div>
        </div>
      ))}
      <div style={{ marginTop: 20, display: "flex", alignItems: "center", gap: 12 }}>
        <input
          type="text"
          value={outputFolder}
          onChange={e => setOutputFolder(e.target.value)}
          style={{ width: 320, marginRight: 8 }}
          placeholder="Output folder path"
        />
        <button onClick={handleSubmitAll} style={{ fontWeight: "bold" }}>
          Submit all results for backend processing
        </button>
      </div>
      {submitMsg && <div style={{ marginTop: 10, color: "#0984e3" }}>{submitMsg}</div>}
    </div>
  );
}

export default Gazeprocess;
