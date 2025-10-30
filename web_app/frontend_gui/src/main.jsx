import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import Tests from "./pages/Tests.jsx";

const App = () => {
    return (
        <Tests />
    )
}

createRoot(document.getElementById('root')).render(
    <StrictMode>
        <App />
    </StrictMode>,
)
