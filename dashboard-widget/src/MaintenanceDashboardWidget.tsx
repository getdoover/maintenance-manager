import "./styles.css";
import {useState, useEffect, useMemo} from "react";
import RemoteComponentWrapper from "customer_site/RemoteComponentWrapper";
import {useAgentChannel, useAgentSendUiCmd, useMultiAgentAggregates} from "customer_site/hooks";
import {useRemoteParams} from "customer_site/useRemoteParams";

import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import localizedFormat from "dayjs/plugin/localizedFormat";

import {DateTimePicker} from "./DateTimePicker";

dayjs.extend(relativeTime);
dayjs.extend(localizedFormat);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function cn(...classes: (string | false | undefined | null)[]) {
  return classes.filter(Boolean).join(" ");
}

/** Extract the device list from deployment_config using the app key. */
function extractDeviceMap(config: any, appKey: string, selfId: string | undefined): Omit<Device, "tags">[] {
  const app = config?.applications?.[appKey];
  const deviceMap = app?.DEVICE_MAP as Record<string, { name: string; display_name: string }>;
  if (!deviceMap || typeof deviceMap !== "object") return [];

  return Object.entries(deviceMap)
    .filter(([id, _]) => id !== selfId)
    .map(([id, vals]) => ({id, name: vals.name, display_name: vals.display_name}));
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface DeviceTags {
  next_service_est: number | null;
  hours_till_next_service: number | null;
  kms_till_next_service: number | null;
  last_service_date: number | null;
  engine_hours: number | null;
  machine_odometer: number | null;
}

interface Device {
  id: string;
  name: string;
  display_name: string;
  tags: DeviceTags;
}

// ---------------------------------------------------------------------------
// Timestamp (relative text + absolute tooltip on hover)
// ---------------------------------------------------------------------------

function Timestamp({value}: { value: number }) {
  const date = dayjs(value);
  const relative = date.fromNow();
  const absolute = date.format("LLLL");
  const isPast = date.isBefore(dayjs());

  return (
    <span className="group/ts relative inline-block">
      <span
        className={cn(
          "cursor-default",
          isPast ? "text-destructive font-medium" : "text-foreground",
        )}
      >
        {relative}
      </span>
      <span
        className="invisible group-hover/ts:visible absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 text-xs rounded-md bg-foreground text-background whitespace-nowrap z-50 pointer-events-none">
        {absolute}
      </span>
    </span>
  );
}

// ---------------------------------------------------------------------------
// ServiceForm – inline form for recording a service with specific readings
// ---------------------------------------------------------------------------

function ServiceForm({
  mutate,
  isPending,
  app_key,
  deviceName,
  engineHours,
  machineOdometer,
  onClose,
}: {
  mutate: (payload: any) => void;
  isPending: boolean;
  app_key: string;
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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div
        className="relative z-[51] w-full max-w-md rounded-lg border border-border bg-background p-6 shadow-lg"
      >
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
    </div>
  );
}

// ---------------------------------------------------------------------------
// DeviceRow – visible table row with its own useAgentSendUiCmd hook.
// ---------------------------------------------------------------------------

function DeviceRow({
                     device,
                     app_key,
                   }: {
  device: Device;
  app_key: string;
}) {
  const {mutate, isPending} = useAgentSendUiCmd(device.id) as any;
  const [expanded, setExpanded] = useState(false);
  const [showServiceForm, setShowServiceForm] = useState(false);

  const tags = device.tags;
  const hoursDisplay = tags.hours_till_next_service != null ? Math.round(tags.hours_till_next_service) : null;
  const kmsDisplay = tags.kms_till_next_service != null ? Math.round(tags.kms_till_next_service) : null;

  return (
    <>
      <tr
        className="hover:bg-muted/50 border-b transition-colors cursor-pointer"
        onClick={() => setExpanded((e) => !e)}
      >
        {/* Device name – clickable link */}
        <td className="p-2 align-middle whitespace-nowrap text-center">
          <a
            href={`/agent/${device.id}`}
            className="text-primary hover:underline underline-offset-4 font-medium"
            onClick={(e) => e.stopPropagation()}
          >
            {device.display_name}
          </a>
        </td>

        {/* Next service due – timestamp with tooltip */}
        <td className="p-2 align-middle whitespace-nowrap text-center">
          {tags.next_service_est != null ? (
            <Timestamp value={tags.next_service_est}/>
          ) : (
            <span className="text-muted-foreground">-</span>
          )}
        </td>

        {/* Hours till service – desktop only */}
        <td className="hidden md:table-cell p-2 align-middle whitespace-nowrap text-center">
          {hoursDisplay != null ? (
            <span>{hoursDisplay}</span>
          ) : (
            <span className="text-muted-foreground">-</span>
          )}
        </td>

        {/* Kms till service – desktop only */}
        <td className="hidden md:table-cell p-2 align-middle whitespace-nowrap text-center">
          {kmsDisplay != null ? (
            <span>{kmsDisplay}</span>
          ) : (
            <span className="text-muted-foreground">-</span>
          )}
        </td>

        {/* Service button */}
        <td className="p-2 align-middle whitespace-nowrap text-center">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowServiceForm((v) => !v);
            }}
            disabled={isPending}
            className="inline-flex items-center justify-center whitespace-nowrap rounded-md border border-border text-xs/relaxed font-medium h-6 px-2 hover:bg-muted/50 hover:text-foreground transition-all disabled:pointer-events-none disabled:opacity-50 select-none"
          >
            {isPending ? "..." : "Service"}
          </button>
        </td>
      </tr>

      {/* Service dialog */}
      {showServiceForm && (
        <ServiceForm
          mutate={mutate}
          isPending={isPending}
          app_key={app_key}
          deviceName={device.display_name}
          engineHours={tags.engine_hours}
          machineOdometer={tags.machine_odometer}
          onClose={() => setShowServiceForm(false)}
        />
      )}

      {/* Expanded detail row */}
      {expanded && (
        <tr className="border-b bg-muted/30">
          <td colSpan={5} className="px-4 py-2 text-xs">
            <div className="flex flex-wrap gap-x-6 gap-y-1">
              <div>
                <span className="text-muted-foreground">Hours till service: </span>
                <span className="font-medium">{hoursDisplay ?? "-"}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Kms till service: </span>
                <span className="font-medium">{kmsDisplay ?? "-"}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Last service: </span>
                <span className="font-medium">
                  {tags.last_service_date != null ? <Timestamp value={tags.last_service_date}/> : "-"}
                </span>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Inner widget (has access to hooks via RemoteComponentWrapper)
// ---------------------------------------------------------------------------
export interface UiRemoteComponentMaintenance {
  app_key: string;
  manager_app_key: string;
}

function MaintenanceDashboardWidgetInner({uiElement}: { uiElement: UiRemoteComponentMaintenance }) {
  const {agentId} = useRemoteParams();
  const appKey = uiElement.manager_app_key;

  // 1. Read the deployment config to get the DEVICE_MAP
  const {aggregate: deploymentConfig, isLoading: configLoading} =
    useAgentChannel(agentId, "deployment_config");

  // Parse device map – exclude the dashboard agent itself
  const devices: Omit<Device, "tags">[] = useMemo(
    () => extractDeviceMap(deploymentConfig, uiElement.app_key, agentId),
    [deploymentConfig, uiElement.app_key, agentId],
  );
  const deviceIds = devices.map(d => d.id);

  const {aggregates, isLoading: aggregatesLoading} = useMultiAgentAggregates(deviceIds, "tag_values");

  const deviceData = useMemo(() => {
    const deviceMap = new Array<Device>();

    for (const device of devices) {
      const tagValues = aggregates[device.id]?.data?.[appKey]
      const tags = {
        next_service_est: tagValues?.next_service_est,
        hours_till_next_service: tagValues?.hours_till_next_service,
        kms_till_next_service: tagValues?.kms_till_next_service,
        last_service_date: tagValues?.last_service_date,
        engine_hours: tagValues?.engine_hours ?? null,
        machine_odometer: tagValues?.machine_odometer ?? null,
      } as DeviceTags;
      const newDevice = {...device, tags};
      deviceMap.push(newDevice);
    }
    return deviceMap.sort((a, b) => a.tags.next_service_est - b.tags.next_service_est)
  }, [devices, aggregates])

  // Keep relative timestamps fresh
  const [, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 60_000);
    return () => clearInterval(id);
  }, []);

  // --- Render ---

  if (configLoading || aggregatesLoading) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        Loading devices...
      </div>
    );
  }

  return (
    <>
      <div className="relative">
        <table className="w-full caption-bottom text-xs">
          <thead className="[&_tr]:border-b">
          <tr className="border-b transition-colors">
            <th className="text-foreground h-10 px-2 text-center align-middle font-medium whitespace-nowrap">
              Device
            </th>
            <th className="text-foreground h-10 px-2 text-center align-middle font-medium whitespace-nowrap">
              Next Service Due
            </th>
            <th
              className="hidden md:table-cell text-foreground h-10 px-2 text-center align-middle font-medium whitespace-nowrap">
              Hours Till Service
            </th>
            <th
              className="hidden md:table-cell text-foreground h-10 px-2 text-center align-middle font-medium whitespace-nowrap">
              Kms Till Service
            </th>
            <th className="text-foreground h-10 px-2 text-center align-middle font-medium whitespace-nowrap">
              Action
            </th>
          </tr>
          </thead>

          <tbody className="[&_tr:last-child]:border-0">
          {deviceData.length === 0 ? (
            <tr>
              <td
                colSpan={5}
                className="p-4 text-center text-muted-foreground"
              >
                No devices configured
              </td>
            </tr>
          ) : (
            deviceData.map((device) => {
              return (
                <DeviceRow
                  key={device.id}
                  device={device}
                  app_key={appKey}
                />
              );
            })
          )}
          </tbody>
        </table>
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// Wrapper – provides the RemoteComponentWrapper context required for hooks
// ---------------------------------------------------------------------------

const MaintenanceDashboardWidget = (props: any) => {
  return (
    <RemoteComponentWrapper>
      <MaintenanceDashboardWidgetInner {...props} />
    </RemoteComponentWrapper>
  );
};

export default MaintenanceDashboardWidget;
