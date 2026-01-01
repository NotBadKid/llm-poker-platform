import {useState, useEffect} from "react";
import {useNavigate} from "react-router-dom";
import {startGame} from "../services/gameApi.ts";
import type {BotPlayerConfig, BotPlayerConfigUI, GameStartPayload, Model} from "../types/game.ts";
import {DEFAULT_AVAILABLE_MODELS} from "../const";
import CustomSelect from "../components/ui/CustomSelect.tsx";
import GameInput from "../components/ui/GameInput.tsx";
import PlayerConfigCard from "../components/ui/PlayerConfigCard.tsx";
import {useGameStore} from "../store/useGameStore.ts";
import ConnectedButton from "../components/ui/ConnectedButton.tsx";
import Tooltip from "../components/ui/Tooltip.tsx";
import {formatModelName} from "../utils/formatModelName.ts";
import {getModels} from "../services/modelsApi.ts";

const CreateTable = () => {
    const navigate = useNavigate();

    const [isLoading, setIsLoading] = useState(false);
    const [smallBlind, setSmallBlind] = useState<number>(100);
    const [bigBlind, setBigBlind] = useState<number>(200);
    const [startingChips, setStartingChips] = useState<number>(10000);
    const [playerCount, setPlayerCount] = useState<number>(4);
    const [numberOfHands, setNumberOfHands] = useState<number>(7);
    const [selectedFormat, setSelectedFormat] = useState<string>("Any (Text)")
    const [modelsList, setModelsList] = useState<Model[]>(DEFAULT_AVAILABLE_MODELS);

    const setGameId = useGameStore((state) => state.setGameId);

    const [bots, setBots] = useState<BotPlayerConfigUI[]>([
        {
            id: 1,
            name: formatModelName(modelsList[0].model_id),
            model_id: modelsList[0].model_id,
            temperature: 1,
            user_prompt: "",
            useCustomPrompt: false
        },
        {
            id: 2,
            name: formatModelName(modelsList[1].model_id),
            model_id: modelsList[1].model_id,
            temperature: 1,
            user_prompt: "",
            useCustomPrompt: false
        },
        {
            id: 3,
            name: formatModelName(modelsList[2].model_id),
            model_id: modelsList[2].model_id,
            temperature: 1,
            user_prompt: "",
            useCustomPrompt: false
        },
        {
            id: 4,
            name: formatModelName(modelsList[3].model_id),
            model_id: modelsList[3].model_id,
            temperature: 1,
            user_prompt: "",
            useCustomPrompt: false
        },
    ]);

    useEffect(() => {
        const fetchModels = async () => {
            setIsLoading(true);

            const response: Model[] = await getModels(selectedFormat === "JSON")

            if (response) {
                setModelsList(response);
            }
            setIsLoading(false);
        }
        fetchModels();
    }, [selectedFormat])

    useEffect(() => {
        setBots((prevBots) => {
            if (playerCount > prevBots.length) {
                return [
                    ...prevBots,
                    {
                        id: playerCount,
                        name: `Bot ${playerCount}`,
                        model_id: modelsList[0].model_id,
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
        setBots(prevBots => prevBots.map((bot, i) => {
            if (i !== index) return bot;

            const updatedBot = { ...bot, [field]: value };

            if (field === 'model_id' && typeof value === 'string') {
                updatedBot.name = formatModelName(value);
            }

            return updatedBot;
        }));
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
            number_of_hands: numberOfHands,
            structured_output: selectedFormat === "JSON"
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
        <div id="create-table-page">
            <h1 className="text-4xl font-bold absolute top-6 bg-gradient-to-r py-1 from-blue-500 via-violet-600 to-green-300 text-transparent bg-clip-text">Table
                Configuration</h1>

            <div className="max-w-4xl w-full space-y-8 pb-20 mt-18">
                <section>
                    <h2 className="mb-4">1. Game Rules</h2>
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
                </section>
                <section>
                    <h2 className='mb-4'>2. Developer settings</h2>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div>
                            <div className='flex gap-2 items-center'>
                                <label className='text-gray-400'>LLM output format</label>
                                <Tooltip>
                                    <b>This setting controls whether the model is forced to return a response in a specific format. </b><br/>

                                    Any (Text) allows the widest range of models. <br/>
                                    JSON attempts to enforce a structured JSON response, which may favor programming-oriented models and may also cause errors. <br/>

                                    We recommend keeping Any (Text). There is no visual difference.
                                </Tooltip>
                            </div>
                            <ConnectedButton
                                options={["Any (Text)", "JSON"]}
                                className='mt-3'
                                currentValue={selectedFormat}
                                onChange={(newValue: string) => {
                                    setSelectedFormat(newValue)
                                }}
                            />
                        </div>
                    </div>
                </section>

                <section>
                    <h2 className="mb-6">3. Players</h2>

                    <div className="grid grid-cols-1 gap-6">
                        {bots.map((bot, index) => (
                            <PlayerConfigCard
                                key={bot.id}
                                index={index}
                                bot={bot}
                                availableModels={modelsList}
                                onUpdate={(field, value) => updateBot(index, field, value)}
                            />
                        ))}
                    </div>
                </section>

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