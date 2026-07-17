// Bootstraps React into #root. The one imperative line in the whole app.
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
