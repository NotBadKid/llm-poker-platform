import {ChatLog} from "./ChatLog.tsx";
import type {ChatMessage} from "../../types/game.ts";
import {LuMessageSquare} from "react-icons/lu";

interface Props {
    chatLogs: ChatMessage[],
}

const ChatContainer = ({chatLogs,}: Props) => {
    return (
        <div className='flex-1 border bg-gradient-to-b from-slate-900 to-slate-950 border-slate-700 rounded-2xl flex flex-col'>
            <div className="flex gap-4 p-6 border-b border-slate-700">
                <LuMessageSquare className=' text-emerald-400 text-4xl'/>
                <h2 className="font-semibold text-2xl">
                    Live Chat / Logs
                </h2>
            </div>
            <div className="flex-1 overflow-y-auto custom-scrollbar custom-scrollbar-emerald">
                <ChatLog log={chatLogs}/>
            </div>
        </div>
    );
};

export default ChatContainer;
