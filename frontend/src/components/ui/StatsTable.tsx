import type {PlayerStats} from "../../types/game.ts";
import SortHeader from "./SortHeader.tsx";
import {STATS_HEADERS} from "../../const";

interface StatsTableProps {
    players: PlayerStats[];
    currentSortParam: string;
    isAscending: boolean;
    onSort: (key: string) => void;
}

interface Header {
    header: string,
    sortKey: string,
}

const StatsTable = ({players, currentSortParam, isAscending, onSort}: StatsTableProps) => {

    return (
        <div className="overflow-x-auto" id='stats-table'>
            <table className="w-full border-collapse">
                <thead>
                <tr className="border-b border-slate-700">
                    <th className="p-4"/>
                    <th className="text-left p-4">Name</th>
                    {STATS_HEADERS.map((thead: Header) => (
                        <SortHeader
                            key={thead.header}
                            header={thead.header}
                            sortKey={thead.sortKey}
                            activeSortKey={currentSortParam}
                            isAscending={isAscending}
                            onClick={onSort}
                        />
                    ))}
                </tr>
                </thead>
                <tbody>
                {players.map((player, idx) => (
                    <tr
                        key={player.model_id}
                        className="border-b border-slate-700 hover:bg-[#0f1f35] transition-colors"
                    >
                        <td className='text-slate-500'>
                            {idx + 1}
                        </td>
                        <td className="text-left">{player.model_id}</td>
                        <td>
                            {player.parameters ? `${player.parameters / 1000000000}B` : "Unknown"}
                        </td>
                        <td className="text-center p-4">
                            {player.hands_played}
                        </td>
                        <td>
                            {player.hands_won}
                        </td>
                        <td>
                            {(player.win_rate * 100).toFixed(2)}%
                        </td>
                        <td
                            className={`${
                                player.total_profit >= 0 ? "text-[#6EE7B7]" : "text-[#F87171]"
                            }`}
                        >
                            {player.total_profit >= 0 ? "+" : ""}
                            {player.total_profit}
                        </td>
                        <td
                            className={`${
                                player.avg_profit_per_hand >= 0 ? "text-[#6EE7B7]" : "text-[#F87171]"
                            }`}
                        >
                            {player.avg_profit_per_hand >= 0 ? "+" : ""}
                            {player.avg_profit_per_hand.toFixed(2)}
                        </td>
                    </tr>
                ))}
                </tbody>
            </table>
        </div>
    );
}

export default StatsTable;