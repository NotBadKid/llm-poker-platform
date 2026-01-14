import type {Player} from '../../types/game.ts';
import Card from "./Card.tsx";
import {LuBot, LuCoins} from "react-icons/lu";

interface PlayerProps {
    player: Player;
    isActive: boolean;
}

const PlayerCard = ({ player, isActive }: PlayerProps) => {
    const activeClass = isActive ? 'border-[#66b185] shadow-[0_0_2rem_rgba(0,255,0,0.3)]' : 'border-slate-600';
    const isPlaying = player.status === "playing"

    return (
        <div id="player-container" className={`${activeClass} ${!isPlaying && 'opacity-50'}`}>
            <div className="flex items-center gap-4">
                <div
                    className={`hidden md:block p-2 border rounded-full text-4xl border-white
                    ${isPlaying && 'bg-gradient-to-tl from-emerald-600 to-purple-600'} 
                    ${isActive && 'shadow-[0_0_1rem_rgba(0,255,0,0.5)]'}`}
                >
                    <LuBot/>
                </div>
                <div className="flex flex-col min-w-0">
                    <h3>{player.name}</h3>
                    <div className='flex items-center text-amber-300'>
                        <LuCoins className="text-2xl"/>
                        <p className='text-lg pl-1'>{player.chipCount}</p>
                    </div>
                </div>
            </div>

            <div className="flex gap-4 mt-4">
                <div className="flex gap-2">
                    <Card card={player.holeCards[0]}/>
                    <Card card={player.holeCards[1]}/>
                </div>
            </div>

            {
                player.currentBet !== 0 && <div id='current-bet-container' className={activeClass}>
                    <p>${player.currentBet}</p>
                </div>
            }
        </div>
    );
};

export default PlayerCard;