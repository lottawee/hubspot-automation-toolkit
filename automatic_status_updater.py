import sys
import requests
import json
import datetime
import unicodedata

# The code changes a selected property status from one value to another based on next activity date
# potential targets of application:
# if the contact has a property that describes its position in the sales funnel (for example meeting scheduled or meeting held)
# this code automatically changes the contact status from meeting scheduled to meeting held if the date of the next meeting has been passed

if len(sys.argv) < 5:
    print 'Too few arguments. Give your API key, HubID, a property label of the property you want to change, value to be changed and the new value. For example: \n python automatic_status_updater.py demo 62515 status "Meeting scheduled" "Meeting held"'
    sys.exit(0)
api_key = sys.argv[1]
hub_id = sys.argv[2]
property_label = sys.argv[3]
value_to_be_changed = sys.argv[4]
new_value = sys.argv[5]

properties = ["firstname", "lastname", "notes_next_activity_date"]
properties.append(property_label)

hubspot_api_base_url = 'https://api.hubapi.com/'


# fetch all contacts from Hubspot

def get_all_contacts():

    # Other variables
    all_contacts = []

    # fetching all contacts
    print 'Starting to fetch all contacts from Hubspot...'
    contacts_api_endpoint = 'contacts/v1/lists/all/contacts/all'

    params = {'hapikey': api_key, 'count': '100', 'property': properties}
    headers = {'content-type': 'application/json'}
    response = requests.get(hubspot_api_base_url + contacts_api_endpoint, params = params, headers = headers)

    response_json = response.json()
    all_contacts.extend(response_json.get('contacts'))
    has_more = response_json.get('has-more')

    while has_more:
        vidoffset = response_json.get('vid-offset')
        params = {'hapikey': api_key, 'count': '100', "vidOffset": vidoffset, 'property': properties}
        response = requests.get(hubspot_api_base_url + contacts_api_endpoint, params=params)
        response_json = response.json()
        all_contacts.extend(response_json.get('contacts'))
        has_more = response_json.get('has-more')

    print "Great, %s contacts found!" %(str(len(all_contacts)))
    return all_contacts

# get selected property value of the contact
def get_value_from_contact(contact, asked_value):
    properties = contact.get('properties')
    get_value = properties.get(asked_value)
    try:
        value = get_value.get('value')
        encoded_data = unicodedata.normalize('NFKD', value).encode('UTF-8', 'ignore')
        return encoded_data
    except:
        return "N/A"

# convert a timestamp to datetime
def convert_timestamp_to_datetime(timestamp):
    if timestamp == "N/A":
        return "N/A"
    else:
        date = datetime.datetime.fromtimestamp(int(timestamp) / 1000)
        return date


# go through all contacts and check if the contact includes a property value you might want to change
# change the selected property value if the next activity date does not exist (the meeting has already been held)

all_contacts = get_all_contacts()

i = 0
t = 0

for contact in all_contacts:

    contact_id = contact.get('vid')
    property_label_value = get_value_from_contact(contact, property_label)
    if property_label_value == value_to_be_changed:

        next_activity_date = convert_timestamp_to_datetime(get_value_from_contact(contact, 'notes_next_activity_date'))

        # if the contact doesn't have next activity date (it has already been met), change the status from meeting scheduled to meeting held
        if next_activity_date == 'N/A':
            first_name = get_value_from_contact(contact, 'firstname')
            last_name = get_value_from_contact(contact, 'lastname')

            contacts_api_endpoint = '/contacts/v1/contact/vid/' + str(contact_id) + '/profile'
            params = {'hapikey': api_key}
            data = {"properties": [{"property": property_label,"value": new_value}]}
            headers = {'content-type': 'application/json'}

            response = requests.post(hubspot_api_base_url + contacts_api_endpoint, params = params, data = json.dumps(data), headers = headers)
            print "Contact %s %s: Property label %s updated to the new value %s" %(first_name, last_name, property_label, new_value)
            t += 1

print "%s contacts updated to the new value." %(t)
