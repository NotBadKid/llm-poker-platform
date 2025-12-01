import {Route, Routes} from "react-router-dom";
import Home from "./pages/Home.tsx";
import Game from "./pages/Game.tsx";

function App() {

    return (
        <Routes>
            <Route path="/llm-poker-platform" element={<Home/>}/>
            <Route path="/llm-poker-platform/game" element={<Game/>}/>
        </Routes>
    )
}

export default App