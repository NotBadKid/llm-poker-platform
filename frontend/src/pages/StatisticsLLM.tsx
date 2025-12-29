import StatsTable from "../components/ui/StatsTable.tsx";
import {useEffect, useState} from "react";
import type {PlayerStats} from "../types/game.ts";

const StatisticsLLM = () => {
    const [playerStats, setPlayerStats] = useState<PlayerStats[]>([])
    const [isLoading, setIsLoading] = useState<boolean>(true)
    const [sortParam, setSortParam] = useState<string>("hands_played");
    const [isAscending, setIsAscending] = useState<boolean>(false);

    const API_URL = 'http://localhost:5000';

    const handleSort = (key: string) => {
        if (sortParam === key) {
            setIsAscending(prev => !prev);
        } else {
            setSortParam(key);
            setIsAscending(false);
        }
    };

    useEffect(() => {
        const fetchStats = async () => {
            setIsLoading(true);
            try {
                const ascValue = isAscending ? 1 : 0;
                const query = `param=${sortParam}&ascending=${ascValue}`;
                const response = await fetch(`${API_URL}/stats?${query}`, {
                    headers: {'Content-Type': 'application/json'},
                })

                if (!response.ok) {
                    throw new Error(`Problem: ${response.status}`);
                }

                const data = await response.json();
                setPlayerStats(data);
            } catch (error) {
                console.error(error);
            } finally {
                setIsLoading(false)
            }
        }

        fetchStats();
    }, [sortParam, isAscending])

    return (
        <div className="min-h-screen p-8 flex flex-col items-center overflow-y-auto">
            <h1 className="text-4xl font-bold absolute top-6 bg-gradient-to-r py-1 from-violet-600 via-teal-500 to-blue-500 text-transparent bg-clip-text">Statistics</h1>

            <div className="w-[80%] mt-18">
                <div className="mb-8 bg-slate-800 border border-slate-700 rounded-2xl p-6">
                    <h2 className="text-2xl font-semibold text-purple-500">Scenario</h2>
                    <div className="flex items-center justify-center flex-wrap gap-x-8 gap-y-3">
                        <div className="flex items-center gap-2">
                            <span className="text-slate-400 text-sm">SB/BB</span>
                            <span className="bg-slate-900 px-3 py-1 rounded-lg">100/200</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-slate-400 text-sm">Starting Chips</span>
                            <span className="bg-slate-900 px-3 py-1 rounded-lg">10,000</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-slate-400 text-sm">Players</span>
                            <span className="bg-slate-900 px-3 py-1 rounded-lg">4</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-[#A855F7] bg-[#A855F7]/10 border border-[#A855F7]/30 px-3 py-1 rounded-lg text-sm">Default Prompts</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-[#A855F7] bg-[#A855F7]/10 border border-[#A855F7]/30 px-3 py-1 rounded-lg text-sm">Default Temperature</span>
                        </div>
                    </div>
                </div>

                <div className="bg-slate-800 rounded-2xl p-8 border border-slate-700">
                    <h2 className="text-2xl font-semibold text-purple-500 mb-6 ">Statistics</h2>
                    {
                        isLoading ? <div className="flex justify-center items-center h-40">
                            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500 text-purple-600 text-xl text-center">POKER</div>
                        </div> : <StatsTable
                            players={playerStats}
                            currentSortParam={sortParam}
                            isAscending={isAscending}
                            onSort={handleSort}
                        />
                    }
                </div>
            </div>
        </div>
    );
}

export default StatisticsLLM;