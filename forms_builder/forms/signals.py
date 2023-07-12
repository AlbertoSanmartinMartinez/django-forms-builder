from _shared.utils.logging import get_logger
logger = getLogger(__name__)

from django import VERSION as DJANGO_VERSION
from django.dispatch import Signal
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist

from live_courses.models import LiveCourse
from fellowships.models import Fellowship
from online_fellowships.models import SelfManagedModule, MentoredModule

from services.utils import get_student_registration

if DJANGO_VERSION < (3, 1, 0):
    form_invalid = Signal(providing_args=["form"])
    form_valid = Signal(providing_args=["form", "entry"])
else:
    form_invalid = Signal()
    form_valid = Signal()


@receiver(form_valid)
def set_username(sender=None, form=None, entry=None, **kwargs):
    request = sender
    if request.user.is_authenticated:
        # Get the service from the form
        service = None
        service_models = [LiveCourse, Fellowship, SelfManagedModule, MentoredModule]
        for model in service_models:
            try:
                service = model.objects.get(feedback_form=entry.form)
            except ObjectDoesNotExist:
                pass
        if not service:
            logger.error('Unable to find service for feedback form: {}'\
                         .format(entry.form))
        else:
            try:
                registration = get_student_registration(service=service,
                                                        user=request.user)
                registration.has_completed_feedback_form = True
                registration.save()
            except Exception as e:
                logger.exception(e)
                logger.info('Unable to find service registration for {}, {}'\
                           .format(request.user, service))
            else:
                logger.debug('{} registration feedback form flag updated'\
                            .format(registration))

        field = entry.form.fields.get(label="username")
        field_entry, _ = entry.fields.get_or_create(field_id=field.id)
        field_entry.value = request.user.username
        field_entry.save()
