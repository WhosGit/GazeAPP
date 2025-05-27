import React, { useEffect } from "react";
import FrameConfig from "./components/FrameConfig";
import ExtractRawGaze from "./components/ExtractRawGaze";
import SelectStartEnd from "./components/SelectStartEnd";
import TransformGaze from "./components/TransformGaze";
import VideoSegmentation from "./components/VideoSegmentation";
import Gazeprocess from "./components/Gazeprocess";
import "./App.css"; // 引入全局样式

const App = () => {
  useEffect(() => {}, []);

  return (
    <div className="main-container">
      <h1 className="main-title">Gaze Processing Dashboard</h1>
      <div className="section-card">
        <FrameConfig />
      </div>
      <div className="section-card">
        <ExtractRawGaze />
      </div>
      <div className="section-card">
        <SelectStartEnd />
      </div>
      <div className="section-card">
        <TransformGaze />
      </div>
      <div className="section-card">
        <VideoSegmentation />
      </div>
      <div className="section-card">
        <Gazeprocess />
      </div>
    </div>
  );
};

export default App;
