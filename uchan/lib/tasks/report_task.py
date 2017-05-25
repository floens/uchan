from uchan import celery


class ManageReportDetails:
    CLEAR = 1
    DELETE_POST = 2
    DELETE_FILE = 3

    def __init__(self, report_id, mod_id):
        self.report_id = report_id
        self.mod_id = mod_id
        self.mode = None


from uchan.lib.service import report_service


@celery.task
def manage_report_task(manage_report_details):
    report_service.handle_manage_report(manage_report_details)
