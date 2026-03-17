import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import Lesson from "./Lesson";
// import "../../../static/styles.css"

createRoot(document.getElementById("lesson")).render(
  <StrictMode>
    <Lesson/>
  </StrictMode>
);
