import sys
import requests
import datetime
from datetime import date
from datetime import timedelta
import unicodedata
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re

if len(sys.argv) < 12:
    print 'Too few arguments. Give your API key, HubID, Email account, Email Password, Outgoing mail server (SMTP), Email port (SMTP), From address, To address, Sorting property, Sorting property value, properties to be included in the report and corresponding property titles. For example: \n python weekly_report_creator.py demo 62515 testname paSSw0rd smtp.test.com 587 sender@gmail.com receiver@gmail.com status "Meeting booked" firstname,lastname,jobtitle,notes_next_activity_date,notes_last_updated,status "First name","Last name","Job title","Next meeting","Date when booked","Prospecting status"'
    sys.exit(0)

# Sorting property: Sorting property is the property that defines whether a contact will be included to the weekly report or not
# Sorting property value: This parameter defines the value that contact's sorting property need to get in order to be included to the report
# Properties to be included to the report: Give a list of property labels you want to include to to your weekly report. Remember to give last activity date (Hubspot label name: notes_last_updated) to get the code run properly.
# Corresponding property titles: Give a list of property titles you want to be shown as headings in your report. Make sure that the order is the same as in your property label list.


api_key = sys.argv[1]
hub_id = sys.argv[2]
EMAIL_ACCOUNT = sys.argv[3]
password = sys.argv[4]
email_server = sys.argv[5]
email_port = sys.argv[6]
sender = sys.argv[7]
to_address = sys.argv[8]
sorting_property = sys.argv[9]
sorting_property_value = sys.argv[10]
properties = sys.argv[11].split(",")
header_list = sys.argv[12].split(",")

hubspot_api_base_url = 'https://api.hubapi.com/'


# Define functions that are needed later

def get_all_contacts():

    # Other variables
    all_contacts = []

    # fetching all contacts from Hubspot
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

def get_value_from_contact(contact, asked_value):
    properties = contact.get('properties')
    get_value = properties.get(asked_value)
    try:
        value = get_value.get('value')
        encoded_data = unicodedata.normalize('NFKD', value).encode('UTF-8', 'ignore')
        return encoded_data
    except:
        return "N/A"


def convert_timestamp_to_datetime(timestamp):
    if timestamp == "N/A":
        return "N/A"
    else:
        date = datetime.datetime.fromtimestamp(int(timestamp) / 1000)
        return date


def convert_timestamp_to_date(timestamp):
    if timestamp == "N/A":
        return "N/A"
    else:
        date = datetime.date.fromtimestamp(int(timestamp) / 1000)
        return date

all_contacts = get_all_contacts()


# a list of all contacts included to weekly report
contacts_to_report = []

# go through all contacts and include contacts to the weekly report based on sorting property
for contact in all_contacts:

    sorting_criteria = get_value_from_contact(contact, sorting_property)

    if sorting_criteria == sorting_property_value:
        i = 0
        property_value_list = []

        # go through all the selected properties of the contact and get property values

        while i < len(properties):
            property_value = get_value_from_contact(contact, properties[i])
            if re.search('\d+', property_value):
                try:
                    property_value = convert_timestamp_to_datetime(property_value).strftime('%d.%m.%Y at %H:%M')
                except:
                    pass

            property_value_list.append(property_value)
            i += 1

        try:
            # Select the contacts for the weekly report based on last activity date (need to be within last week)

            today = date.today()
            last_week = []

            # get last weeks's time interval (last 7 days)
            for i in range (1,7):
                last_week.append(today - timedelta(days=i))

            # check whether to include a contact to a weekly report and add it to the list

            last_activity_date = convert_timestamp_to_date(get_value_from_contact(contact, 'notes_last_updated'))

            if last_activity_date in last_week:
                contacts_to_report.append(property_value_list)

        except:
            print "Oooops, something went wrong! Unable to create a weekly report."


# prepare table of contacts and properties for the weekly report

total_rows= ""

for row in contacts_to_report:

    i = 0
    total_row_values = ""
    for s in row:
        row_value = """
        <td>{0}</td>
        """.format(row[i])
        i += 1
        total_row_values += row_value

    new_row = """
    <tr>
        {0}
    </tr>
    """.format(total_row_values)
    total_rows += new_row


i = 0
total_header = ""

for a in header_list:
    header_value = """
    <th><b>{0}</b></th>
    """.format(header_list[i])
    total_header += header_value
    i += 1


print "%s contacts added to the weekly report." %(len(contacts_to_report))

# create an email with weekly report as a table

message = MIMEMultipart('alternative')
message['Subject'] = "Hubspot weekly report"
message['From'] = sender
message['To'] = to_address

html = """\
<!DOCTYPE html>
<html>
<head>
    <style>
    th, td {
      text-align: left;
      border: 1px solid black;
      padding: 7px 9px;
    </style >
  </head >
  <body>
    <p>Helou!<br><br>
       Here is a the weekly report from the last 7 days.<br><br>
       Cheers!<br>
    </p>
    <table>
    <caption>Weekly report
    <thead>
    <tr>
        %s
    </tr>
    </thead>
    <tbody>
        %s
    </tbody>
    </table>
  </body>

</html>
""" %(total_header, total_rows)

message.attach(MIMEText(html, 'html'))

# connect to SMTP server and send email
if len(contacts_to_report) > 0:
    try:
        s = smtplib.SMTP(email_server, int(email_port))
        s.starttls()
        s.login(EMAIL_ACCOUNT, password)
        s.sendmail(sender, [to_address], message.as_string())
        s.quit()
        print "Email sent successfully"
    except:
        print "Unable to send email."

else:
    print "Nothing to be included to the report this week"
