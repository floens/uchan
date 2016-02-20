# Celery
BROKER_URL = 'amqp://uchan:yourpassword@yourhostname/uchanvhost'
CELERY_RESULT_BACKEND = 'rpc://'

# Move to JSON when exceptions are properly handled
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_ACCEPT_CONTENT = ['pickle']
CELERY_RESULT_SERIALIZER = 'pickle'

CELERY_IMPORTS = [
    'uchan.lib.tasks.post_task'
]
