from unichan import celery, g


class PostDetails:
    def __init__(self, board_name, thread_id, text, name, subject, password):
        self.board_name = board_name
        self.thread_id = thread_id
        self.text = text
        self.name = name
        self.subject = subject
        self.password = password


@celery.task
def post_task(post_details):
    return g.posts_service.handle_post(post_details)


class ManagePostDetails:
    DELETE = 1
    REPORT = 2

    def __init__(self, post_id):
        self.post_id = post_id
        self.mod_id = None
        self.mode = None
        self.password = None


@celery.task
def manage_post_task(manage_post_details):
    g.posts_service.handle_manage_post(manage_post_details)
