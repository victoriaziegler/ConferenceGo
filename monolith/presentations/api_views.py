from django.http import JsonResponse
from .models import Presentation
from common.json import ModelEncoder
from django.views.decorators.http import require_http_methods
import json
from events.models import Conference
from events.api_views import ConferenceListEncoder
import pika


class PresentationListEncoder(ModelEncoder):
    model = Presentation
    properties = ["title"]


@require_http_methods(["GET", "POST"])
def api_list_presentations(request, conference_id):
    if request.method == "GET":
        presentations = Presentation.objects.all()
        return JsonResponse(
            {"presentations": presentations},
            encoder=PresentationListEncoder,
            safe=False,
        )
    else:
        content = json.loads(request.body)
        try:
            conference = Conference.objects.get(id=conference_id)
            content["conference"] = conference
        except Conference.DoesNotExist:
            return JsonResponse(
                {"message": "Invalid conference id"},
                status=400,
            )
        presentation = Presentation.create(**content)
        return JsonResponse(
            presentation,
            encoder=PresentationDetailEncoder,
            safe=False,
        )


class PresentationDetailEncoder(ModelEncoder):
    model = Presentation
    properties = [
        "presenter_name",
        "company_name",
        "presenter_email",
        "title",
        "synopsis",
        "created",
        "conference",
    ]
    encoders = {
        "conference": ConferenceListEncoder(),
    }

    def get_extra_data(self, o):
        return {"status": o.status.name}


@require_http_methods(["DELETE", "GET", "PUT"])
def api_show_presentation(request, pk):
    if request.method == "GET":
        presentation = Presentation.objects.get(id=pk)
        return JsonResponse(
            presentation,
            encoder=PresentationDetailEncoder,
            safe=False,
        )
    elif request.method == "DELETE":
        count, _ = Presentation.objects.filter(id=pk).delete()
        return JsonResponse({"deleted": count > 0})
    else:
        content = json.loads(request.body)
        try:
            if "presentation" in content:
                presentation = Presentation.objects.get(id=content["presentation"])
                content["presentation"] = presentation
        except Presentation.DoesNotExist:
            return JsonResponse(
                {"message": "Invalid presentation"},
                status=400,
            )
        Presentation.objects.filter(id=pk).update(**content)
        presentation = Presentation.objects.get(id=pk)
        return JsonResponse(
            presentation,
            encoder=PresentationDetailEncoder,
            safe=False,
        )


@require_http_methods(["PUT"])
def api_approve_presentation(request, pk):
    presentation = Presentation.objects.get(id=pk)
    presentation.approved_status()
    send_message("APPROVED", presentation)
    return JsonResponse(
        presentation,
        encoder=PresentationDetailEncoder,
        safe=False,
    )


@require_http_methods(["PUT"])
def api_reject_presentation(request, pk):
    presentation = Presentation.objects.get(id=pk)
    presentation.rejected_status()
    send_message("REJECTED", presentation)
    return JsonResponse(
        presentation,
        encoder=PresentationDetailEncoder,
        safe=False,
    )


def send_message(status_input, presentation):
    if status_input == "APPROVED":
        parameters = pika.ConnectionParameters(host="rabbitmq")
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue="presentation_approvals")
        channel.basic_publish(
            exchange="",
            routing_key="presentation_approvals",
            body=json.dumps(
                {
                    "presenter_name": presentation.presenter_name,
                    "presenter_email": presentation.presenter_email,
                    "title": presentation.title,
                }
            ),
        )
        print("Approving status...")
        connection.close()
    elif status_input == "REJECTED":
        parameters = pika.ConnectionParameters(host="rabbitmq")
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue="presentation_rejections")
        channel.basic_publish(
            exchange="",
            routing_key="presentation_rejections",
            body=json.dumps(
                {
                    "presenter_name": presentation.presenter_name,
                    "presenter_email": presentation.presenter_email,
                    "title": presentation.title,
                }
            ),
        )
        print("Rejecting status...")
        connection.close()
