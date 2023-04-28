from typing import List

from uchan import celery, config
from uchan.lib.model import PostResultModel
from uchan.lib.service import posts_service
from uchan.lib.service.file_service import UploadedFile


class PostDetails:
    def __init__(self, form, board_name, thread_refno, text, name, subject, password, has_files, ip4, mod_id,
                 verification_data):
        self.form = form
        self.board_name = board_name
        self.thread_refno = thread_refno
        self.text = text
        self.name = name
        self.subject = subject
        self.password = password
        self.has_files = has_files
        self.ip4 = ip4
        self.mod_id = mod_id
        self.verification_data = verification_data

        self.uploaded_files: List[UploadedFile] = None

        self.file_time = 0


@celery.task
def post_task(post_details):
    return posts_service.create_post(post_details)


def execute_post_task(post_details: PostDetails) -> PostResultModel:
    if config.bypass_worker:
        return posts_service.create_post(post_details)
    else:
        return post_task.delay(post_details).get()


class ManagePostDetails:
    DELETE = 1
    REPORT = 2
    TOGGLE_STICKY = 3
    TOGGLE_LOCKED = 4

    def __init__(self, board_name, thread_refno, post_id, ip4, mod_id, mode, password):
        self.board_name = board_name
        self.thread_refno = thread_refno
        self.post_id = post_id
        self.ip4 = ip4
        self.mod_id = mod_id
        self.mode = mode
        self.password = password


@celery.task
def manage_post_task(manage_post_details):
    posts_service.handle_manage_post(manage_post_details)


def execute_manage_post_task(manage_post_details: ManagePostDetails):
    if config.bypass_worker:
        return posts_service.handle_manage_post(manage_post_details)
    else:
        return manage_post_task.delay(manage_post_details).get()
