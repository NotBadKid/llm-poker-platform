import { useState } from "react";
import CustomSelect from "../ui/CustomSelect.tsx";
import type {BotPlayerConfig, Model} from "../../types/game.ts";
import {formatModelName} from "../../utils/formatModelName.ts";

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

const PlayerConfigCard = ({ index, bot, availableModels, onUpdate }: Props) => {
    const [isPromptHidden, setIsPromptHidden] = useState(false);

    return (
        <div className="bg-slate-900 p-5 rounded-xl border border-slate-700 flex flex-col md:flex-row gap-6 transition-all hover:border-purple-500">
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
                    <CustomSelect
                        value={bot.model_id}
                        onChange={(val: string) => onUpdate('model_id', val)}
                        options={availableModels.map(m => ({
                            value: m.model_id,
                            label: formatModelName(m.model_id)
                        }))}
                        className="mt-1"
                    />
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