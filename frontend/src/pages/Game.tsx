import {useGameSocket} from "../hooks/useGameSocket.ts";
import {useGameStore} from "../store/useGameStore.ts";
import GameControls from "../components/ui/GameControls.tsx";
import GameContainer from "../components/ui/GameContainer.tsx";
import ChatContainer from "../components/ui/ChatContainer.tsx";

const Game = () => {
    const {
        pot,
        communityCards,
        players,
        activePlayer,
        chatLog,
        gameId,
    } = useGameStore((state) => state);

    useGameSocket(gameId);

    return (
        <main className="text-white flex flex-col gap-12">
            <div className='flex justify-between'>
                <h1 className='text-xl md:text-4xl font-bold tracking-wider'>
                    LLM Poker Platform
                </h1>
                <GameControls/>
            </div>
            <div className='flex gap-4 max-lg:flex-col h-[75vh]'>
                <GameContainer pot={pot} communityCards={communityCards} players={players} activePlayer={activePlayer}/>
                <ChatContainer chatLogs={chatLog}/>
            </div>
        </main>
    );
};

export default Game;
