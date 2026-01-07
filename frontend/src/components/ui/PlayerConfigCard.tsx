import {useState} from "react";
import type {BotPlayerConfig, Model} from "../../types/game.ts";
import Modal from "./Modal.tsx";
import {LuSearch} from "react-icons/lu";
import {ExternalLink} from "lucide-react";

export interface BotUIConfig extends BotPlayerConfig {
    id: number;
    useCustomPrompt: boolean;
}

interface Props {
    index: number;
    bot: BotUIConfig;
    availableModels: Model[];
    onUpdate: (field: keyof BotUIConfig, value: string | number | boolean) => void;
}

const PlayerConfigCard = ({index, bot, availableModels, onUpdate}: Props) => {
    const [isPromptHidden, setIsPromptHidden] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState<string>("")

    const openModal = () => setIsModalOpen(true);
    const closeModal = () => {
        setIsModalOpen(false)
        setSearchQuery("")
    };
    const filteredModels: Model[] = availableModels.filter((model) => {
        const query = searchQuery.toLowerCase();

        return (
            model.name.toLowerCase().includes(query) ||
            model.model_id.toLowerCase().includes(query) ||
            model.description.toLowerCase().includes(query)
        )
    })

    return (
        <div
            className="bg-slate-900 p-5 rounded-xl border border-slate-700 flex flex-col md:flex-row gap-6 transition-all hover:border-purple-500">
            <div className="w-full md:w-1/3 flex flex-col gap-4">
                <h3 className="text-xl font-bold flex items-center gap-2">
                    <span className="bg-slate-800 text-purple-500 px-2 py-1 rounded text-sm">#{index + 1}</span>

                </h3>

                <div>
                    <label className="text-xs text-gray-500 uppercase font-bold">Name</label>
                    <input
                        type="text"
                        value={bot.name}
                        onChange={(e) => onUpdate('name', e.target.value)}
                        className="w-full bg-slate-800 border border-slate-600 rounded p-2 mt-1 text-sm focus:border-purple-500 outline-none placeholder-gray-600"
                        placeholder={`Bot ${index + 1}`}
                    />
                </div>

                <div>
                    <label className="text-xs text-gray-500 uppercase font-bold">Model</label>
                    <button
                        onClick={openModal}
                        className="w-full p-3 rounded-lg cursor-pointer bg-slate-900 border border-slate-600 text-left overflow-hidden flex items-center justify-between outline-none hover:border-purple-500"
                    >
                        <span className="whitespace-nowrap overflow-x-hidden">
                            {bot.name}
                        </span>

                        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"/>
                        </svg>

                    </button>

                    <Modal
                        isOpen={isModalOpen}
                        onClose={closeModal}
                        title="Select LLM Model"
                    >
                        <div className='border-b border-slate-600 p-6'>
                            <div className='relative'>
                                <LuSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400"/>
                                <input
                                    className="w-full pl-10 border bg-slate-700 border-slate-600 rounded-lg p-2 focus:border-purple-500 outline-none transition placeholder:text-slate-400 hover:border-slate-500"
                                    type="text"
                                    placeholder="Search models by name, ID, or description..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                />
                            </div>
                        </div>
                        <div className='h-full overflow-y-auto p-8 flex flex-col gap-6 custom-scrollbar'>
                            {
                                filteredModels.map((model: Model) => (
                                    <div
                                        key={model.model_id}
                                        className={`bg-slate-700 rounded-lg p-4 cursor-pointer hover:bg-slate-600 transition-colors border hover:border-purple-500 ${bot.model_id === model.model_id ? "border-purple-500" : "border-slate-600"}`}
                                        onClick={() => {
                                            onUpdate('model_id', model.model_id)
                                            closeModal()
                                        }}
                                    >
                                        <div className="flex items-center gap-2 mb-1">
                                            <h3 className="truncate text-lg">{model.name}</h3>
                                            <a
                                                href={model.open_router_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                onClick={(e) => e.stopPropagation()}
                                                className="text-purple-400 hover:text-purple-300 flex-shrink-0"
                                            >
                                                <ExternalLink className="w-5 h-5"/>
                                            </a>
                                        </div>

                                        <p className="text-slate-400 mb-3 font-mono">
                                            {model.model_id}
                                        </p>

                                        <p className="text-sm text-slate-300 mb-6 line-clamp-3">
                                            {model.description}
                                        </p>

                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                                            <div>
                                                <div className="text-slate-400">
                                                    Parameters
                                                </div>
                                                <div className="text-base">
                                                    {model.parameters ? `${model.parameters / 1000000000}B` : "Unknown"}
                                                </div>
                                            </div>
                                            <div>
                                                <div className="text-slate-400">
                                                    Context Window
                                                </div>
                                                <div className="text-base text-white">
                                                    {(model.context / 1000).toFixed(0)}k tokens
                                                </div>
                                            </div>
                                            <div>
                                                <div className="text-slate-400">
                                                    Input Price
                                                </div>
                                                <div className="text-base text-purple-400">
                                                    ${model.input_price.toFixed(2)}/1M
                                                </div>
                                            </div>
                                            <div>
                                                <div className="text-slate-400">
                                                    Output Price
                                                </div>
                                                <div className="text-base text-purple-400">
                                                    ${model.output_price.toFixed(2)}/1M
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))
                            }
                        </div>
                    </Modal>
                </div>

                <div>
                    <div className="flex justify-between">
                        <label className="text-xs text-gray-500 uppercase font-bold">Temperature</label>
                        <span className="text-xs text-purple-500 font-mono">{bot.temperature}</span>
                    </div>
                    <input
                        type="range"
                        min="0.05"
                        max="2"
                        step="0.05"
                        value={bot.temperature}
                        onChange={(e) => onUpdate('temperature', parseFloat(e.target.value))}
                        className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer mt-2 accent-purple-500"
                    />
                </div>
            </div>

            <div className="w-full md:w-2/3 flex flex-col border-t md:border-t-0 md:border-l border-slate-700 md:pl-6 pt-4 md:pt-0">
                <div className="flex justify-between items-center mb-2">
                    <label className="flex items-center space-x-2 cursor-pointer select-none group">
                        <input
                            type="checkbox"
                            checked={bot.useCustomPrompt}
                            onChange={(e) => onUpdate('useCustomPrompt', e.target.checked)}
                            className="w-4 h-4 accent-purple-600 rounded cursor-pointer"
                        />
                        <span className={`text-sm tracking-wide font-semibold transition-colors ${bot.useCustomPrompt ? 'text-purple-500' : 'text-gray-500 group-hover:text-gray-400'}`}>
                            Custom Playstyle
                        </span>
                    </label>

                    {bot.useCustomPrompt && (
                        <label className="flex items-center space-x-2 cursor-pointer select-none animate-fadeIn">
                            <span className="text-[0.9rem] text-gray-400">Private mode</span>
                            <input
                                type="checkbox"
                                checked={isPromptHidden}
                                onChange={() => setIsPromptHidden(!isPromptHidden)}
                                className="w-4 h-4 accent-slate-500 rounded cursor-pointer"
                            />
                        </label>
                    )}
                </div>

                <div className="relative flex-grow">
                    {bot.useCustomPrompt ? (
                        <textarea
                            value={bot.user_prompt}
                            onChange={(e) => onUpdate('user_prompt', e.target.value)}
                            placeholder="Instructions for how the LLM should behave (e.g., always go all-in, insult opponents…)"
                            className={`w-full h-full min-h-[160px] bg-slate-800 border border-slate-600 rounded-lg p-3 text-sm resize-none focus:outline-none focus:ring-1 focus:ring-purple-500 transition-all duration-300 
                                ${isPromptHidden ? 'blur-md select-none pointer-events-none opacity-50' : 'opacity-100'}
                            `}
                        />
                    ) : (
                        <div className="w-full h-full min-h-[160px] bg-slate-800/50 border border-slate-700 border-dashed rounded-lg flex items-center justify-center text-gray-500 text-sm italic p-4 text-center">
                            The default system prompt will be used. <br/>
                            Enable ‘Custom System Prompt’ to modify your bot’s playstyle.
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default PlayerConfigCard;