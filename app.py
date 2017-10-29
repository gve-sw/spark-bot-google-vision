#
#   Hantzley Tauckoor (htauckoo@cisco.com)
#       October 2017
#
#       This sample Spark bot application uses ngrok to facilitate a webhook to Spark
#
#
#   REQUIREMENTS:
#       Flask python module
#       ngrok - https://ngrok.com/
#       Spark account with Bot created
#       Spark webhook created with bot token
#       settings.py file, you can modify and rename settings_template.py
#       Google Cloud account and Vision API access
#
#   WARNING:
#       This script is meant for educational purposes only.
#       Any use of these scripts and tools is at
#       your own risk. There is no guarantee that
#       they have been through thorough testing in a
#       comparable environment and we are not
#       responsible for any damage or data loss
#       incurred with their use.
#


import requests
from flask import Flask, request, session, redirect
import json
import io
import os
import re
from google.cloud import vision
from google.cloud.vision import types
from PIL import Image


import logging
logging.basicConfig(level=logging.DEBUG)

from settings import bot_id, bot_token, ngrok_url, webhook_id, webhook_name

image_is_in_Spark = False
detect_macs = True
filename = None

base_img_width=1024

signature = "Hantzley Tauckoor - [\[Email\]](mailto:htauckoo@cisco.com) \
    [\[LinkedIn\]](http://linkedin.com/in/hantzley) \
    [\[@hantzley\]](http://twitter.com/hantzley) \
    [\[GitHub\]](http://github.com/hantzley)"

project_info = "Liked this Bot? Want to contribute or create your own? See \
    the project on [GitHub](https://github.com/Hantzley/spark-bot-google-vision)"

def resize_image (filename, base_img_width):
    img=Image.open(filename)

    #Only resize if image width > base_img_width
    if img.size[0] > base_img_width:
        wpercent= (base_img_width / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        img = img.resize((base_img_width, hsize), Image.ANTIALIAS)

        #Save resized Image
        new_filename = 'new_' + filename
        img.save(new_filename)

        #Remove old Image
        os.remove(filename)
        filename = 'new_' + filename

    #return final image name
    return filename

# get ngrok tunnels information
def get_ngrok_tunnels(ngrok_url):
    headers = {'cache-control': "no-cache"}
    response = requests.request("GET", ngrok_url, headers=headers)
    tunnels = response.json()
    return {
        'public_http_url' : tunnels['tunnels'][0]['public_url'],
        'public_https_url' : tunnels['tunnels'][1]['public_url']
    }

# set spark headers
def set_headers(access_token):
    accessToken_hdr = 'Bearer ' + access_token
    spark_header = {
        'Authorization':accessToken_hdr,
        'Content-Type':'application/json; charset=utf-8',
        }
    return (spark_header)

# update webhook with updated ngrok tunnel information
def update_webhook (the_headers,webhook_name,webhook_id,targetUrl):
    url = "https://api.ciscospark.com/v1/webhooks/" + webhook_id
    payload = "{\n\t\"name\": \"" + webhook_name + "\",\n\t\"targetUrl\": \"" + targetUrl + "\"\n}"
    response = requests.request("PUT", url, data=payload, headers=the_headers)
    return response.status_code

# posts a message to the room
def post_message_to_room(the_header,roomId,msg):
    message = {"roomId":roomId,"markdown":msg}
    uri = 'https://api.ciscospark.com/v1/messages'
    resp = requests.post(uri, json=message, headers=the_header)

# posts a messages in list format to the room
def post_messages_to_room(the_header,roomId,messages):
    for item in messages:
        message = {"roomId":roomId,"markdown":item}
        uri = 'https://api.ciscospark.com/v1/messages'
        resp = requests.post(uri, json=message, headers=the_header)

# get message details
def get_message_details(the_header,msgId):
    uri = 'https://api.ciscospark.com/v1/messages/' + msgId
    resp = requests.get(uri, headers=the_header)
    return resp.text


############################ Google Vision Functions ###########################

# [START def_detect_faces]
def detect_faces(path):
    """Detects faces in an image."""
    client = vision.ImageAnnotatorClient()

    # [START migration_face_detection]
    # [START migration_image_file]
    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)
    # [END migration_image_file]

    response = client.face_detection(image=image)
    faces = response.face_annotations

    lines = []

    # Names of likelihood from google.cloud.vision.enums
    likelihood_name = ('UNKNOWN', 'VERY_UNLIKELY', 'UNLIKELY', 'POSSIBLE',
                       'LIKELY', 'VERY_LIKELY')
    lines.append('\n**Faces:**')

    for face in faces:
        lines.append('* anger: {}'.format(likelihood_name[face.anger_likelihood]))
        lines.append('* joy: {}'.format(likelihood_name[face.joy_likelihood]))
        lines.append('* surprise: {}'.format(likelihood_name[face.surprise_likelihood]))

        vertices = (['({},{})'.format(vertex.x, vertex.y)
                    for vertex in face.bounding_poly.vertices])

        lines.append('* face bounds: {}'.format(','.join(vertices)))

    return lines
    # [END migration_face_detection]
# [END def_detect_faces]


# [START def_detect_faces_uri]
def detect_faces_uri(uri):
    """Detects faces in the file located in Google Cloud Storage or the web."""
    client = vision.ImageAnnotatorClient()
    # [START migration_image_uri]
    image = types.Image()
    image.source.image_uri = uri
    # [END migration_image_uri]

    response = client.face_detection(image=image)
    faces = response.face_annotations

    lines = []

    # Names of likelihood from google.cloud.vision.enums
    likelihood_name = ('UNKNOWN', 'VERY_UNLIKELY', 'UNLIKELY', 'POSSIBLE',
                       'LIKELY', 'VERY_LIKELY')
    lines.append('\n**Faces:**')

    for face in faces:
        lines.append('* anger: {}'.format(likelihood_name[face.anger_likelihood]))
        lines.append('* joy: {}'.format(likelihood_name[face.joy_likelihood]))
        lines.append('* surprise: {}'.format(likelihood_name[face.surprise_likelihood]))

        vertices = (['({},{})'.format(vertex.x, vertex.y)
                    for vertex in face.bounding_poly.vertices])

        lines.append('* face bounds: {}'.format(','.join(vertices)))

    return lines
# [END def_detect_faces_uri]


# [START def_detect_labels]
def detect_labels(path):
    """Detects labels in the file."""
    client = vision.ImageAnnotatorClient()

    # [START migration_label_detection]
    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)

    response = client.label_detection(image=image)
    labels = response.label_annotations

    lines = []
    lines.append('\n**Labels:**')

    for label in labels:
        lines.append('* ' + label.description)

    return lines
    # [END migration_label_detection]
# [END def_detect_labels]


# [START def_detect_labels_uri]
def detect_labels_uri(uri):
    """Detects labels in the file located in Google Cloud Storage or on the
    Web."""
    client = vision.ImageAnnotatorClient()
    image = types.Image()
    image.source.image_uri = uri

    response = client.label_detection(image=image)
    labels = response.label_annotations

    lines = []
    lines.append('\n**Labels:**')

    for label in labels:
        lines.append('* ' + label.description)

    return lines
# [END def_detect_labels_uri]


# [START def_detect_landmarks]
def detect_landmarks(path):
    """Detects landmarks in the file."""
    client = vision.ImageAnnotatorClient()

    # [START migration_landmark_detection]
    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)

    response = client.landmark_detection(image=image)
    landmarks = response.landmark_annotations

    lines = []
    lines.append('\n**Landmarks:**')

    for landmark in landmarks:
        lines.append('* ' + landmark.description)

    return lines
    # [END migration_landmark_detection]
# [END def_detect_landmarks]


# [START def_detect_landmarks_uri]
def detect_landmarks_uri(uri):
    """Detects landmarks in the file located in Google Cloud Storage or on the
    Web."""
    client = vision.ImageAnnotatorClient()
    image = types.Image()
    image.source.image_uri = uri

    response = client.landmark_detection(image=image)
    landmarks = response.landmark_annotations

    lines = []
    lines.append('\n**Landmarks:**')

    for landmark in landmarks:
        lines.append('* ' + landmark.description)

    return lines
# [END def_detect_landmarks_uri]


# [START def_detect_logos]
def detect_logos(path):
    """Detects logos in the file."""
    client = vision.ImageAnnotatorClient()

    # [START migration_logo_detection]
    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)

    response = client.logo_detection(image=image)
    logos = response.logo_annotations

    lines = []
    lines.append('\n**Logos:**')

    for logo in logos:
        lines.append('* ' + logo.description)

    return lines
    # [END migration_logo_detection]
# [END def_detect_logos]


# [START def_detect_logos_uri]
def detect_logos_uri(uri):
    """Detects logos in the file located in Google Cloud Storage or on the Web.
    """
    client = vision.ImageAnnotatorClient()
    image = types.Image()
    image.source.image_uri = uri

    response = client.logo_detection(image=image)
    logos = response.logo_annotations

    lines = []
    lines.append('\n**Logos:**')

    for logo in logos:
        lines.append('* ' + logo.description)

    return lines
# [END def_detect_logos_uri]


# [START def_detect_text]
def detect_text(path):
    """Detects text in the file."""
    client = vision.ImageAnnotatorClient()

    # [START migration_text_detection]
    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations

    lines = []
    lines.append('\n**Texts:**')

    for text in texts:
        lines.append('\n* "{}"'.format(text.description))

        vertices = (['({},{})'.format(vertex.x, vertex.y)
                    for vertex in text.bounding_poly.vertices])

        lines.append('* bounds: {}'.format(','.join(vertices)))

    return lines
    # [END migration_text_detection]
# [END def_detect_text]


# [START def_detect_text_uri]
def detect_text_uri(uri):
    """Detects text in the file located in Google Cloud Storage or on the Web.
    """
    client = vision.ImageAnnotatorClient()
    image = types.Image()
    image.source.image_uri = uri

    response = client.text_detection(image=image)
    texts = response.text_annotations

    lines = []
    lines.append('\n**Texts:**')

    for text in texts:
        lines.append('\n* "{}"'.format(text.description))

        vertices = (['({},{})'.format(vertex.x, vertex.y)
                    for vertex in text.bounding_poly.vertices])

        lines.append('* bounds: {}'.format(','.join(vertices)))

    return lines
# [END def_detect_text_uri]


# [START def_detect_web]
def detect_web(path):
    """Detects web annotations given an image."""
    client = vision.ImageAnnotatorClient()

    # [START migration_web_detection]
    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)

    response = client.web_detection(image=image)
    notes = response.web_detection

    lines = []
    lines.append('\n**Web annotations:**')

    if notes.pages_with_matching_images:
        lines.append('\n{} Pages with matching images retrieved'.format(
               len(notes.pages_with_matching_images)))

        for page in notes.pages_with_matching_images:
            lines.append('* Url   : {}'.format(page.url))

    if notes.full_matching_images:
        lines.append ('\n{} Full Matches found: '.format(
               len(notes.full_matching_images)))

        for image in notes.full_matching_images:
            lines.append('* Url  : {}'.format(image.url))

    if notes.partial_matching_images:
        lines.append ('\n{} Partial Matches found: '.format(
               len(notes.partial_matching_images)))

        for image in notes.partial_matching_images:
            lines.append('* Url  : {}'.format(image.url))

    if notes.web_entities:
        lines.append ('\n{} Web entities found: '.format(len(notes.web_entities)))

        for entity in notes.web_entities:
            lines.append('* Score      : {}'.format(entity.score))
            lines.append('* Description: {}'.format(entity.description))

    return lines
    # [END migration_web_detection]
# [END def_detect_web]


# [START def_detect_web_uri]
def detect_web_uri(uri):
    """Detects web annotations in the file located in Google Cloud Storage."""
    client = vision.ImageAnnotatorClient()
    image = types.Image()
    image.source.image_uri = uri

    response = client.web_detection(image=image)
    notes = response.web_detection

    lines = []
    lines.append('\n**Web annotations:**')

    if notes.pages_with_matching_images:
        lines.append('\n{} Pages with matching images retrieved'.format(
               len(notes.pages_with_matching_images)))

        for page in notes.pages_with_matching_images:
            lines.append('* Url   : {}'.format(page.url))

    if notes.full_matching_images:
        lines.append ('\n{} Full Matches found: '.format(
               len(notes.full_matching_images)))

        for image in notes.full_matching_images:
            lines.append('* Url  : {}'.format(image.url))

    if notes.partial_matching_images:
        lines.append ('\n{} Partial Matches found: '.format(
               len(notes.partial_matching_images)))

        for image in notes.partial_matching_images:
            lines.append('* Url  : {}'.format(image.url))

    if notes.web_entities:
        lines.append ('\n{} Web entities found: '.format(len(notes.web_entities)))

        for entity in notes.web_entities:
            lines.append('* Score      : {}'.format(entity.score))
            lines.append('* Description: {}'.format(entity.description))

    return lines
# [END def_detect_web_uri]


def detect_mac_addresses(path):
    """Detects MAC addresses in the image."""
    client = vision.ImageAnnotatorClient()
    mac_addresses = []
    lines = []
    lines.append('\n**MAC Addresses:**')

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations

    for text in texts:
        #Match MAC addresses in format aa:bb:cc:dd:ee:ff or aa-bb-cc-dd-ee-ff
        tmp_text = text.description

        match_regex = re.compile('^' + '[\:\-]'.join(['([0-9A-F]{1,2})']*6) + '$', re.IGNORECASE)
        matched_mac_addresses = match_regex.findall(tmp_text)
        if len(matched_mac_addresses) == 0:
            #Match MAC addresses in format aabbccddeeff
            match_regex = re.compile('^' + '([0-9A-F]{2})'*6 + '$', re.IGNORECASE)
            matched_mac_addresses = match_regex.findall(tmp_text)

        if len(matched_mac_addresses) > 0:
            #print (str(len(matched_mac_addresses)) + " matches found in text : " + tmp_text )
            for mac in matched_mac_addresses:
                lines.append('* ' + ':'.join(mac))

    return lines

################################################################################




# Flask used as listener for webhooks from Spark
app = Flask(__name__)

@app.route('/',methods=['POST'])
def listener():
    # On receipt of a POST (webhook), load the JSON data from the request
    data = json.loads(request.data.decode('utf-8'))
    headers = request.headers
    #print data

    messageID = data['data']['id']
    roomID = data['data']['roomId']

    #print ("Data from webhook:")
    #print (json.dumps(data, indent=4))

    #print ("\nHeaders from webhook:")
    #print (headers)

    # If the poster of the message was NOT the bot itself
    if data['actorId'] != bot_id:
        spark_headers = set_headers(bot_token)

        # Get more specific information about the message that triggered the webhook
        json_string = get_message_details(spark_headers, messageID)
        message = json.loads(json_string)

        #print ("\n\nMessage details: ")
        #print (json.dumps(message, indent=4))

        if 'files' in data['data']:
            for item in data['data']['files']:
                response = requests.request("GET", item, headers=spark_headers)
                if response.status_code == 200:
                    imgHeaders = response.headers
                    if 'image' in imgHeaders['Content-Type']:
                        filename = imgHeaders[
                            'Content-Disposition'].replace("attachment; ", "").replace('filename', '').replace('=', '').replace('"', '')

                        with open(filename, 'wb') as f:
                            f.write(response.content)

                        filename = resize_image(filename, base_img_width)

                        #Analyse image with Google Vision API
                        lines = detect_web(filename)
                        if len(lines) > 1:
                            myStr = '\n'.join(lines)
                            post_message_to_room(spark_headers,roomID,myStr)

                        lines = detect_text(filename)
                        if len(lines) > 1:
                            myStr = '\n'.join(lines)
                            post_message_to_room(spark_headers,roomID,myStr)

                        lines = detect_faces(filename)
                        if len(lines) > 1:
                            myStr = '\n'.join(lines)
                            post_message_to_room(spark_headers,roomID,myStr)

                        lines = detect_labels(filename)
                        if len(lines) > 1:
                            myStr = '\n'.join(lines)
                            post_message_to_room(spark_headers,roomID,myStr)

                        lines = detect_landmarks(filename)
                        if len(lines) > 1:
                            myStr = '\n'.join(lines)
                            post_message_to_room(spark_headers,roomID,myStr)

                        lines = detect_logos(filename)
                        if len(lines) > 1:
                            myStr = '\n'.join(lines)
                            post_message_to_room(spark_headers,roomID,myStr)

                        if detect_macs:
                            lines = detect_mac_addresses(filename)
                            if len(lines) > 1:
                                myStr = '\n'.join(lines)
                                post_message_to_room(spark_headers,roomID,myStr)


                        #Delete file
                        os.remove(filename)

                        post_message_to_room(spark_headers,roomID,project_info)

                    else:
                        #print(filename + " is not an image")
                        post_message_to_room(spark_headers,roomID,"Ahoy! Thanks for sending me your \
                            file. However, I only analyze images.")

        else:
            #print ("No files posted...")
            #let's see if there is an image URL in posted text
            #print ("Text posted: ", message['text'])
            urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message['text'])
            #print ("Urls found", urls)

            if len(urls) > 0:
                for url in urls:
                    #check if URL is an image
                    response = requests.head(url)
                    #print (response.headers.get('content-type'))

                    #Only send URL to Google Vision API if url is an image
                    if 'image' in response.headers.get('content-type'):
                        lines = detect_web_uri(url)
                        if len(lines) > 1:
                            myStr = '\n'.join(lines)
                            post_message_to_room(spark_headers,roomID,myStr)

                        lines = detect_text_uri(url)
                        if len(lines) > 1:
                            myStr = '\n'.join(lines)
                            post_message_to_room(spark_headers,roomID,myStr)

                        lines = detect_faces_uri(url)
                        if len(lines) > 1:
                            myStr = '\n'.join(lines)
                            post_message_to_room(spark_headers,roomID,myStr)

                        lines = detect_labels_uri(url)
                        if len(lines) > 1:
                            myStr = '\n'.join(lines)
                            post_message_to_room(spark_headers,roomID,myStr)

                        lines = detect_landmarks_uri(url)
                        if len(lines) > 1:
                            myStr = '\n'.join(lines)
                            post_message_to_room(spark_headers,roomID,myStr)

                        lines = detect_logos_uri(url)
                        if len(lines) > 1:
                            myStr = '\n'.join(lines)
                            post_message_to_room(spark_headers,roomID,myStr)

                        if detect_macs:
                            #Download the image and find MAC addresses
                            response = requests.request("GET", url)
                            filename = url.split("/")[-1]
                            with open(filename, 'wb') as f:
                                f.write(response.content)

                            filename = resize_image(filename, base_img_width)

                            lines = detect_mac_addresses(filename)
                            if len(lines) > 1:
                                myStr = '\n'.join(lines)
                                post_message_to_room(spark_headers,roomID,myStr)

                        post_message_to_room(spark_headers,roomID,project_info)
                    else:
                        #print(url + " is not an image")
                        post_message_to_room(spark_headers,roomID,"Ahoy! Thanks for sending me your \
                            url. However, I only analyze images.")

            elif 'help' in message['text']:
                post_message_to_room(spark_headers,roomID,"Hey! This is bot is easy to use. \
                    Just post an image to the Spark room, and the Bot will tell you what it sees. \
                    Give it a try and send me your feedback.\n\nThank you,\n\n" + signature)

    return "OK"


# Runs the listener
if __name__ == '__main__':
    #get ngrok tunnel details and update webhook
    print ("Updating webhook with ngrok tunnel details")
    headers = set_headers(bot_token)
    ngrok_tunnels = get_ngrok_tunnels(ngrok_url)
    public_url = ngrok_tunnels['public_http_url'] # to use https, use the 'public_https_url' key instead
    print ("Webhook update status code: ", update_webhook(headers, webhook_name, webhook_id, public_url))

    #launching main application
    print ("Launching spark bot application")
    app.run(host='0.0.0.0', port=8080, debug=True)
