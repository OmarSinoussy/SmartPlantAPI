
# SmartPlantAPI

This Github Repository is made for Capstone Project Group 2 and it has all of the server side code used as the cloud platform for this project.

As a very quick rundown of this project, this project uses Django with an SQL lite database as a way to allow communication between the sensors, actuators, and the smartphone application developed for this project.

# API Documentation

### **Endpoint:** `/AddEntry`

- **Description:** This is the end point that is responsible for the addition of the entries to the database. 
The sensors ESP32 module uses this end point to send the data to it so that its stored in the database 
- **Method:** Post
- **Expected Headers:**
    -  **Plant-Id:** a unique identifier to each plant to identify the plant in the database and to ensure that multiple plants can be supported by the server.
-  **Expected Payload:**
    - **Soil Moisture:** the value of the soil moisture being read by the soil moisture sensor
    - **Light Intensity:** the value of the light intensity being read by the LDR sensor
    - **Water Level:** the value of the water level in the water tank being read by the water level sensor.
- **Expected Response**:
    - **status:** 200 If the entry has been added sucessfully, 400 if the addition has failed
    - **response:**: a verbal response of the status.
    - **entry_count:** the number of the entires that share the same Plant-Id
- **Sample Request:**
    ```py
    #A sample of a post request where we send data to the server via the AddEntry endpoint
    payload = {
        "Soil Moisture": 12,
        "Light Intensity": 89,
        "Water Level": 42
    }
    headers = {"Plant-Id": plant_id}
    requests.post(url + "AddEntry", headers = headers, json=payload).json() 
    
    #Sample Sucessful Response
    >>> {
           "status":200,
           "response":"Entry Added",
           "entry_count":7
        }
    ```

### **Endpoint:** `/StatisticalData`

- **Description:** This is an endpoint that is used to provide some statiscal data on the plant and its needs. Examples of what it provides are water level statistics, light sensor readings, and soil moisture sensor readings. This endpoint is typically used by the smartphone app.
- **Method:** Get
- **Expected Headers:**
    -  **Plant-Id:** a unique identifier to each plant to identify the plant in the database and to ensure that multiple plants can be supported by the server.
- **Expected Response**:
    - **status:** 200 if the request is sucessful, and 400 if the request made is in an invalid format
        - **response:** a verbal response of the status.
        - **graphs:** an array of graphs of the following data
            - **title:** the title of the graph
            - **y_axis_unit:** the the unit of the y_axis
            - **x_axis_unit:** the the unit of the x_axis
            - **gradient_from:** a hex color used for the gradient coloring
            - **gradient_to:** a hex color used for the gradient coloring
            - **x_axis_data:** the data used on the x_axis
            - **y_axis_data:** the data used on the y_axis
- **Sample Request:**
    ```py
    #Getting statistical data on the plants form the StatisticalData endpoint 
    headers = {'Plant-Id': "debugPlant"}
    requests.get(url + "StatisticalData", headers=headers).json()
    
    #Sample Sucessful Response
    >>> {
            "status":200,
            "response":"success",
            "graphs":[
                {
                    "title":"Light Intensity Statistics",
                    "y_axis_unit":"%",
                    "x_axis_unit":"",
                    "gradient_from":"",
                    "gradient_to":"",
                    "x_axis_data":[
                        "Monday",
                        "Tuesday",
                        "Wednessday",
                        "Thursday",
                        "Friday",
                        "Saturday",
                        "Sunday"
                    ],
                    "y_axis_data":[
                        42,
                        17,
                        47,
                        68,
                        40,
                        28,
                        40
                    ]
                },
                {
                    "title":"Soil Moisture Statistics",
                    "y_axis_unit":"%",
                    "x_axis_unit":"",
                    "gradient_from":"",
                    "gradient_to":"",
                    "x_axis_data":[
                        "Monday",
                        "Tuesday",
                        "Wednessday",
                        "Thursday",
                        "Friday",
                        "Saturday",
                        "Sunday"
                    ],
                    "y_axis_data":[
                        43,
                        38,
                        39,
                        23,
                        28,
                        26,
                        32
                    ]
                },
                {
                    "title":"Water Level Statistics",
                    "y_axis_unit":"L",
                    "x_axis_unit":"",
                    "gradient_from":"",
                    "gradient_to":"",
                    "x_axis_data":[
                        "Monday",
                        "Tuesday",
                        "Wednessday",
                        "Thursday",
                        "Friday",
                        "Saturday",
                        "Sunday"
                    ],
                    "y_axis_data":[
                        49,
                        46,
                        61,
                        19,
                        11,
                        52,
                        29
                    ]
                }
            ]
        }
    ```

### **Endpoint:** `/AppBasicData`

- **Description:** This endpoint is responsible for providing all of the basic data about the plant to the smartphone application. This is data such as the latest sensor readings, And some reports on the equipment and the water tank.
- **Method:** Get
- **Expected Headers:**
    -  **Plant-Id:** a unique identifier to each plant to identify the plant in the database and to ensure that multiple plants can be supported by the server.
- **Expected Response**:
    - **status:** 200 if the retrieval is done, 500 if it fails
    - **metadata:** a dictionary of some metadata on the request
	    - **last_reading_time:** the time that the last reading was made. Converted to the Malaysian timezone.
        - **override:** a boolean that defines if there is an active override or not
    - **plant_state:**
		- **state:** a verbal state of the plant, may either be happy, sad, or hungry
		- **description:** a description of the above state
	- **sensor_readings:** an array of dictionaries containing data on the sensors. entries in this array follow the following format
		- **name:** the sensor name
		- **description:** a description of what this sensor is used for
		- **readings:** an array of the readings read by the sensor and  all of the possible unit conversions
	- **reports:** an array of reports containing data on the equipment. Each report has the following format
		- **title:** the title of the given report
		- **header_text:** the header of the report
		- **value:** the values of the given report
		- **description:** a verbal description of the title and value of the report
- **Sample Request:**
    ```py
    #A sample request for the application data
    headers = {"Plant-Id": plant_id}
    requests.get(url +  'AppBasicData', headers=headers).json()
    
    #Sample Sucessful Response
    >>> {
            "metadata":{
                "last_reading_time":"2020-08-21T15:21:36.941+08:00"
            },
            "plant_state":{
                "state":"Hungry",
                "description":"Your plant requires more soil moisture content to continue healthy growth."
            },
            "sensor_readings":[
                {
                    "name":"Soil Moisture",
                    "description":"The current light intensity.",
                    "readings":[
                    "12%"
                    ]
                },
                {
                    "name":"Light Intensity",
                    "description":"The current light intensity.",
                    "readings":[
                    "89%"
                    ]
                },
                {
                    "name":"Water Level",
                    "description":"The current water level in the tank.",
                    "readings":[
                    "2.1 Litre",
                    "42%"
                    ]
                }
            ],
            "reports":[
                {
                    "title":"Water Tank Report",
                    "header_text":"Water Level",
                    "value":"2.1 Litre - 42%",
                    "description":"With the current water level in the tank, it can last for another 7 days without any intervension"
                },
                {
                    "title":"Water Pump Report",
                    "header_text":"Pump State",
                    "value":true,
                    "description":"The water pump is currently turned on and watering the plant"
                },
                {
                    "title":"Light Source Report",
                    "header_text":"Lamp Power",
                    "value":10,
                    "description":"The light source is currently working at 10% intensity. The light intensity depends on the time of day and the current intensity of the light in the room."
                }
            ]
        }
	```
- **Notes:** *The statistics endpoint is not this endpoint. Go through the documentation to find the endpoint used in the statistics*

### **Endpoint:** `/ActuatorData`

- **Description:** This is the main endpoint used to provide data to the actuator side of things. This endpoint is typically only used by the ESP32 module connected to the actuators. A different endpoint is used for the mobile application.
- **Method:** Get
- **Expected Headers:**
    -  **Plant-Id:** a unique identifier to each plant to identify the plant in the database and to ensure that multiple plants can be supported by the server.
- **Expected Response**:
    - **status:** 200 upon sucess, 400 or 500 upon failure
    - **override:** May either be true or false, If the values have been overridden by the user input, a True is returned, else, a false is returned
    - **Lamp Intensity State:** the intensity that the lamp should run at. This is sent as a percentage.
    - **Water Pump State:** this variable defines whether the water pump should be turned on or off
- **Sample Request:**
    ```py
    #A sample of the code that gets the data that is sent to the actuator
    headers = {"Plant-Id": plant_id}
    requests.get(url + "ActuatorData", headers = headers, json=payload).json()
    
    #Sample Sucessful Response
    >>> {
           "status":200,
           "override":false,
           "Lamp Intensity State":10,
           "Water Pump State":true
        }
    ```
- **Notes:** *This method must first check if there has been an override request made to the actuators by the smartphone app. if such a thing has been made, then the server trusts the user's decision for a given amount of time and then goes back again to regulate the plant state. To change how long an override request is valid, the* `override_validity` *variable in the* `override_data()` *function is changed to showcase such change.*
    
### **Endpoint:** `/RemoveOverride`

- **Description:** This is an API endpoint that removes all of the override requests made to the server for a specific plant id.
- **Method:** Delete
- **Expected Headers:**
    -  **Plant-Id:** a unique identifier to each plant to identify the plant in the database and to ensure that multiple plants can be supported by the server.
- **Expected Response**:
    - **status:** 200 If the entry has been added sucessfully, 400 if the addition has failed
    - **response:** a verbal response of the status.
    - **count:** this count should always be 0 if the request has been done sucesffuly
- **Sample Request:**
    ```py
    #Removing the override request made to the server for a specific plant_id
    headers = {"Plant-Id": plant_id}
    requests.delete(url + "RemoveOverride", headers = headers).json()
    
    #Sample Sucessful Response
    >>> {
           "status":200,
           "response":"Records have been removed sucessfully",
           "count":0
        }
    ```
    
### **Endpoint:** `/Override`

- **Description:** This method is used to send an override request to server. Bascially telling the server "I want to have control over my own plant, you dont worry about regulating anything" In this case, the user assumes full control over the plant until the override request expires
- **Method:** Post
- **Expected Headers:**
    -  **Plant-Id:** a unique identifier to each plant to identify the plant in the database and to ensure that multiple plants can be supported by the server.
- **Expected Payload:**
    - **Lamp Intensity State:** the intensity that the lamp should run at. This is sent as a percentage.
    - **Water Pump State:** this variable defines whether the water pump should be turned on or off
- **Expected Response**:
    - **status:** 200 If the entry has been added sucessfully, 400 if the addition has failed
    - **response:** a verbal response of the status.
- **Sample Request:**
    ```py
    #A sample of the code that performs override requests to the server
    payload = {
        "Lamp Intensity State": 84,
        "Water Pump State": True
    }
    headers = {"Plant-Id": plant_id}
    requests.post(url + "Override", headers = headers, json=payload).json()
    
    #Sample Sucessful Response
    >>> {
           "status":200,
           "response":"override request made"
        }
    ```
