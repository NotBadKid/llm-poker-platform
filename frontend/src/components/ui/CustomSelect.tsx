import { useState, useRef, useEffect } from "react";

interface CustomSelectProps<T extends number | string> {
    value: T,
    onChange: (value: T) => void,
    options: { value: T; label: string }[],
    className?: string,
}

const CustomSelect = <T extends number | string>({ value, onChange, options, className }: CustomSelectProps<T>) => {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const selectedLabel = options.find((opt) => opt.value === value)?.label;

    return (
        <div className="flex flex-col relative" ref={dropdownRef}>

            <div
                onClick={() => setIsOpen(!isOpen)}
                className={`
                    w-full p-3 rounded-lg cursor-pointer flex justify-between items-center transition-all duration-200
                    bg-slate-900 border ${className}
                    ${isOpen ? 'border-purple-500 ring-1 ring-purple-500' : 'border-slate-600 hover:border-purple-400'}
                `}
            >
                <span>{selectedLabel}</span>
                <svg
                    className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
                    fill="none" stroke="currentColor" viewBox="0 0 24 24"
                >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                </svg>
            </div>

            {isOpen && (
                <div className="absolute top-full left-0 w-full mt-2 bg-slate-900 border border-purple-500 rounded-lg shadow-xl z-50 overflow-hidden">
                    {options.map((option) => (
                        <div
                            key={option.value}
                            onClick={() => {
                                onChange(option.value);
                                setIsOpen(false);
                            }}
                            className={`
                                p-3 cursor-pointer transition-colors duration-150
                                ${option.value === value ? 'bg-purple-900/50 text-purple-200' : 'text-gray-300'}
                                hover:bg-purple-700 hover:text-white
                            `}
                        >
                            {option.label}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default CustomSelect;