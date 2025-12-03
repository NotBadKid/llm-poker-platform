interface Props {
    label: string,
    value: number,
    onChange: (newValue: number) => void,
    min: number,
    max: number,
}

const GameInput = ({ label, value, onChange, min, max }: Props) => {
    return (
        <div className="flex flex-col">
            <label className="text-gray-400 mb-2">{label}</label>
            <input
                type="number"
                value={value}
                min={min}
                max={max}
                onChange={(e) => onChange(Number(e.target.value))}
                className="bg-slate-900 border border-slate-600 rounded-lg p-3 outline-none no-spinner hover:border-purple-400 transition-all duration-200 focus:ring-1 ring-purple-500"
            />
        </div>
    );
};

export default GameInput;