import { useNavigate } from "react-router-dom";
import { startGame } from "../services/gameApi.ts";

const Home = () => {
    const navigate = useNavigate();

    const handleStartLLMTable = async () => {
        try {
            console.log("Inicjowanie gry...");

            await startGame();

            navigate("/llm-poker-platform/game");
        } catch (error) {
            console.error("Błąd startu:", error);
            alert("Nie udało się wystartować stołu. Sprawdź backend.");
        }
    };

    return (
        <div className="flex flex-col items-center justify-center h-screen bg-slate-900 text-white gap-10">
            <h1 className="text-6xl font-bold text-green-500">Poker LLM</h1>

            <div className="flex flex-col gap-4">
                <button
                    onClick={handleStartLLMTable}
                    className="px-10 py-5 bg-gradient-to-r from-green-600 to-green-800 rounded-2xl text-3xl font-bold shadow-lg hover:scale-105 transition transform"
                >
                    Start
                </button>

                <button
                    onClick={() => navigate("/settings")}
                    className="px-10 py-4 bg-slate-700 rounded-2xl text-xl hover:bg-slate-600 transition"
                >
                    Settings
                </button>
            </div>
        </div>
    );
};

export default Home;