import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { applyTheme, initTelegram, tg } from "./lib/telegram";
import "./styles.css";

initTelegram();
applyTheme();
tg?.onEvent?.("themeChanged", applyTheme);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
