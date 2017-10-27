# Spark Bot with Google Vision API integration

This Spark Bot uses Google Vision to analyze a pictures sent to it. You can either send a URL of an image or you can post the image itself into the spark room.



## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.



### Prerequisites
* [ngrok](http://ngrok.com) - Tunneling utility that exposes local servers behind NATs and firewalls to the public internet over secure tunnels.
* [Python 3.x](http://www.python.org) - Python interpreter
* [Flask](http://flask.pocoo.org/)  - Flask is a microframework for Python based on Werkzeug and Jinja 2
* Spark Bot - create a spark bot. See https://developer.ciscospark.com/bots.html
* Spark webhook - create a webhook using your Bot's token. See https://developer.ciscospark.com/webhooks-explained.html
* Google Cloud Vision API - See https://cloud.google.com/vision/docs


### Installing

Create a google cloud account and enable the Google Vision API. See https://cloud.google.com/vision/docs/before-you-begin


Download and extract [ngrok](http://ngrok.com/download. Then launch it.

```
$ ./ngrok http 8080
```

Install [Flask](http://flask.pocoo.org/) framework for Python using pip.

```
$ pip install Flask
```

Rename settings_template.py file to settings.py and update the variables with your Bot token, Bot id, webhook name, webhook id. If you choose to run ngrok on a different machine, you should update the ngrok_url variable.

Launch the Python application.

```
$ python app.py
```

On Spark, create a 1-1 room with the Spark Bot, and start posting images or URL of images in that room. You will notice the posted messages being printed by your application on the terminal. The Bot will post the result Google Vision analysis of the image to the Spark room.


## Authors

* **Hantzley Tauckoor** - [linkedin](http://linkedin.com/in/hantzley) [@hantzley](http://twitter.com/hantzley)
