import type {CardId, Player} from "../../types/game.ts";
import PokerTable from "./PokerTable.tsx";
import PlayerCard from "./PlayerCard.tsx";

interface Props {
    pot: number,
    communityCards: CardId[],
    players: Player[],
    activePlayer: string | null,
}

const GameContainer = ({pot, communityCards, players, activePlayer}: Props) => {
    const playerPositions: string[] = [
        'top-12 left-12',
        'top-12 right-12',
        'bottom-12 left-12',
        'bottom-12 right-12',
    ];

    return (
        <div
            className="flex-2 border relative rounded-2xl bg-gradient-to-br from-slate-900/50 to-slate-950/50 border-slate-700 flex items-center flex-col">

            <PokerTable
                pot={pot}
                communityCards={communityCards}
            />
            <div className="grid grid-cols-2 grid-rows-2 gap-2 mt-8">
                {players.map((player, index) => (
                    <div
                        key={player.name}
                        className={`static md:absolute ${playerPositions[index] || 'top-1/2 left-1/2'}`}
                    >
                        <PlayerCard
                            player={player}
                            isActive={player.name === activePlayer}
                        />
                    </div>
                ))}
            </div>

        </div>
    );
};

export default GameContainer;
