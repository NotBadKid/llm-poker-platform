interface Props {
    header: string;
    sortKey: string;
    activeSortKey: string;
    isAscending: boolean;
    onClick: (key: string) => void;
}

const SortHeader = ({ header, sortKey, activeSortKey, isAscending, onClick }: Props) => {
    const isActive = sortKey === activeSortKey;
    const showUpArrow = isActive && isAscending;

    return (
        <th className="p-2 cursor-pointer select-none" onClick={() => onClick(sortKey)}>
            <div
                className={`flex items-center justify-center gap-2 px-3 py-2 rounded transition-all duration-200 
                ${isActive ? "border border-slate-400 bg-slate-700/50" : "border border-transparent hover:bg-slate-800"}`}
            >
                <span className="font-semibold text-slate-200">{header}</span>

                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className={`text-slate-400 transition-transform duration-200 ${showUpArrow ? "rotate-180" : ""}`}
                >
                    <path d="M6 9l6 6 6-6"/>
                </svg>
            </div>
        </th>
    );
};

export default SortHeader;