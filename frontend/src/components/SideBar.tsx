import {ChatLog} from "./ui/ChatLog.tsx";
import type {ChatMessage} from "../types/game.ts";

interface SideBarProps {
    chatLogs: ChatMessage[]
}

const SideBar = ({chatLogs}: SideBarProps) => {
    return (
        <div id='sidebar'>
            <h2>
                Chat / Logs
            </h2>

            <ChatLog log={chatLogs} />

        </div>
    );
};

export default SideBar;
