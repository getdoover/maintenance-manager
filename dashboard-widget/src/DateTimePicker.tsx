"use client";
import * as React from "react";
import { Calendar } from "./components/ui/calendar";
import { Input } from "./components/ui/input";
import { ChevronDownIcon } from "lucide-react";
import dayjs from "dayjs";
import localizedFormat from "dayjs/plugin/localizedFormat";

dayjs.extend(localizedFormat);

interface DateTimePickerProps {
  value: Date | undefined;
  onChange: (value: Date | undefined) => void;
  disabled?: boolean;
}

export function DateTimePicker({
  value,
  onChange: setDate,
  disabled,
}: DateTimePickerProps) {
  const [open, setOpen] = React.useState(false);
  const [date, setState] = React.useState(() =>
    value ? dayjs(value) : undefined,
  );
  const [time, setTime] = React.useState(() =>
    value ? dayjs(value).format("HH:mm") : undefined,
  );
  const containerRef = React.useRef<HTMLDivElement>(null);

  // Close on outside click
  React.useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const handleDateChange = (date: Date) => {
    setState(dayjs(date));
    if (time) {
      setDate(
        dayjs(date)
          .set("hour", Number(time.split(":")[0]))
          .set("minute", Number(time.split(":")[1]))
          .toDate(),
      );
    }
  };

  const handleTimeChange = (time: string) => {
    setTime(time);
    if (date) {
      setDate(
        dayjs(date)
          .set("hour", Number(time.split(":")[0]))
          .set("minute", Number(time.split(":")[1]))
          .toDate(),
      );
    }
  };

  return (
    <div className="flex gap-2 items-center flex-row">
      <div className="relative" ref={containerRef}>
        <button
          type="button"
          disabled={disabled}
          onClick={() => setOpen((v) => !v)}
          className="inline-flex items-center justify-between gap-1 h-7 rounded-md border border-border bg-input/20 px-2 text-xs font-normal transition-all hover:bg-input/50 hover:text-foreground focus-visible:border-ring focus-visible:ring-ring/30 focus-visible:ring-[2px] outline-none disabled:pointer-events-none disabled:opacity-50 select-none [&_svg]:size-3.5 [&_svg]:pointer-events-none [&_svg]:shrink-0"
        >
          {date ? date.format("LL") : "Select date"}
          <ChevronDownIcon className="text-muted-foreground" />
        </button>

        {open && (
          <div className="absolute top-full left-0 mt-1 z-[60] rounded-lg bg-popover text-popover-foreground shadow-md ring-1 ring-foreground/10 overflow-hidden">
            <Calendar
              mode="single"
              selected={date?.toDate()}
              captionLayout="dropdown"
              defaultMonth={date?.toDate()}
              disabled={disabled}
              onSelect={(date) => {
                if (date) {
                  handleDateChange(date);
                }
                setOpen(false);
              }}
            />
          </div>
        )}
      </div>

      <Input
        type="time"
        step={60 * 1000}
        className="appearance-none [&::-webkit-calendar-picker-indicator]:hidden [&::-webkit-calendar-picker-indicator]:appearance-none !text-xs !w-24"
        onBlur={(e) => handleTimeChange(e.target.value)}
        onChange={(e) => setTime(e.target.value)}
        value={time}
        disabled={disabled}
      />
    </div>
  );
}
