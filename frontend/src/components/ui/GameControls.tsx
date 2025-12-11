import {useGameStore} from '../../store/useGameStore.ts';
import {pauseGame, resumeGame, stepGame} from "../../services/gameApi.ts";
import {useState} from "react";

const GameControls = () => {
    const gameId = useGameStore((state) => state.gameId);
    const [isPlaying, setIsPlaying] = useState(true);

    if (!gameId) return;

    return (
        <div id="game-flow-controls-container">
            {
                isPlaying ? (
                    <button onClick={() => {
                        pauseGame(gameId);
                        setIsPlaying(false);
                    }}>
                        Pause
                    </button>
                ) : (
                    <div className="flex gap-4">
                        <button onClick={() => {
                            resumeGame(gameId)
                            setIsPlaying(true);
                        }}>
                            Resume
                        </button>
                        <button onClick={() => stepGame(gameId)}>One Step</button>
                    </div>

                )
            }
        </div>
    );
};

export default GameControls;