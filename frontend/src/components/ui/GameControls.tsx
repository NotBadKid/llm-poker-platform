import {useGameStore} from '../../store/useGameStore.ts';
import {pauseGame, resumeGame, stepGame} from "../../services/gameApi.ts";
import {useState} from "react";
import {LuPause} from "react-icons/lu";
import {RxResume} from "react-icons/rx";
import {MdPlusOne} from "react-icons/md";

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
                        <div className="flex items-center gap-2">
                            <LuPause />
                            <span className="hidden md:block">Pause</span>
                        </div>

                    </button>
                ) : (
                    <div className="flex gap-4">
                        <button onClick={() => {
                            resumeGame(gameId)
                            setIsPlaying(true);
                        }}>
                            <div className="flex items-center gap-2">
                                <RxResume />
                                <span className="hidden md:block">Resume</span>
                            </div>
                        </button>
                        <button onClick={() => stepGame(gameId)}>
                            <div className="flex items-center gap-2">
                                <MdPlusOne />
                                <span className="hidden md:block">One step</span>
                            </div>
                        </button>
                    </div>

                )
            }
        </div>
    );
};

export default GameControls;