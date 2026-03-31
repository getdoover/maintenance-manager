from pydoover.tags import Tag, Tags


class MaintenanceManagerTags(Tags):
    next_service_est = Tag("number")
    days_till_next_service = Tag("number")
    engine_hours = Tag("number")
    hours_till_next_service = Tag("number")
    machine_odometer = Tag("number")
    kms_till_next_service = Tag("number")

    last_service_hours = Tag("number")
    last_service_odometer = Tag("number")
    last_service_date = Tag("number")

    service_notification_sent = Tag("boolean", default=False)

    hours_offset = Tag("number", default=0)
    odo_offset = Tag("number", default=0)

    ave_hours_per_day = Tag("number")
    ave_kms_per_day = Tag("number")
