from django.conf import settings
from django.utils import timezone
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from smart_plant_api.models import ReadingEntry, OverrideRequest, TokenPlantIDBind, NotificationSent
import json, collections, pytz, random, datetime, statistics

from exponent_server_sdk import DeviceNotRegisteredError
from exponent_server_sdk import PushClient
from exponent_server_sdk import PushMessage
from exponent_server_sdk import PushResponseError
from exponent_server_sdk import PushServerError
from requests.exceptions import ConnectionError
from requests.exceptions import HTTPError

#All of the following are helper methods
def generate_error_message(error_message) -> str:
    '''
    A method used to generate error messages to provide more info in the error message with a high consistency

    Arguments:
        |- error_message: The issue or the error

    Returns:
        |- (string): returns a string of the error message
    '''

    github_page = "https://github.com/OmarSinoussy/SmartPlantAPI"
    return f"{error_message}. Please visit {github_page} for API documentation and more information on this error"

def override_data(plant_id) -> dict:
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
    override_requests = OverrideRequest.objects.filter(plant_id = plant_id)
    if len(override_requests) == 0 or (timezone.now().date() - override_requests[len(override_requests) - 1].request_time).seconds / 60 > override_validity:
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

def calculate_actuator_values(light_intensity, soil_moisture) -> tuple:
    '''
    A method used to calculate the lamp_intensity_state, and the water_pump_state based on the light_intensity and the soil moisture

    Arguments:
        |- light_intensity: the amount of light that the plant is currently exposed to
        |- soil_moisture: the amount of moisture currently in the soil

    Returns
        |- (tuple): a tuple of the (lamp_intensity_state, water_pump_state)
    '''
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
    # if soil_moisture < 100:
    if soil_moisture < 65:
        water_pump_state = True
    
    return (lamp_intensity_state, water_pump_state)

def print_v(string, end="\n") -> None:
    '''
    A very simple method used to print a string if the verbouse parameter in the settings is set to true, othrewise it doesnt print it.

    Arguments:
        |- string: the string to print
        |- end: the end of the string

    '''
    if settings.VERBOUSE:
        print(string, end=end)

def send_notification(token, title, message):
    '''
    A method used to send a notification to the application using the exponent_server_sdk library. 

    Arguments:
        |- token: The Expo notification token to send notifications to
        |- title: The title of the notification that displays on the screen
        |- messag: The message included in the body of the message
    '''
    extra = None
    try:
        response = PushClient().publish(
            PushMessage(to=token,
                        title=title,
                        body=message,
                        sound='default',
                        data=extra))
    except PushServerError as exc:
        # Encountered some likely formatting/validation error.
        rollbar.report_exc_info(
            extra_data={
                'token': token,
                'message': message,
                'extra': extra,
                'errors': exc.errors,
                'response_data': exc.response_data,
            })
        raise
    except (ConnectionError, HTTPError) as exc:
        # Encountered some Connection or HTTP error - retry a few times in
        # case it is transient.
        rollbar.report_exc_info(
            extra_data={'token': token, 'message': message, 'extra': extra})
        raise self.retry(exc=exc)

    try:
        # We got a response back, but we don't know whether it's an error yet.
        # This call raises errors so we can handle them with normal exception
        # flows.
        response.validate_response()
    except DeviceNotRegisteredError:
        # Mark the push token as inactive
        from notifications.models import PushToken
        PushToken.objects.filter(token=token).update(active=False)
    except PushResponseError as exc:
        # Encountered some other per-notification error.
        rollbar.report_exc_info(
            extra_data={
                'token': token,
                'message': message,
                'extra': extra,
                'push_response': exc.push_response._asdict(),
            })
        raise self.retry(exc=exc)

#All ofthe following are the views methods
def welcome_view(request):
    '''
    A very simple method used to verify that he server is up and running

    Expected Response:
        |- status: 200 or 500 depending on whether the server is online or not
        |- response: a verbal response of the status.    
    '''
    return JsonResponse({'status': 200, 'response': 'Server is up and running'}, status=200)

@csrf_exempt
def add_entry(request):
    '''
    This is the end point that is responsible for the addition of the entries to the database.
    The sensors ESP32 module uses this end point to send the data to it so that its stored in the database.
    This endpoint is also responsbile for sending the notifications.

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
            |- entry_count: the number of the entires that share the same Plant-Id

    Get: No get requests are allowed to this end point. A get request will result in a status 400 response
    '''
    def check_and_send(monitored_quantity_name, monitored_quantity_value, minimum_value, title, message, wait_time):
        if monitored_quantity_value < minimum_value:
            notifications_sent = NotificationSent.objects.filter(plant_id = plant_id)
            
            shouldContinue = True
            for notification in notifications_sent:
                if notification.reason == monitored_quantity_name and notification.minutes_since_notification(timezone.now()) < wait_time:
                    shouldContinue = False
                    break

            if shouldContinue:
                NotificationSent(plant_id = plant_id, reason = monitored_quantity_name, time=timezone.now()).save()
                tokens = TokenPlantIDBind.objects.filter(plant_id = request.headers.get('Plant-Id'))[0].tokens.split(',')
                for token in tokens:
                    send_notification(token, title, message)

    if request.method == "POST":
        sensor_readings = json.loads(request.body)
        plant_id = request.headers.get('Plant-Id')

        if sensor_readings.get('Soil Moisture') == None or sensor_readings.get('Light Intensity') == None or sensor_readings.get('Water Level') == None:
            return JsonResponse({'status': 400,
                                'response': generate_error_message('Not all payload items were provided')},
                                status = 400)

        if plant_id == None:
            return JsonResponse({'status': 400,
                                'response': generate_error_message('No Plant-Id provided in the request header')},
                                status = 400)

        ReadingEntry(plant_id = plant_id, reading_date = timezone.now(), soil_moisture_reading = sensor_readings["Soil Moisture"], light_intensity_reading = sensor_readings["Light Intensity"], water_level_reading = sensor_readings["Water Level"]).save()
        print_v(f'Soil Moisture: {sensor_readings["Soil Moisture"]}\nLight Intensity: {sensor_readings["Light Intensity"]}\nWater Level: {sensor_readings["Water Level"]}\n')
        entry_count = len(ReadingEntry.objects.all().filter(plant_id = plant_id))

        #Checking for the water level sensor and the soil moisture and sending notifications if they're too low.
        check_and_send('Water Level', sensor_readings["Water Level"], 20, "Water Level is too low", f"Your current water level is {sensor_readings['Water Level']}. Please refill the tank soon to keep your plant healthy", wait_time = 10)
        check_and_send('Soil Moisture', sensor_readings["Soil Moisture"], 20, "Your plant needs to be watered", f"Your current soil moisture is {sensor_readings['Soil Moisture']}. Please water your plant as soon as possible to ensure that it is kept healthy", wait_time = 10)

        return JsonResponse({"status":200, "response": "Entry Added", "entry_count": entry_count})
    else:
        return JsonResponse({"status": 400, "response": generate_error_message("Endpoint only accepts post requests")}, status = 400)

def statistical_data(request):
    '''
    This is an endpoint that is used to provide some statiscal data on the plant and its needs. Examples of what it provides are water level statistics, light sensor readings,
    and soil moisture sensor readings. This endpoint is typically used by the smartphone app.

    Endpoint: /StatisticalData

    Get:
        Expected Headers:
            |- Plant-Id: a unique identifier to each plant to identify the plant in the database and to ensure 
            |- Period: An optional header that defines the length of time to get the data for. Defaults to 7 days when this parameter is not defined.
        Expected Payload: None
        Expected Response:
            |- status: 200 if the request is sucessful, and 400 if the request made is in an invalid format
            |- response: a verbal response of the status.
            |- graphs: an array of graphs of the following data
                |- title: the title of the graph
                |- y_axis_unit: the the unit of the y_axis
                |- x_axis_unit: the the unit of the x_axis
                |- gradient_from: a hex color used for the gradient coloring
                |- gradient_to: a hex color used for the gradient coloring
                |- x_axis_data: the data used on the x_axis
                |- y_axis_data: the data used on the y_axis

    Post: No post requests are allowed to this end point. A post request will result in a status 400 response    
    '''
    def generate_graph_data(title, y_axis_unit, x_axis_unit, gradient_from, gradient_to, x_axis_data, y_axis_data) -> dict:
        '''
        A simple helper method local to this view that is used to generate the graph data sent back as a response
        Why do we use this method? To ensure consistent naming of the keys of the dictionary
        '''
        return {
            'title': f'{title} Statistics',
            'y_axis_unit': y_axis_unit,
            'x_axis_unit': x_axis_unit,
            'gradient_from': gradient_from,
            'gradient_to': gradient_to,
            'x_axis_data': x_axis_data,
            'y_axis_data': y_axis_data,
            'minimum': min(y_axis_data),
            'maximum': max(y_axis_data),
            "average": int(sum(y_axis_data) / len(y_axis_data)),
            'todays': y_axis_data[-1]
        }

    def get_reading_entry_average(reading_entry_array) -> dict:
        '''
        A simple helper method that can be used to find the average from the given reading entry array given

        Arguments:
            |- reading_entry_array: an array of reading entries 
    
        Returns: 
            |- (dict): of the data. The following is the format of the dict
                {
                    soil_moisture_reading: (float)
                    light_intensity_reading: (float)
                    water_level_reading: (float)
                }
        '''
        light_intensity_readings = []
        soil_moisture_readings = []
        water_level_readings = []
        for entry in reading_entry_array:
            light_intensity_readings.append(entry.light_intensity_reading)
            soil_moisture_readings.append(entry.soil_moisture_reading)
            water_level_readings.append(entry.water_level_reading)

        return {
            'light_intensity_reading': statistics.mean(light_intensity_readings if len(soil_moisture_readings) != 0 else [0]),
            'soil_moisture_reading': statistics.mean(soil_moisture_readings if len(soil_moisture_readings) != 0 else [0]),
            'water_level_reading': statistics.mean(water_level_readings if len(soil_moisture_readings) != 0 else [0])
        }

    if request.method == "GET":
        if request.headers.get('Plant-Id') == None:
            return JsonResponse({'status': 400,
                                'response': generate_error_message('No Plant-Id provided in the request header')},
                                status = 400)

        todays_date = timezone.now().date()
        number_of_data = request.headers.get('Period') if request.headers.get('Period') != None else 7

        applicable_dates = [todays_date - datetime.timedelta(days=i) for i in range(0, number_of_data, 1)][::-1]
        x_axis = [date.strftime("%a") for date in applicable_dates]
        applicable_data = [ReadingEntry.objects.filter(plant_id = request.headers.get('Plant-Id'), reading_date = date) for date in applicable_dates]
        applicable_data = list(map(get_reading_entry_average, applicable_data))

        light_intensity_stats = [int(data['light_intensity_reading']) for data in applicable_data]
        soil_moisture_stats = [int(data['soil_moisture_reading']) for data in applicable_data]
        water_level_stats = [int(data['water_level_reading']) for data in applicable_data]

        #Returning the data obtained from the database (at this point this data is random. When the DB integration happens, it wont be any longer)
        return JsonResponse({
            'status': 200,
            'response': 'success',
            'graphs': [
                generate_graph_data(title='Light Intensity', y_axis_unit='%', x_axis_unit='', gradient_from="#4e54c8", gradient_to="#8f94fb", x_axis_data=x_axis, y_axis_data=light_intensity_stats),
                generate_graph_data(title='Soil Moisture', y_axis_unit='%', x_axis_unit='', gradient_from="#ff9966", gradient_to="#ff5e62", x_axis_data=x_axis, y_axis_data=soil_moisture_stats),
                generate_graph_data(title='Water Level', y_axis_unit='%', x_axis_unit='', gradient_from="#536976", gradient_to="#292E49", x_axis_data=x_axis, y_axis_data=water_level_stats)
            ]
        })
    else:
        return JsonResponse({"status": 400, "response": generate_error_message('Endpoint only accepts get requests')}, status = 400)

@csrf_exempt
def remove_entries(request):
    '''
    This endpoint is reserved for removing all of the reading entries available for a plant. At the current moment of time, this is not
    accicible to anybody except for the server admin, The remove requests require to be accepted by the admin via an input statement
    
    Note: This endpoint is not currently accisible to the public for public usage. It's only enabled when the server is in debug mode and is disabled
          for the release version of the server-side code due to how dangerous it can be if left unattended
    
    Endpoint: /RemoveEntries

    Delete:
        Expected Headers:
            |- Plant-Id: a unique identifier to each plant to identify the plant in the database and to ensure 
        Expected Payload: None
        Expected Response:
            |- status: 200 If the entry has been removed sucessfully, 400 if the removal has failed
            |- response: a verbal response of the status.
            |- count: the number of entries avialble for this plant of this Plant-Id
    '''
    if not settings.DEBUG:
        return JsonResponse({'status': 403,
                            'response': 'This endpoint is only avialble in debug mode',
                            'count': 'n/a'},
                            status=403)

    if request.method == "DELETE":
        if request.headers.get('Plant-Id') == None:
            return JsonResponse({'status': 400,
                                'response': generate_error_message('No Plant-Id provided in the request header')},
                                status = 400)

        admin_response = input(f'A request has been made to delete entries for the plant with plant-id {request.headers.get("Plant-Id")}\nAccept this request? (y/n): ').lower()
        if 'y' in admin_response:
            ReadingEntry.objects.filter(plant_id = request.headers.get('Plant-Id')).delete()
            status = 200
            response_message = 'Removal request has been accepted'
        else:
            status = 500 
            response_message = 'Removal request has been denied'

        return JsonResponse({'status': status,
                            'response': response_message,
                            'count': len(ReadingEntry.objects.filter(plant_id = request.headers.get('Plant-Id')))},
                            status=status)

    else:
        return JsonResponse({"status": 400, "response": generate_error_message('Endpoint only accepts delete requests')}, status = 400)

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
            response = {'status': 200, 
                        'override': True, 
                        "Lamp Intensity State": override_request['data']['Lamp Intensity State'], 
                        "Water Pump State": override_request['data']['Water Pump State']}

            print_v(response)
            return JsonResponse(response)

        #The following section is the processing done based on the last entry added 
        else:
            entries = ReadingEntry.objects.all().filter(plant_id = request.headers.get('Plant-Id'))
            
            if len(entries) == 0:
                return JsonResponse({'status': 400,
                                    'response': generate_error_message('The Plant-Id provided has no entries linked to it')},
                                    status = 400) 

            last_entry = entries[len(entries) - 1]  #the Django ORM rejects any negative indexing, so the only way to get he last index is to do entries[len(entries) - 1]
            lamp_intensity_state, water_pump_state = calculate_actuator_values(last_entry.light_intensity_reading, last_entry.soil_moisture_reading)

            response = {'status': 200, 
                        'override': False, 
                        "Lamp Intensity State": lamp_intensity_state, 
                        "Water Pump State": water_pump_state}

            print_v(f'{response}\n')
            return JsonResponse(response)

    else:
        return JsonResponse({"status": 400, "response": generate_error_message('Endpoint only accepts get requests')}, status = 400)

def app_basic_data(request):
    '''
    This endpoint is responsible for providing all of the basic data about the plant to the smartphone application. This is data such as the latest sensor readings,
    And some reports on the equipment and the water tank.

    Note: the statistics endpoint is not this endpoint. Go through the documentation to find the endpoint used in the statistics 

    Endpoint: /AppBasicData

    Get:
        Expected Headers:
            |- Plant-Id: a unique identifier to each plant to identify the plant in the database and to ensure 
        Expected Payload: None
        Expected Response:
            |- status: 200 if the retrieval is done, 500 if it fails
            |- metadata: a dictionary of some metadata on the request
                |- last_reading_time: the time that the last reading was made. Converted to the Malaysian timezone.
                |- override: a boolean that defines if there is an active override or not
            |- plant_state:
                |- state: a verbal state of the plant, may either be happy, sad, or hungry
                |- description: a description of the above state
            |- sensor_readings: an array of dictionaries containing data on the sensors. entries in this array follow the following format
                |- name: the sensor name
                |- description: a description of what this sensor is used for
                |- readings: an array of the readings read by the sensor and all of the possible unit conversions
            |- reports: an array of reports containing data on the equippment. Each report has the following format
                |- title: the title of the given report
                |- header_text: the header of the report
                |- value: the values of the given report
                |- description: a verbal description of the title and value of the report

    Post: No post requests are allowed to this end point. A post request will result in a status 400 response
    '''
    response_dict = collections.defaultdict(dict)
    if request.method == "GET":
        if request.headers.get('Plant-Id') == None:
            return JsonResponse({'status': 400,
                                'response': generate_error_message('No Plant-Id provided in the request header')},
                                status = 400)

        latest_entry = ReadingEntry.objects.filter(plant_id = request.headers.get('Plant-Id')).order_by('-id')[0]
        water_tank_max_level = 5

        #Working on the metadata
        response_dict['metadata']['last_reading_time'] = latest_entry.reading_date

        #Working on the plant state
        plant_state = {
            'state': "",
            'description': ""
        }
        
        if latest_entry.soil_moisture_reading > 50 and latest_entry.light_intensity_reading > 50:
            plant_state['state'] = "Happy"
            plant_state['description'] = "Your plant is well watered, has adequate light exposure and is healthier than ever!"
        elif latest_entry.soil_moisture_reading < 50:
            plant_state['state'] = "Hungry"
            plant_state['description'] += "Your plant requires more soil moisture content to continue healthy growth."
        elif latest_entry.light_intensity_reading < 50:
            plant_state['state'] = "Sad"
            if plant_state['description'] == "":
                plant_state['description'] = "Your plant requires more light in order for it to continue healthy growth."
            else:
                plant_state['description'].replace(' to continue healthy growth.', 'and more light in order for it to continue healthy growth.')

        response_dict['plant_state'] = plant_state

        #Working on the Sensor Reading
        response_dict['sensor_readings'] = [
            {
                'name': 'Soil Moisture',
                'description': 'The current light intensity.',
                'readings': [f'{latest_entry.soil_moisture_reading}%']
            },
            {
                'name': 'Light Intensity',
                'description': 'The current light intensity.',
                'readings': [f'{latest_entry.light_intensity_reading}%']
            },
            {
                'name': 'Water Level',
                'description': 'The current water level in the tank.',
                'readings': [
                    f'{latest_entry.water_level_reading * water_tank_max_level / 100} L',
                    f'{latest_entry.water_level_reading}%']
            },
        ]

        #Working on the reports section
        #Getting the last override request
        override_info = override_data(request.headers.get('Plant-Id'))
        response_dict['metadata']['override'] = override_info['isOverridden']
        if override_info['isOverridden'] == True:
            lamp_intensity_state, water_pump_state = override_info['data']['Lamp Intensity State'], override_info['data']['Water Pump State']
        else:
            lamp_intensity_state, water_pump_state = calculate_actuator_values(latest_entry.light_intensity_reading, latest_entry.soil_moisture_reading)

        response_dict['reports'] = [
            {
                'title': 'Water Tank Report',
                'header_text': 'Water Level',
                'value': " - ".join([one for one in response_dict['sensor_readings'][2]['readings']]),
                'description': "With the current water level in the tank, it can last for another 7 days without any intervension"
            },
            {
                'title': 'Water Pump Report',
                'header_text': 'Pump State',
                'value': "On" if water_pump_state else "Off",
                'description': f'The water pump is currently {"turned on and watering the plant" if water_pump_state == True else "is not turned on."}'
            },
            {
                'title': 'Light Source Report',
                'header_text': 'Lamp Power',
                'value': f'{lamp_intensity_state}%',
                'description': f'The light source is currently working at {lamp_intensity_state}% intensity. The light intensity depends on the time of day and the current intensity of the light in the room.'
            }
        ]

        return JsonResponse(dict(response_dict), status=200)

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
        print_v(f"Lamp Intensity: {lamp_intensity_state}\tWater Pump: {water_pump_state}")

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

@csrf_exempt
def bindPlantIdToken(request):
    '''
    This endpoint is responsible for binding a plant_ids with expo tokens used for push notifications. 

    EndPoint: /BindPlantIdToeken

    Post:
        Expected Headers:
            |- Plant-Id: a unique identifier to each plant to identify the plant in the database and to ensure 
        Expected Payload:
            |- Token: the expo token provided by the app.
        Expected Response:
            |- status: 200 If the entry has been added sucessfully, 400 or 500 if the removal has failed
            |- response: a verbal response of the status.
            |- tokens: The expo push notifications tokens that are registered and bound to this plant_id
    '''
    if request.method == "POST":
        token = json.loads(request.body)['Token']
        
        if request.headers.get('Plant-Id') == None:
            return JsonResponse({'status': 400,
                                'response': generate_error_message('No Plant-Id provided in the request header')},
                                status = 400)
        if token == None or 'Expo' not in token:
            return JsonResponse({'status': 400,
                                'response': generate_error_message('No valid expo token was provided in the request')},
                                status = 400)

        bind = TokenPlantIDBind.objects.filter(plant_id = request.headers.get('Plant-Id'))
        if (len(bind) == 0):
            #No binds in the database. Create a bind and save it to the database
            TokenPlantIDBind(plant_id = request.headers.get('Plant-Id'), tokens = token).save()
        else:
            #A bind already exists in the database. Update the bind.
            tokens = bind[0].tokens
            if token not in tokens:
                bind.update(tokens = ",".join([tokens, token]))

        return JsonResponse({'status': 200,
                            'response': 'Token has been bound to the plant_id sucessfully',
                            'tokens': bind[0].tokens})

    else:
        return JsonResponse({"status": 400, "response": generate_error_message('Endpoint only accepts post requests')}, status = 400)

'''
TODO:
    - Ensure that the override requests actually expire in 5 minutes. Some early testing showed that they dont. If they do not find where this bug happens and work on it.
'''