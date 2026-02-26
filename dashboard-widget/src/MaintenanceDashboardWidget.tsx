import "./styles.css";
import {useState, useEffect, useCallback, useMemo} from "react";
import RemoteComponentWrapper from "customer_site/RemoteComponentWrapper";
import {useAgentChannel, useAgentSendUiCmd, useAgent} from "customer_site/hooks";
import {useRemoteParams} from "customer_site/useRemoteParams";

import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import localizedFormat from "dayjs/plugin/localizedFormat";

dayjs.extend(relativeTime);
dayjs.extend(localizedFormat);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function cn(...classes: (string | false | undefined | null)[]) {
  return classes.filter(Boolean).join(" ");
}

/** Read a tag value from the tag_values aggregate using the app key. */
function getTag(aggregate: any, appKey: string, tagName: string): any {
  return aggregate?.[appKey]?.[tagName] ?? null;
}

/** Extract the device list from deployment_config using the app key. */
function extractDeviceMap(config: any, appKey: string, selfId: string | undefined): Device[] {
  const app = config?.applications?.[appKey];
  const deviceMap = app?.DEVICE_MAP;
  console.log(deviceMap, app, config);
  if (!deviceMap || typeof deviceMap !== "object") return [];

  return Object.entries(deviceMap)
    .filter(([id]) => id !== selfId)
    .map(([id, name]) => ({id, name: name as string}));
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Device {
  id: string;
  name: string;
}

interface DeviceTagData {
  aggregate: any;
  isLoading: boolean;
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
// DeviceTagsFetcher – invisible component that subscribes to a device's tags
// channel and reports data back to the parent via callback.
// ---------------------------------------------------------------------------

function DeviceTagsFetcher({
                             deviceId,
                             onData,
                           }: {
  deviceId: string;
  onData: (id: string, data: DeviceTagData) => void;
}) {
  const {aggregate, isLoading} = useAgentChannel(deviceId, "tag_values");

  useEffect(() => {
    onData(deviceId, {aggregate, isLoading});
  }, [aggregate, isLoading, deviceId, onData]);

  return null;
}

// ---------------------------------------------------------------------------
// DeviceRow – visible table row with its own useAgentSendUiCmd hook.
// ---------------------------------------------------------------------------

function DeviceRow({
                     device,
                     app_key,
                     nextServiceEst,
                     hoursTillService,
                     kmsTillService,
                     lastServiceDate,
                     isLoading,
                   }: {
  device: Device;
  app_key: string;
  nextServiceEst: number | null;
  hoursTillService: number | null;
  kmsTillService: number | null;
  lastServiceDate: number | null;
  isLoading: boolean;
}) {
  const {mutate, isPending} = useAgentSendUiCmd(device.id) as any;
  const [expanded, setExpanded] = useState(false);

  const hoursDisplay = hoursTillService != null ? Math.round(hoursTillService) : null;
  const kmsDisplay = kmsTillService != null ? Math.round(kmsTillService) : null;

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
            {device.name}
          </a>
        </td>

        {/* Next service due – timestamp with tooltip */}
        <td className="p-2 align-middle whitespace-nowrap text-center">
          {isLoading ? (
            <span className="text-muted-foreground">Loading...</span>
          ) : nextServiceEst != null ? (
            <Timestamp value={nextServiceEst}/>
          ) : (
            <span className="text-muted-foreground">-</span>
          )}
        </td>

        {/* Hours till service – desktop only */}
        <td className="hidden md:table-cell p-2 align-middle whitespace-nowrap text-center">
          {isLoading ? (
            <span className="text-muted-foreground">Loading...</span>
          ) : hoursDisplay != null ? (
            <span>{hoursDisplay}</span>
          ) : (
            <span className="text-muted-foreground">-</span>
          )}
        </td>

        {/* Kms till service – desktop only */}
        <td className="hidden md:table-cell p-2 align-middle whitespace-nowrap text-center">
          {isLoading ? (
            <span className="text-muted-foreground">Loading...</span>
          ) : kmsDisplay != null ? (
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
              mutate({[`${app_key}_reset_service`]: true});
            }}
            disabled={isPending}
            className="inline-flex items-center justify-center whitespace-nowrap rounded-md border border-border text-xs/relaxed font-medium h-6 px-2 hover:bg-muted/50 hover:text-foreground transition-all disabled:pointer-events-none disabled:opacity-50 select-none"
          >
            {isPending ? "..." : "Service"}
          </button>
        </td>
      </tr>

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
                  {lastServiceDate != null ? <Timestamp value={lastServiceDate}/> : "-"}
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
  const devices: Device[] = useMemo(
    () => extractDeviceMap(deploymentConfig, uiElement.app_key, agentId),
    [deploymentConfig, uiElement.app_key, agentId],
  );

  // 2. Collect tag data from each DeviceTagsFetcher
  const [tagData, setTagData] = useState<Record<string, DeviceTagData>>({});

  const handleDeviceData = useCallback(
    (deviceId: string, data: DeviceTagData) => {
      setTagData((prev) => {
        const existing = prev[deviceId];
        if (
          existing?.aggregate === data.aggregate &&
          existing?.isLoading === data.isLoading
        ) {
          return prev; // no change – avoid unnecessary re-render
        }
        return {...prev, [deviceId]: data};
      });
    },
    [],
  );

  // 3. Sort by next service date – soonest first, nulls last
  const sorted = useMemo(() => {
    return [...devices].sort((a, b) => {
      const aEst = getTag(tagData[a.id]?.aggregate, appKey, "next_service_est");
      const bEst = getTag(tagData[b.id]?.aggregate, appKey, "next_service_est");
      if (aEst == null && bEst == null) return 0;
      if (aEst == null) return 1;
      if (bEst == null) return -1;
      return aEst - bEst;
    });
  }, [devices, tagData, appKey]);

  // Keep relative timestamps fresh
  const [, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 60_000);
    return () => clearInterval(id);
  }, []);

  // --- Render ---

  if (configLoading) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        Loading devices...
      </div>
    );
  }

  return (
    <>
      {/* Hidden data fetchers – one per device */}
      {devices.map((d) => (
        <DeviceTagsFetcher
          key={d.id}
          deviceId={d.id}
          onData={handleDeviceData}
        />
      ))}

      <div className="relative w-full overflow-x-auto">
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
          {sorted.length === 0 ? (
            <tr>
              <td
                colSpan={5}
                className="p-4 text-center text-muted-foreground"
              >
                No devices configured
              </td>
            </tr>
          ) : (
            sorted.map((device) => {
              const agg = tagData[device.id]?.aggregate;
              return (
                <DeviceRow
                  key={device.id}
                  device={device}
                  app_key={appKey}
                  nextServiceEst={getTag(agg, appKey, "next_service_est")}
                  hoursTillService={getTag(agg, appKey, "hours_till_next_service")}
                  kmsTillService={getTag(agg, appKey, "kms_till_next_service")}
                  lastServiceDate={getTag(agg, appKey, "last_service_date")}
                  isLoading={tagData[device.id]?.isLoading ?? true}
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
  console.log("props, prop", props);
  return (
    <RemoteComponentWrapper>
      <MaintenanceDashboardWidgetInner {...props} />
    </RemoteComponentWrapper>
  );
};

export default MaintenanceDashboardWidget;
