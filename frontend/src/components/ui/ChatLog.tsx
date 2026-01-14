import type {ChatMessage} from '../../types/game';

interface ChatLogProps {
    log: ChatMessage[];
}

export const ChatLog = ({ log }: ChatLogProps) => {
    const COLORS = ['#ff6900', '#7ccf00', '#00a6f4', '#c800de'];
    const uniquePlayers = Array.from(new Set(log.map(m => m.player)));
    const playerColorMap: Record<string, string> = {};

    uniquePlayers.forEach((playerName, index) => {
        playerColorMap[playerName] = COLORS[index % COLORS.length];
    });

    return (
        <div className="h-full p-6 overflow-y-auto font-mono min-h-0 max-lg:max-h-[50vh]">
            <div className="flex flex-col-reverse gap-2">
                {[...log].reverse().map((entry, index) => (
                    <p key={index} className="text-base">
                        <span className='font-bold'
                            style={{color: playerColorMap[entry.player]}}>
                            <span className=''>
                                {entry.player}
                            </span> [{entry.action}{entry.amount !== 0 && ` $${entry.amount}`}]:
                        </span>
                        <span className="text-gray-200 ml-2">{entry.message}</span>
                    </p>
                ))}
            </div>
        </div>
    );
};