import { scan } from "react-scan"
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from "./App.js";

scan({
    enabled: true,
    });

createRoot(document.getElementById('root')!).render(
    <StrictMode>
        <App />
    </StrictMode>,
)
