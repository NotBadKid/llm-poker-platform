import type {ChatMessage} from '../../types/game';

interface ChatLogProps {
    log: ChatMessage[];
}

export const ChatLog = ({ log }: ChatLogProps) => {
    return (
        <div className="h-full p-4 overflow-y-auto font-mono">
            <div className="pt-4 flex flex-col-reverse gap-2">
                {[...log].reverse().map((entry, index) => (
                    <p key={index} className="text-sm">
                        <span className="text-[#FFF707]">
                            <span className='font-bold'>
                                {entry.player}
                            </span> [{entry.action}{entry.amount && ` $${entry.amount}`}]:
                        </span>
                        <span className="text-gray-200 ml-2">{entry.message}</span>
                    </p>
                ))}
            </div>
        </div>
    );
};