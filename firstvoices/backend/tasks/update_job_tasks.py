from celery import shared_task


@shared_task
def validate_update_job(update_job_id):
    # Placeholder for the actual validation logic
    pass


@shared_task
def confirm_update_job(update_job_id):
    # Placeholder for the actual confirmation logic
    pass
