from uchan import celery, g


class ManageReportDetails:
    CLEAR = 1
    DELETE_POST = 2
    DELETE_FILE = 3

    def __init__(self, report_id, mod_id):
        self.report_id = report_id
        self.mod_id = mod_id
        self.mode = None


@celery.task
def manage_report_task(manage_report_details):
    g.report_service.handle_manage_report(manage_report_details)
