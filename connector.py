import sys
import requests
import json

# case: too few arguments
if len(sys.argv) < 3:
    print 'Too few arguments. Give your HubID and API key. For example: \n python connector.py 62515 demo'
    sys.exit(0)

# Command line arguments
hub_id = sys.argv[1]
api_key = sys.argv[2]

# Other variables
hubspot_api_base_url = 'https://api.hubapi.com/'
all_contacts = []

# fetching all contacts
print 'Starting to fetch all contacts from Hubspot...'
contacts_api_endpoint = 'contacts/v1/lists/all/contacts/all'

payload = {'hapikey': api_key, 'count': '100'}
response = requests.get(hubspot_api_base_url + contacts_api_endpoint, params=payload)

response_json = response.json()
all_contacts.extend(response_json.get('contacts'))
has_more = response_json.get('has-more')

while has_more:
    vidoffset = response_json.get('vid-offset')
    payload = {'hapikey': api_key, 'count': '100', "vidOffset": vidoffset}
    response = requests.get(hubspot_api_base_url + contacts_api_endpoint, params=payload)
    response_json = response.json()
    all_contacts.extend(response_json.get('contacts'))
    has_more = response_json.get('has-more')

print str(len(all_contacts))
