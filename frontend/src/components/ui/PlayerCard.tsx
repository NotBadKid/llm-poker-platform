import type {Player} from '../../types/game.ts';
import Card from "./Card.tsx";
import chip from "../../assets/chip.png"

interface PlayerProps {
    player: Player;
    isActive: boolean;
}

const PlayerCard = ({ player, isActive }: PlayerProps) => {
    const activeClass = isActive ? 'border-[#FFF707]' : 'border-white';

    return (
        <div id="player-container" className={activeClass}>
            <h3>{player.name}</h3>

            <div className="flex gap-4">
                <div className="flex gap-2">
                    <Card card={player.holeCards[0]}/>
                    <Card card={player.holeCards[1]}/>
                </div>

                <div className="flex flex-col items-center justify-center ">
                    <img
                        src={chip} alt="tokens"
                        width="32"
                    />
                    <p>{player.chipCount}</p>
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