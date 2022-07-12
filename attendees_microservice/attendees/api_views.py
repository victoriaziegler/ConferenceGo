from django.http import JsonResponse
from common.json import ModelEncoder
from .models import Attendee, ConferenceVO
from django.views.decorators.http import require_http_methods
import json


class AttendeeListEncoder(ModelEncoder):
    model = Attendee
    properties = ["name"]


class ConferenceVODetailEncoder(ModelEncoder):
    model = ConferenceVO
    properties = ["name", "import_href"]


class AttendeeDetailEncoder(ModelEncoder):
    model = Attendee
    properties = [
        "email",
        "name",
        "company_name",
        "created",
        "conference",
    ]
    encoders = {
        "conference": ConferenceVODetailEncoder(),
    }


@require_http_methods(["GET", "POST"])
def api_list_attendees(request, conference_vo_id=None):
    if request.method == "GET":
        attendees = Attendee.objects.filter(conference=conference_vo_id)
        return JsonResponse(
            {"attendees": attendees},
            encoder=AttendeeListEncoder,
        )
    else:
        content = json.loads(request.body)

        # Get the Conference object and put it in the content dict
        try:
            conference_href = content["conference"]
            conference = ConferenceVO.objects.get(import_href=conference_href)
            content["conference"] = conference
        except ConferenceVO.DoesNotExist:
            return JsonResponse(
                {"message": "Invalid conference id"},
                status=400,
            )

        attendee = Attendee.objects.create(**content)
        return JsonResponse(
            attendee,
            encoder=AttendeeDetailEncoder,
            safe=False,
        )


@require_http_methods(["DELETE", "GET", "PUT"])
def api_show_attendee(request, pk):
    if request.method == "GET":
        attendee = Attendee.objects.get(id=pk)
        return JsonResponse(
            {"attendee": attendee},
            encoder=AttendeeDetailEncoder,
            safe=False,
        )
    elif request.method == "DELETE":
        count, _ = Attendee.objects.filter(id=pk).delete()
        return JsonResponse({"deleted": count > 0})
    else:
        content = json.loads(request.body)
        try:
            if "attendee" in content:
                attendee = Attendee.objects.get(id=content["attendee"])
                content["attendee"] = attendee
        except Attendee.DoesNotExist:
            return JsonResponse(
                {"message": "Invalid attendee"},
                status=400,
            )
        Attendee.objects.filter(id=pk).update(**content)
        presentation = Attendee.objects.get(id=pk)
        return JsonResponse(
            presentation,
            encoder=AttendeeDetailEncoder,
            safe=False,
        )
