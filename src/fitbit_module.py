import fitbit_auth

import datetime
import requests

# Get the current date and time
today = datetime.datetime.now()

# Set the API endpoint
endpoint = f"https://api.fitbit.com/1/user/{fitbit_auth.USERS['Nathan']}/activities/steps/date/" + today.strftime("%Y-%m-%d")

# Set the API headers
headers = {
    "Authorization": "Bearer YOUR_ACCESS_TOKEN"
}

# Make the API request
response = requests.get(endpoint, headers=headers)

# Check the response status code
if response.status_code == 200:
    # Get the steps walked
    steps = response.json()["activities-steps"]["value"]
    print("The number of steps walked today is:", steps)
else:
    print("There was an error:", response.status_code)



https://www.fitbit.com/oauth2/authorize?client_id=ABC123&response_type=code
&code_challenge=<code_challenge>&code_challenge_method=S256
&scope=activity%20heartrate%20location%20nutrition%20oxygen_saturation%20profile
%20respiratory_rate%20settings%20sleep%20social%20temperature%20weight