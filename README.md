# SmartPlantAPI

This Github Repository is made by Multimedia University Capstone Project Group 2 and it has all of the server side code used as the cloud platform for this project.

As a very quick rundown of this project, this project uses Django with an SQL lite database as a way to allow communication between the sensors, actuators, and the smartphone application developed for this project.

# API Documentation

### Endpoint: `/AddEntry`

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
    - **entry count:** the number of the entires that share the same Plant-Id
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
           "entry count":7
        }
    ```
    
### Endpoint: `/ActuatorData`

- **Description:** This is the main endpoint used to provide data to the actuator side of things. This endpint is typically only used by the ESP32 module connected to the actuators. A different endpoint is used for the mobile application.
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
    
### Endpoint: `/RemoveOverride`

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
    
### Endpoint: `/Override`

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
