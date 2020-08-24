from django.shortcuts import render
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from smart_plant_api.models import ReadingEntry, OverrideRequest
import json, datetime
from collections import defaultdict

def generate_error_message(error_message):
    '''
    A method used to generate error messages to provide more info in the error message with a high consistency

    Arguments:
        |- error_message: The issue or the error

    Returns:
        |- (string): returns a string of the error message
    '''

    github_page = "https://github.com/OmarSinoussy/SmartPlantAPI"
    return f"{error_message}. Please visit {github_page} for API documentation and more information on this error"

def override_data(plant_id):
    '''
    This method gets data on whether the plant_id has a valid override request. If the plant has any override requests. It will return its data

    Arguments:
        |- Plant-Id: a unique identifier to each plant to identify the plant in the database and to ensure 
    
    Returns: 
        |- (dict): of the data. The following is the format of the dict
            {
                isOverridden: (bool)
                data: {
                    "Lamp Intensity State": (int),
                    "Water Pump State": (int)
                }
            }
    
    Notes: if there are no valid override requests, data is equal to None 
    '''
    override_validity = 5 #How long an override request is valid in minutes
    override_requests = OverrideRequest.objects.all().filter(plant_id = plant_id)
    if len(override_requests) == 0 or (timezone.now() - override_requests[len(override_requests) - 1].request_time).seconds / 60 > override_validity:
        return {
            "isOverridden": False,
            "data": None
        }
    
    return {
        "isOverridden": True,
        "data": {
            "Lamp Intensity State": override_requests[len(override_requests) - 1].lamp_intensity_state,
            "Water Pump State": override_requests[len(override_requests) - 1].water_pump_state,
        }
    }

@csrf_exempt
def add_entry(request):
    '''
    This is the end point that is responsible for the addition of the entries to the database.
    The sensors ESP32 module uses this end point to send the data to it so that its stored in the database 

    Endpoint: /AddEntry

    Post:
        Expected Headers:
            |- Plant-Id: a unique identifier to each plant to identify the plant in the database and to ensure 
        Expected Payload:
            |- Soil Moisture: the value of the soil moisture being read by the soil moisture sensor
            |- Light Intensity: the value of the light intensity being read by the LDR sensor
            |- Water Level: the value of the water level in the water tank being read by the water level sensor
        Expected Response:
            |- status: 200 If the entry has been added sucessfully, 400 if the addition has failed
            |- response: a verbal response of the status.
            |- entry count: the number of the entires that share the same Plant-Id

    Get: No get requests are allowed to this end point. A get request will result in a status 400 response
    '''
    if request.method == "POST":
        sensor_readings = json.loads(request.body)
        plant_id = request.headers.get('Plant-Id')

        ReadingEntry(plant_id = plant_id, reading_date = timezone.now(), soil_moisture_reading = sensor_readings["Soil Moisture"], light_intensity_reading = sensor_readings["Light Intensity"], water_level_reading = sensor_readings["Water Level"]).save()

        entry_count = len(ReadingEntry.objects.all().filter(plant_id = request.headers['Plant-Id']))
        print(entry_count)

        return JsonResponse({"status":200, "response": "Entry Added", "entry count": entry_count})
    else:
        return JsonResponse({"status": 400, "response": generate_error_message("Endpoint only accepts post requests")}, status = 400)

def actuator_data(request):
    '''
    This is the main endpoint used to provide data to the actuator side of things. This endpint is typically only used by
    the ESP32 module connected to the actuators. A different endpoint is used for the mobile application.

    Note: This method must first check if there has been an override request made to the actuators by the smartphone app.
          if such a thing has been made, then the server trusts the user's decision for a given amount of time and then goes
          back again to regulate the plant state. To change how long an override request is valid, the override_validity variable
          in the override_data function is changed to showcase such change.
    
    Endpoint: /ActuatorData

    Post: No post requests are allowed to this end point. A post request will result in a status 400 response

    Get: 
        Expected Headers:
            |- Plant-Id: a unique identifier to each plant to identify the plant in the database and to ensure 
        Expected Payload: No payload is expected to be supplied to this endpoint
        Expected Response:
            |- status: 200 upon sucess, 400 or 500 upon failure
            |- override: May either be true or false, If the values have been overridden by the user input, a True is returned, else, a false is returned
            |- Lamp Intensity State: the intensity that the lamp should run at. This is sent as a percentage.
            |- Water Pump State: this variable defines whether the water pump should be turned on or off
    '''
    if request.method == "GET":
        if request.headers.get('Plant-Id') == None:
            return JsonResponse({'status': 400,
                                'response': generate_error_message('No Plant-Id provided in the request header')},
                                status = 400)

        #Getting the override data of the plant
        override_request = override_data(request.headers.get('Plant-Id'))

        #Override the sensors and act upon the user input
        if override_request['isOverridden']:
            return JsonResponse({'status': 200, 
                                'override': True, 
                                "Lamp Intensity State": override_request['data']['Lamp Intensity State'], 
                                "Water Pump State": override_request['data']['Water Pump State']})

        #The following section is the processing done based on the last entry added 
        else:
            entries = ReadingEntry.objects.all().filter(plant_id = request.headers.get('Plant-Id'))
            
            if len(entries) == 0:
                return JsonResponse({'status': 400,
                                    'response': generate_error_message('The Plant-Id provided has no entries linked to it')},
                                    status = 400) 

            last_entry = entries[len(entries) - 1]  #the Django ORM rejects any negative indexing, so the only way to get he last index is to do entries[len(entries) - 1]
            soil_moisture = last_entry.soil_moisture_reading
            light_intensity = last_entry.light_intensity_reading
            water_level = last_entry.water_level_reading

            lamp_intensity_state = 0
            water_pump_state = False

            #Controlling the lamp intensity.
            if 0 <= light_intensity < 25:
                lamp_intensity_state = 100
            elif 25 <= light_intensity < 50:
                lamp_intensity_state = 75
            elif 50 <= light_intensity < 75:
                lamp_intensity_state = 50
            elif 75 <= light_intensity < 100:
                lamp_intensity_state = 10
            
            #Controlling the water pump.
            if soil_moisture < 75:
                water_pump_state = True
        
            return JsonResponse({'status': 200, 
                                'override': False, 
                                "Lamp Intensity State": lamp_intensity_state, 
                                "Water Pump State": water_pump_state})

    else:
        return JsonResponse({"status": 400, "response": generate_error_message('Endpoint only accepts get requests')}, status = 400)

@csrf_exempt
def Override(request):
    '''
    This method is used to send an override request to server. Bascially telling the server "I want to have control over my own plant, you dont worry about regulating anything"
    In this case, the user assumes full control over the plant until the override request expires

    Post:
        Expected Headers:
            |- Plant-Id: a unique identifier to each plant to identify the plant in the database and to ensure 
        Expected Payload:
            |- Lamp Intensity State: the intensity that the lamp should run at. This is sent as a percentage.
            |- Water Pump State: this variable defines whether the water pump should be turned on or off
        Expected Response:
            |- status: 200 If the entry has been added sucessfully, 400 if the addition has failed
            |- response: a verbal response of the status.

    Get: No get requests are allowed to this end point. A get request will result in a status 400 response
    '''
    if request.headers.get('Plant-Id') == None:
        return JsonResponse({'status': 400,
                            'response': generate_error_message('No Plant-Id provided in the request header')},
                            status = 400)

    if request.method == "POST":
        lamp_intensity_state = json.loads(request.body).get('Lamp Intensity State')
        water_pump_state = json.loads(request.body).get('Water Pump State')

        #only triggers if one of the above terms are not provided        
        if lamp_intensity_state == None or water_pump_state == None:
            return JsonResponse({"status": 400, "response": generate_error_message('Bad request. Either the lamp intensity or the water pump state were not provided')}, status = 400)

        OverrideRequest(plant_id = request.headers.get('Plant-Id'), request_time = timezone.now(), lamp_intensity_state = lamp_intensity_state, water_pump_state = water_pump_state).save()
        return JsonResponse({'status': 200, 'response': "override request made"})

    else:
        return JsonResponse({"status": 400, "response": generate_error_message('Endpoint only accepts post requests')}, status = 400)

@csrf_exempt
def RemoveOverride(request):
    '''
    This is an API endpoint that removes all of the override requests made to the server for a specific plant id.

    Delete:
        Expected Headers:
            |- Plant-Id: a unique identifier to each plant to identify the plant in the database and to ensure 
        Expected Payload: No payload is expected here
        Expected Response:
            |- status: 200 If the entry has been removed sucessfully, 400 if the removal has failed
            |- response: a verbal response of the status.
            |- count: this count should always be 0 if the request has been done sucesffuly
    '''
    if request.method == "DELETE":
        if request.headers.get('Plant-Id') == None:
            return JsonResponse({'status': 400,
                                'response': generate_error_message('No Plant-Id provided in the request header')},
                                status = 400)

        OverrideRequest.objects.filter(plant_id = request.headers.get('Plant-Id')).delete()
        return JsonResponse({'status': 200,
                            'response': 'Records have been removed sucessfully', 
                            'count': len(OverrideRequest.objects.filter(plant_id = request.headers.get('Plant-Id')))})

    else:
        return JsonResponse({"status": 400, "response": generate_error_message('Endpoint only accepts delete requests')}, status = 400)
