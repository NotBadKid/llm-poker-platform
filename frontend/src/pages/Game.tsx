import {useGameSocket} from "../hooks/useGameSocket.ts";
import {useGameStore} from "../store/useGameStore.ts";
import NavBar from "../components/NavBar.tsx";
import SideBar from "../components/SideBar.tsx";
import PokerTable from "../components/ui/PokerTable.tsx";
import PlayerCard from "../components/ui/PlayerCard.tsx";
import GameControls from "../components/ui/GameControls.tsx";

const Game = () => {
    const {
        pot,
        communityCards,
        players,
        activePlayer,
        chatLog,
        gameId
    } = useGameStore((state) => state);

    useGameSocket(gameId);

    const playerPositions: string[] = [
        'bottom-32 left-18',
        'top-32 left-18',
        'bottom-32 right-18',
        'top-32 right-18',
    ];


    return (
        <main className="text-4xl w-full h-screen overflow-hidden text-white pr-[300px]">
            <NavBar />
            <SideBar chatLogs={chatLog} />

            <div className="w-full h-full relative">

                <GameControls/>

                <PokerTable
                    pot={pot}
                    communityCards={communityCards}
                />

                {players.map((player, index) => (
                    <div
                        key={player.name}
                        className={`absolute ${playerPositions[index] || 'top-1/2 left-1/2'}`}
                    >
                        <PlayerCard
                            player={player}
                            isActive={player.name === activePlayer}
                        />
                    </div>
                ))}
            </div>
        </main>
    );
};

export default Game;
