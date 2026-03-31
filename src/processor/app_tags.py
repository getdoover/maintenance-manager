from pydoover.tags import Tag, Tags


class MaintenanceManagerTags(Tags):
    next_service_est = Tag("number", default=None)
    days_till_next_service = Tag("number", default=None)
    engine_hours = Tag("number", default=0)
    hours_till_next_service = Tag("number", default=None)
    machine_odometer = Tag("number", default=None)
    kms_till_next_service = Tag("number", default=None)

    last_service_hours = Tag("number", default=None)
    last_service_odometer = Tag("number", default=None)
    last_service_date = Tag("number", default=None)

    service_notification_sent = Tag("boolean", default=False)

    hours_offset = Tag("number", default=0)
    odo_offset = Tag("number", default=0)

    ave_hours_per_day = Tag("number", default=0)
    ave_kms_per_day = Tag("number", default=0)
