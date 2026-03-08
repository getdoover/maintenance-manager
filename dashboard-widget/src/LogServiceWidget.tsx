import "./styles.css";
import {useState} from "react";
import {createPortal} from "react-dom";
import RemoteComponentWrapper from "customer_site/RemoteComponentWrapper";
import {useAgentChannel, useAgentSendUiCmd} from "customer_site/hooks";
import {useRemoteParams} from "customer_site/useRemoteParams";

import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import localizedFormat from "dayjs/plugin/localizedFormat";

import {DateTimePicker} from "./DateTimePicker";

dayjs.extend(relativeTime);
dayjs.extend(localizedFormat);

// ---------------------------------------------------------------------------
// ServiceForm
// ---------------------------------------------------------------------------

function ServiceForm({
                       mutate,
                       isPending,
                       deviceName,
                       engineHours,
                       machineOdometer,
                       onClose,
                     }: {
  mutate: (payload: any) => void;
  isPending: boolean;
  deviceName: string;
  engineHours: number | null;
  machineOdometer: number | null;
  onClose: () => void;
}) {
  const [dateTimeValue, setDateTimeValue] = useState<Date | undefined>(() => new Date());
  const [hours, setHours] = useState(engineHours != null ? String(engineHours) : "");
  const [odometer, setOdometer] = useState(machineOdometer != null ? String(machineOdometer) : "");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = () => {
    if (!dateTimeValue) {
      setError("Date/time is required.");
      return;
    }
    const parsedHours = hours.trim() !== "" ? parseFloat(hours) : null;
    const parsedOdo = odometer.trim() !== "" ? parseFloat(odometer) : null;

    if (parsedHours != null && isNaN(parsedHours)) {
      setError("Hours must be a valid number.");
      return;
    }
    if (parsedOdo != null && isNaN(parsedOdo)) {
      setError("Odometer must be a valid number.");
      return;
    }

    setError(null);
    const dateMs = dayjs(dateTimeValue).valueOf();
    mutate({
      request: {
        name: "create_service",
        values: {
          dt: dateMs,
          hours: parsedHours,
          kms: parsedOdo,
        },
      },
    });
    onClose();
  };

  const inputClass =
    "h-7 w-full rounded-md border border-border bg-input/20 px-2 text-xs transition-colors focus-visible:border-ring focus-visible:ring-ring/30 focus-visible:ring-[2px] outline-none disabled:pointer-events-none disabled:opacity-50";

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50" onClick={onClose}/>
      <div className="relative z-[51] w-full max-w-md rounded-lg border border-border bg-background p-6 shadow-lg">
        <h3 className="text-sm font-semibold mb-1">{deviceName}</h3>
        <p className="text-xs text-muted-foreground mb-4">Record a service for this device.</p>
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground font-medium">Service Date/Time *</label>
            <DateTimePicker
              value={dateTimeValue}
              onChange={setDateTimeValue}
              disabled={isPending}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground font-medium">Hours</label>
            <input
              type="number"
              step="any"
              value={hours}
              onChange={(e) => setHours(e.target.value)}
              placeholder="Engine hours"
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground font-medium">Odometer (km)</label>
            <input
              type="number"
              step="any"
              value={odometer}
              onChange={(e) => setOdometer(e.target.value)}
              placeholder="Kms"
              className={inputClass}
            />
          </div>
          {error && <p className="text-xs text-destructive font-medium">{error}</p>}
          <div className="flex justify-end gap-2 mt-1">
            <button
              onClick={onClose}
              disabled={isPending}
              className="inline-flex items-center justify-center rounded-md border border-border text-xs font-medium h-8 px-4 hover:bg-muted/50 transition-colors disabled:pointer-events-none disabled:opacity-50 select-none"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={isPending}
              className="inline-flex items-center justify-center rounded-md bg-primary text-primary-foreground text-xs font-medium h-8 px-4 hover:bg-primary/90 transition-colors disabled:pointer-events-none disabled:opacity-50 select-none"
            >
              {isPending ? "..." : "Submit"}
            </button>
          </div>
        </div>
      </div>
    </div>,
    document.body,
  );
}

// ---------------------------------------------------------------------------
// Inner widget
// ---------------------------------------------------------------------------

export interface UiRemoteComponentLogService {
  app_key: string;
  device_name: string;
}

function LogServiceWidgetInner({uiElement, ui_element_props}: {
  uiElement: UiRemoteComponentLogService;
  ui_element_props?: any
}) {
  const {agentId} = useRemoteParams();
  const {mutate, isPending} = useAgentSendUiCmd(agentId) as any;
  const [showForm, setShowForm] = useState(false);

  const {app_key, device_name} = uiElement;

  // Read tag values to get current engine hours / odometer
  const {aggregate: tagValues} = useAgentChannel(agentId, "tag_values");

  const deviceName = device_name ?? ui_element_props?.ui?.display_name ?? "This Device";
  const engineHours = tagValues?.[app_key]?.engine_hours ?? null;
  const machineOdometer = tagValues?.[app_key]?.machine_odometer ?? null;

  return (
    <>
      <button
        onClick={() => setShowForm(true)}
        disabled={isPending}
        className="inline-flex w-full items-center justify-center whitespace-nowrap rounded-md border border-border text-sm font-medium h-9 px-4 hover:bg-muted/50 hover:text-foreground transition-all disabled:pointer-events-none disabled:opacity-50 select-none"
      >
        {isPending ? "..." : "Log Service"}
      </button>

      {showForm && (
        <ServiceForm
          mutate={mutate}
          isPending={isPending}
          deviceName={deviceName}
          engineHours={engineHours}
          machineOdometer={machineOdometer}
          onClose={() => setShowForm(false)}
        />
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Wrapper
// ---------------------------------------------------------------------------

const LogServiceWidget = (props: any) => {
  return (
    <RemoteComponentWrapper>
      <LogServiceWidgetInner {...props} />
    </RemoteComponentWrapper>
  );
};

export default LogServiceWidget;
