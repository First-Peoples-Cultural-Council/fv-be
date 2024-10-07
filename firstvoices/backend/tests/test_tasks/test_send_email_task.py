from backend.tasks.send_email_tasks import send_email_task
from backend.tests.test_tasks.base_task_test import IgnoreTaskResultsMixin


class TestSendEmailTask(IgnoreTaskResultsMixin):
    TASK = send_email_task

    def get_valid_task_args(self):
        return ("subject", "message", ["testemail"])
