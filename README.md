# SmartPlantAPI

This Github Repository is made by Multimedia University Capstone Project Group 2 and it has all of the server side code used as the cloud platform for this project.

As a very quick rundown of this project, this project uses Django with an SQL lite database as a way to allow communication between the sensors, actuators, and the smartphone application developed for this project.

# API Documentation

### Endpoint: `/AddEntry`

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
    ```
    
### Endpoint: `/ActuatorData`

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
    ```
    
### Endpoint: `/RemoveOverride`

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
    ```
    
### Endpoint: `/Override`

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
    ```
