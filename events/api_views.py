from django.http import JsonResponse
from .models import Conference, Location
from common.json import ModelEncoder


class ConferenceListEncoder(ModelEncoder):
    model = Conference
    properties = ["name"]


def api_list_conferences(request):
    conferences = Conference.objects.all()
    return JsonResponse(
        {"conferences": conferences},
        encoder=ConferenceListEncoder,
    )


class LocationListEncoder(ModelEncoder):
    model = Location
    properties = ["name"]


class ConferenceDetailEncoder(ModelEncoder):
    model = Conference
    properties = [
        "name",
        "description",
        "max_presentations",
        "max_attendees",
        "starts",
        "ends",
        "created",
        "updated",
        "location",
    ]
    encoders = {
        "location": LocationListEncoder(),
    }


def api_show_conference(request, pk):
    conference = Conference.objects.get(id=pk)
    return JsonResponse(
        conference,
        encoder=ConferenceDetailEncoder,
        safe=False,
    )


def api_list_locations(request):
    locations = [
        {
            "name": location.name,
            "href": location.get_api_url(),
        }
        for location in Location.objects.all()
    ]
    return JsonResponse({"locations": locations})


class LocationDetailEncoder(ModelEncoder):
    model = Location
    properties = [
        "name",
        "city",
        "room_count",
        "created",
        "updated",
    ]

    def get_extra_data(self, o):
        return {"state": o.state.abbreviation}


def api_show_location(request, pk):
    location = Location.objects.get(id=pk)
    return JsonResponse(
        location,
        encoder=LocationDetailEncoder,
        safe=False,
    )
