import {Route, Routes} from "react-router-dom";
import Home from "./pages/Home.tsx";
import Game from "./pages/Game.tsx";
import CreateTable from "./pages/CreateTable.tsx";

function App() {


    return (
        <Routes>
            <Route path="/llm-poker-platform" element={<Home/>}/>
            <Route path="/llm-poker-platform/game" element={<Game/>}/>

            <Route path="/llm-poker-platform/create-table" element={<CreateTable/>}/>
        </Routes>
    )
}

export default App