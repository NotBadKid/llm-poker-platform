import { useGameStore } from "./store/useGameStore.ts";
import { useGameSocket } from "./hooks/useGameSocket.ts"; // Twój hook do socketów
import { startGame } from "./services/gameApi.ts"; // Twoja funkcja do POSTa
import NavBar from "./components/NavBar.tsx";
import SideBar from "./components/SideBar.tsx";
import PokerTable from "./components/ui/PokerTable.tsx";
import PlayerCard from "./components/ui/PlayerCard.tsx";

function App() {
    // 1. Uruchamiamy nasłuchiwanie WebSocket (automatycznie po załadowaniu strony)
    useGameSocket();

    // 2. Pobieramy aktualny stan gry ze Store (to się zaktualizuje samo jak przyjdzie event z socketa)
    const {
        pot,
        communityCards,
        players,
        activePlayer, // Upewnij się, że w types/game.ts masz activePlayerId (zgodnie z backendem)
        chatLog
    } = useGameStore((state) => state);

    // Pozycje dla graczy (zakładamy max 4 graczy dla tego układu)
    const playerPositions: string[] = [
        'top-32 left-18',
        'top-32 right-18',
        'bottom-32 left-18',
        'bottom-32 right-18',
    ];

    // Funkcja do odpalenia gry
    const handleStartGame = async () => {
        try {
            await startGame();
            console.log("Wysłano żądanie startu gry");
        } catch (error) {
            alert("Błąd startu gry - sprawdź czy backend działa!");
        }
    };

    return (
        <main className="text-4xl relative w-full h-screen overflow-hidden bg-slate-900 text-white">

            {/* Przycisk START (Widoczny tylko jeśli nie ma jeszcze graczy/gry) */}
            {players.length === 0 && (
                <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
                    <button
                        onClick={handleStartGame}
                        className="px-8 py-4 bg-green-600 hover:bg-green-500 text-white font-bold rounded-full shadow-2xl text-2xl transition transform hover:scale-105"
                    >
                        START GAME
                    </button>
                </div>
            )}

            <NavBar />

            {/* Przekazujemy logi do Sidebara */}
            <SideBar chatLogs={chatLog} />

            <div className="w-full h-full relative">

                {/* Stół i karty wspólne */}
                <PokerTable
                    pot={pot}
                    communityCards={communityCards}
                />

                {/* Gracze rozmieszczeni absolutnie wokół stołu */}
                {players.map((player, index) => (
                    <div
                        key={player.name}
                        className={`absolute ${playerPositions[index] || 'top-1/2 left-1/2'}`}
                    >
                        <PlayerCard
                            player={player}
                            // Sprawdzamy czy nazwa gracza == ID aktywnego gracza
                            isActive={player.name === activePlayer}
                        />
                    </div>
                ))}
            </div>
        </main>
    )
}

export default App