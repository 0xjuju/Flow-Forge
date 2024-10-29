import json

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse


@csrf_exempt
def process_blockchain_events(request):
    if request.method == "POST":
        decoded_data = request.body.decode("utf-8")
        try:
            data = json.loads(decoded_data)
            print(data)
            return JsonResponse({"body": data})
        except json.JSONDecodeError:
            print(f"Invalid JSON conversion from: {decoded_data}")


