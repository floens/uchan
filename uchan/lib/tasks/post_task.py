from uchan import celery
from uchan.lib.service import posts_service


class PostDetails:
    def __init__(self, form, board_name, thread_refno, text, name, subject, password, has_file, ip4):
        self.form = form
        self.board_name = board_name
        self.thread_refno = thread_refno
        self.text = text
        self.name = name
        self.subject = subject
        self.password = password
        self.has_file = has_file
        self.ip4 = ip4
        self.mod_id = None
        self.verification_data = None

        self.uploaded_file = None

        self.check_time = 0
        self.file_time = 0


@celery.task
def post_check_task(post_details):
    return posts_service.handle_post_check(post_details)


@celery.task
def post_task(post_details):
    return posts_service.handle_post(post_details)


class ManagePostDetails:
    DELETE = 1
    REPORT = 2
    TOGGLE_STICKY = 3
    TOGGLE_LOCKED = 4

    def __init__(self, board_name, thread_refno, post_id, ip4):
        self.board_name = board_name
        self.thread_refno = thread_refno
        self.post_id = post_id
        self.ip4 = ip4
        self.mod_id = None
        self.mode = None
        self.password = None
        self.report_verification_data = None


@celery.task
def manage_post_task(manage_post_details):
    posts_service.handle_manage_post(manage_post_details)
