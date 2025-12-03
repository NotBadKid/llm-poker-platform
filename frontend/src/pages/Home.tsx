import {useNavigate} from "react-router-dom";
import HomeButton from "../components/home/HomeButton.tsx";

const Home = () => {
    const navigate = useNavigate();

    return (
        <div className="flex flex-col items-center justify-center h-screen">
            <h1 className="text-6xl font-bold absolute top-24 bg-gradient-to-r from-blue-600 via-green-500 to-indigo-400 text-transparent bg-clip-text">Poker LLM</h1>

            <div className="flex flex-col gap-4 mt-24">
                <HomeButton
                    content="Create Table"
                    onClick={() => navigate("/llm-poker-platform/create-table")}
                    className="bg-violet-700"
                />
                <HomeButton
                    content="Join Table"
                    onClick={() => {
                    }}
                    disabled
                />
                <HomeButton
                    content="LLM statistics"
                    onClick={() => {
                    }}
                    disabled
                />
                <HomeButton
                    content="Player statistics"
                    onClick={() => {
                    }}
                    disabled
                />

            </div>
        </div>
    );
};

export default Home;