import React, { useEffect, useState } from "react";
import FrameConfig from "./components/FrameConfig";
import ExtractRawGaze from "./components/ExtractRawGaze";
import SelectStartEnd from "./components/SelectStartEnd";
import TransformGaze from "./components/TransformGaze";
import VideoSegmentation from "./components/VideoSegmentation";  // ✅ Add this line

const App = () => {
  useEffect(() => {}, []);

  return (
    <div>
      <h1>Gaze Processing Dashboard</h1>
      <FrameConfig />
      <ExtractRawGaze />
      <SelectStartEnd />
      <TransformGaze />
      <VideoSegmentation /> {/* ✅ Add this component at the bottom */}
    </div>
  );
};

export default App;
