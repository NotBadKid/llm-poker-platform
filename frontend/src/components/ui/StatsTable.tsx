import type {PlayerStats} from "../../types/game.ts";

interface StatsTableProps {
    players: PlayerStats[];
}

const StatsTable = ({ players }: StatsTableProps)=>  {
    return (
        <div className="overflow-x-auto" id='stats-table'>
            <table className="w-full">
                <thead>
                <tr className="border-b border-slate-700">
                    <th/>
                    <th className="text-left">Name</th>
                    <th>Hands Played</th>
                    <th>Hands Won</th>
                    <th>Win Rate</th>
                    <th>Total Profit</th>
                    <th>Avg Profit/Hand</th>
                </tr>
                </thead>
                <tbody>
                {players.map((player, idx) => (
                    <tr
                        key={player.name}
                        className="border-b border-slate-700 hover:bg-[#0f1f35] transition-colors"
                    >
                        <td className='text-slate-500'>
                            {idx + 1}
                        </td>
                        <td className="text-left">{player.name}</td>
                        <td className="">
                            {player.hands_played}
                        </td>
                        <td>
                            {player.hands_won}
                        </td>
                        <td>
                            {player.win_rate.toFixed(2)}%
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