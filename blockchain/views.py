import json

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from .tasks import process_events


@csrf_exempt
def process_blockchain_events(request):
    if request.method == "POST":
        decoded_data = request.body.decode("utf-8")

        try:
            data = json.loads(decoded_data)
            logs = data["event"]["data"]["block"]["logs"]
            if logs:
                print(f"{data['event']['network']} transaction found. Sending logs to queue")
                process_events.delay(data)
            return HttpResponse(200)

        except json.JSONDecodeError:
            print(f"Invalid JSON conversion from: {decoded_data}")





