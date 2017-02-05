import os
import random
import shutil
import string

from PIL import Image
from sqlalchemy.event import listen

# Extensions that will be converted
CONVERT_EXTENSIONS = [('jpeg', 'jpg')]

# Extensions that are allowed
ALLOWED_EXTENSIONS = ['jpg', 'png', 'gif']

# Actual file types that are allowed, should correspond to allowed extensions
ALLOWED_FORMATS = ['JPEG', 'PNG', 'GIF']

GENERATED_FILE_NAME_LENGTH = 16
MAX_FILE_NAME_LENGTH = 50
MAX_IMAGE_WIDTH = 10000
MAX_IMAGE_HEIGHT = 10000
THUMBNAIL_POSTFIX = '_t'

from uchan import logger
from uchan.lib.exceptions import ArgumentError
from uchan.lib.models import File


class FileCdn:
    def upload(self, local_path, file_name):
        raise NotImplementedError()

    def delete(self, file_name):
        raise NotImplementedError()

    def resolve_to_uri(self, file_name):
        raise NotImplementedError()


class LocalCdn(FileCdn):
    """
    A local version of a cdn, just a folder on the same machine.
    Configure paths with config.py
    """

    def __init__(self, path, web_path):
        super().__init__()
        self.path = path
        self.web_path = web_path

    def upload(self, local_path, file_name):
        subdir, name = self._folderize(file_name, True)

        shutil.copyfile(local_path, os.path.join(self.path, subdir, name))

    def delete(self, file_name):
        subdir, name = self._folderize(file_name)

        os.remove(os.path.join(self.path, subdir, name))

    def resolve_to_uri(self, file_name):
        return self.web_path + file_name[:2] + '/' + file_name[2:]

    def _folderize(self, file_name, make_subdir=False):
        # Make the first two chars of the random name a folder, this is efficient for most file systems

        subdir = file_name[:2]

        if make_subdir:
            try:
                os.mkdir(os.path.join(self.path, subdir))
            except OSError:
                pass

        return subdir, file_name[2:]


class UploadedFile:
    def __init__(self, location, thumbnail_location, original_name, width, height, size, thumbnail_width,
                 thumbnail_height):
        self.location = location
        self.thumbnail_location = thumbnail_location
        self.original_name = original_name
        self.width = width
        self.height = height
        self.size = size
        self.thumbnail_width = thumbnail_width
        self.thumbnail_height = thumbnail_height


class UploadQueueFiles:
    def __init__(self, image_output, image_name, thumbnail_output, thumbnail_name):
        self.image_output = image_output
        self.image_name = image_name
        self.thumbnail_output = thumbnail_output
        self.thumbnail_name = thumbnail_name


cdn = None  # type: FileCdn
upload_queue_path = None


def init(_upload_queue_path, _cdn):
    global upload_queue_path, cdn
    upload_queue_path = _upload_queue_path
    cdn = _cdn

    # Register on the event when a post row is deleted to also remove it from the cdn
    listen(File, 'after_delete', _on_file_deleted)


def resolve_to_uri(name):
    return cdn.resolve_to_uri(name)


def prepare_upload(file, thumbnail_size):
    user_file_name = file.filename
    if not user_file_name:
        raise ArgumentError('Invalid file name')

    extension = _get_extension(user_file_name)
    if not extension:
        raise ArgumentError('Invalid file format')

    # truncate filename if too long
    user_file_name = user_file_name[:MAX_FILE_NAME_LENGTH]

    filename, extension = _get_filename(extension)

    image_name = filename + '.' + extension
    thumbnail_name = filename + THUMBNAIL_POSTFIX + '.jpg'

    image_output = os.path.join(upload_queue_path, image_name)
    thumbnail_output = os.path.join(upload_queue_path, thumbnail_name)

    # Save the file from the user to the upload queue dir
    file.save(image_output)

    # Get image params and generate thumbnail
    width, height, size, thumbnail_width, thumbnail_height = \
        process_and_generate_thumbnail(image_output, thumbnail_output, thumbnail_size)

    # Ready to be send to the worker to be inserted into the db
    uploaded_file = UploadedFile(image_name, thumbnail_name, user_file_name, width, height, size, thumbnail_width,
                                 thumbnail_height)
    upload_queue_files = UploadQueueFiles(image_output, image_name, thumbnail_output, thumbnail_name)
    return uploaded_file, upload_queue_files


def do_upload(uploaded_file: UploadQueueFiles):
    # Upload the image and the thumbnail to the cdn
    cdn.upload(uploaded_file.image_output, uploaded_file.image_name)
    cdn.upload(uploaded_file.thumbnail_output, uploaded_file.thumbnail_name)


def clean_up_queue(upload_queue_files):
    try:
        os.remove(upload_queue_files.image_output)
    except OSError:
        logger.exception('Error removing upload queue image')

    try:
        os.remove(upload_queue_files.thumbnail_output)
    except OSError:
        logger.exception('Error removing upload queue thumbnail')


def process_and_generate_thumbnail(local_path, thumbnail_path, thumbnail_size):
    try:
        file_size = os.stat(local_path).st_size
        image = Image.open(local_path)
        if image.format not in ALLOWED_FORMATS:
            raise ArgumentError('Invalid file format')

        width, height = image.size

        if width > MAX_IMAGE_WIDTH or height > MAX_IMAGE_HEIGHT:
            raise ArgumentError('Image size too big')

        image.thumbnail((thumbnail_size, thumbnail_size))
        thumbnail_width, thumbnail_height = image.size

        if image.mode != 'RGB':
            image = image.convert('RGB')

        image.save(thumbnail_path, 'JPEG')
        return width, height, file_size, thumbnail_width, thumbnail_height
    except (IOError, OSError):
        logger.exception('Error processing image')
        raise ArgumentError('Invalid file')


def _on_file_deleted(mapper, connection, target):
    cdn.delete(target.location)
    cdn.delete(target.thumbnail_location)


def _get_filename(extension):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in
                   range(GENERATED_FILE_NAME_LENGTH)), extension


def _get_extension(filename):
    if '.' in filename:
        ext = filename.rsplit('.', 1)[1]

        for k, v in CONVERT_EXTENSIONS:
            if ext == k:
                ext = v
                break

        if ext in ALLOWED_EXTENSIONS:
            return ext
    return None
