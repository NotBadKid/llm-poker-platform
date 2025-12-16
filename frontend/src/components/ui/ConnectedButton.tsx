interface Props {
    options: string[],
    className?: string,
    currentValue: string
    onChange: (val: string) => void
}

const ConnectedButton = ({options, className, currentValue, onChange}: Props) => {
    return (
        <div className={`flex w-fit border rounded-xl border-slate-600 text-slate-400 bg-slate-900 cursor-pointer ${className}`}>
            {
                options.map((option) => (
                    <div
                        key={option}
                        className={`px-8 py-2 rounded-xl whitespace-nowrap ${currentValue == option ? 'text-white bg-purple-600' : 'bg-slate-900'} `}
                        onClick={() => onChange(option)}
                    >
                        {option}
                    </div>
                ))
            }
        </div>
    );
};

export default ConnectedButton;
