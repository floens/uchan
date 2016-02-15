from unichan import celery, g


class PostDetails:
    def __init__(self, board_name, thread_id, text, name, subject, password, has_file, ip4):
        self.board_name = board_name
        self.thread_id = thread_id
        self.text = text
        self.name = name
        self.subject = subject
        self.password = password
        self.has_file = has_file
        self.ip4 = ip4

        self.uploaded_file = None


@celery.task
def post_check_task(post_details):
    return g.posts_service.handle_post_check(post_details)


@celery.task
def post_task(post_details):
    return g.posts_service.handle_post(post_details)


class ManagePostDetails:
    DELETE = 1
    REPORT = 2

    def __init__(self, post_id, ip4):
        self.post_id = post_id
        self.mod_id = None
        self.mode = None
        self.password = None
        self.ip4 = ip4


@celery.task
def manage_post_task(manage_post_details):
    g.posts_service.handle_manage_post(manage_post_details)
