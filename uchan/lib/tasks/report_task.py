from uchan import celery, config


class ManageReportDetails:
    CLEAR = 1
    DELETE_POST = 2
    DELETE_FILE = 3

    def __init__(self, report_id: int, mod_id: int, mode: int):
        self.report_id = report_id
        self.mod_id = mod_id
        self.mode = mode


from uchan.lib.service import report_service  # noqa


@celery.task
def manage_report_task(manage_report_details):
    report_service.handle_manage_report(manage_report_details)


def execute_manage_report_task(manage_report_details: ManageReportDetails):
    if config.bypass_worker:
        return report_service.handle_manage_report(manage_report_details)
    else:
        return manage_report_task.delay(manage_report_details).get()
