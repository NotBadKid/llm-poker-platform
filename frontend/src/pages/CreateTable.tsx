import {useState, useEffect} from "react";
import {useNavigate} from "react-router-dom";
import {startGame} from "../services/gameApi.ts";
import type {BotPlayerConfig, BotPlayerConfigUI, GameStartPayload} from "../types/game.ts";
import {AVAILABLE_MODELS} from "../const";
import CustomSelect from "../components/ui/CustomSelect.tsx";
import GameInput from "../components/ui/GameInput.tsx";
import PlayerConfigCard from "../components/ui/PlayerConfigCard.tsx";
import {useGameStore} from "../store/useGameStore.ts";

const CreateTable = () => {
    const navigate = useNavigate();

    const [isLoading, setIsLoading] = useState(false);
    const [smallBlind, setSmallBlind] = useState<number>(100);
    const [bigBlind, setBigBlind] = useState<number>(200);
    const [startingChips, setStartingChips] = useState<number>(10000);
    const [playerCount, setPlayerCount] = useState<number>(4);
    const [numberOfHands, setNumberOfHands] = useState<number>(7);

    const setGameId = useGameStore((state) => state.setGameId);

    const [bots, setBots] = useState<BotPlayerConfigUI[]>([
        {
            id: 1,
            name: "Bot 1",
            model_id: AVAILABLE_MODELS[0].id,
            temperature: 1,
            user_prompt: "",
            useCustomPrompt: false
        },
        {
            id: 2,
            name: "Bot 2",
            model_id: AVAILABLE_MODELS[1].id,
            temperature: 1,
            user_prompt: "",
            useCustomPrompt: false
        },
        {
            id: 3,
            name: "Bot 3",
            model_id: AVAILABLE_MODELS[2].id,
            temperature: 1,
            user_prompt: "",
            useCustomPrompt: false
        },
        {
            id: 4,
            name: "Bot 4",
            model_id: AVAILABLE_MODELS[3].id,
            temperature: 1,
            user_prompt: "",
            useCustomPrompt: false
        },
    ]);

    useEffect(() => {
        setBots((prevBots) => {
            if (playerCount > prevBots.length) {
                return [
                    ...prevBots,
                    {
                        id: playerCount,
                        name: `Bot ${playerCount}`,
                        model_id: AVAILABLE_MODELS[0].id,
                        temperature: 1,
                        user_prompt: "",
                        useCustomPrompt: false,
                    }
                ];
            } else {
                return prevBots.slice(0, playerCount);
            }
        });
    }, [playerCount]);

    const updateBot = (index: number, field: keyof BotPlayerConfigUI, value: string | number | boolean) => {
        const newBots = [...bots];
        // @ts-ignore
        newBots[index][field] = value;
        setBots(newBots);
    };

    const handleStart = async () => {
        setIsLoading(true);

        const payload: GameStartPayload = {
            players: bots.map((bot: BotPlayerConfig) => ({
                name: bot.name,
                model_id: bot.model_id,
                user_prompt: bot.user_prompt || "",
                temperature: bot.temperature
            })),
            initial_stack: startingChips,
            small_blind: smallBlind,
            big_blind: bigBlind,
            number_of_hands: numberOfHands
        };

        console.log("payload:", payload);

        const response = await startGame(payload);

        if (response.game_id) {
            setGameId(response.game_id)
        }

        navigate("/llm-poker-platform/game");
        setIsLoading(false)

    };

    return (
        <div className="min-h-screen p-8 flex flex-col items-center overflow-y-auto">
            <h1 className="text-4xl font-bold absolute top-6 bg-gradient-to-r py-1 from-blue-500 via-violet-600 to-green-300 text-transparent bg-clip-text">Table
                Configuration</h1>

            <div className="max-w-4xl w-full space-y-8 pb-20 mt-18">
                <div className="bg-slate-800 p-6 rounded-2xl shadow-lg border border-slate-700">
                    <h2 className="text-2xl font-semibold mb-4 text-purple-500">1. Game Rules</h2>
                    <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
                        <div className="flex flex-col">
                            <label className="text-gray-400 mb-2">Number of Players</label>
                            <CustomSelect
                                value={playerCount}
                                onChange={(val: number) => setPlayerCount(val)}
                                options={[
                                    {value: 2, label: "2 Players"},
                                    {value: 3, label: "3 Players"},
                                    {value: 4, label: "4 Players"}
                                ]}
                            />
                        </div>
                        <GameInput
                            label="Small Blind"
                            value={smallBlind}
                            onChange={setSmallBlind}
                            min={5}
                            max={500}
                        />
                        <GameInput
                            label="Big Blind"
                            value={bigBlind}
                            onChange={setBigBlind}
                            min={10}
                            max={1000}
                        />
                        <GameInput
                            label="Starting Stack"
                            value={startingChips}
                            onChange={setStartingChips}
                            min={1000}
                            max={100000}
                        />
                        <GameInput
                            label="Number of Hands"
                            value={numberOfHands}
                            onChange={setNumberOfHands}
                            min={3}
                            max={15}
                        />
                    </div>
                </div>

                <div className="bg-slate-800 p-6 rounded-2xl shadow-lg border border-slate-700">
                    <h2 className="text-2xl font-semibold text-purple-500 mb-6 ">2. Players</h2>

                    <div className="grid grid-cols-1 gap-6">
                        {bots.map((bot, index) => (
                            <PlayerConfigCard
                                key={bot.id}
                                index={index}
                                bot={bot}
                                availableModels={AVAILABLE_MODELS}
                                onUpdate={(field, value) => updateBot(index, field, value)}
                            />
                        ))}
                    </div>
                </div>

                <div className="flex justify-end gap-4 pt-4">
                    <button onClick={() => navigate("/llm-poker-platform/")}
                            className="px-10 py-3 rounded-xl border border-gray-600 text-gray-300 hover:bg-gray-800 transition cursor-pointer">Cancel
                    </button>
                    <button
                        onClick={handleStart}
                        disabled={isLoading}
                        className="cursor-pointer px-10 py-3 rounded-xl bg-gradient-to-r from-violet-900 to-violet-700  font-bold text-lg shadow-lg hover:scale-105 transition transform disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isLoading ? "Initializing..." : "Start game"}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default CreateTable;