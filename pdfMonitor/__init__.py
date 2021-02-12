import logging
from os import environ
import io
import azure.functions as func
import requests
from requests import get, post
import time
import json

def get_configuration():
    max_tries = "15"    
    wait_sec = "5"
    max_wait_sec = "60"
    terms = {}

    try:
        import configuration as config
        
        max_tries = config.MAX_TRIES
        wait_sec = config.WAIT_SEC
        max_wait_sec = config.MAX_WAIT_SEC
        terms = config.TERMS
    except ImportError:
        pass

    max_tries = environ.get('MAX_TRIES', max_tries)
    wait_sec = environ.get('WAIT_SEC', max_tries)
    max_wait_sec = environ.get('WAIT_SEC', max_wait_sec)
    terms = environ.get('TERMS', terms)

    return {
        'max_tries': max_tries,
        'wait_sec': wait_sec,
        'max_wait_sec': max_wait_sec,
        'terms': terms
    }


def analyze_form(post_url, apim_key, model_id, data):
    configuration = get_configuration()

    # Endpoint URL

    if model_id == None:
        logging.error("Model IDentifier not provided")

    url = post_url + "/formrecognizer/v2.0-preview/custom/models/%s/analyze" % model_id

    params = {
        "includeTextDetails": True
    }

    headers = {
        # Request headers
        'Content-Type': 'application/pdf',
        'Ocp-Apim-Subscription-Key': apim_key,
    }

    try:
        resp = post(url=url, data=data, headers=headers, params=params)
        if resp.status_code != 202:
            logging.info("POST analyze failed:\n%s" % json.dumps(resp.json()))

        logging.info("POST analyze succeeded:\n%s" % resp.headers)
        get_url = resp.headers["operation-location"]

    except Exception as e:
        print("POST analyze failed:\n%s" % str(e))

    n_tries = int(configuration['max_tries'])
    n_try = 0
    wait_sec = int(configuration['wait_sec'])
    max_wait_sec = int(configuration['max_wait_sec'])

    while n_try < n_tries:
        try:
            resp = get(url=get_url, headers={
                       "Ocp-Apim-Subscription-Key": apim_key})
            resp_json = resp.json()
            if resp.status_code != 200:
                print("GET analyze results failed:\n%s" %
                      json.dumps(resp_json))
            status = resp_json["status"]
            if status == "succeeded":
                logging.info("Analysis succeeded")
  
                result =  json.dumps(resp_json)

                return result
            if status == "failed":
                print("Analysis failed:\n%s" % json.dumps(resp_json))
            # Analysis still running. Wait and retry.
            time.sleep(wait_sec)
            n_try += 1
            wait_sec = min(2*wait_sec, max_wait_sec)
        except Exception as e:
            logging.error("[Analyze] GET analyze results failed: %s" % str(e))
            return {
                'status' : 'fail',
                'message' : str(e)
            }


def main(inputBlob: func.InputStream, outputBlob: func.Out[str]):
  
    logging.info(f"Blob trigger executed!")
    logging.info(f"Blob Name: {inputBlob.name} ({inputBlob.length}) bytes")
    logging.info(f"Full Blob URI: {inputBlob.uri}")

    configuration = get_configuration()
    logging.info(f"Terms: {configuration['terms']}")

    post_url = environ.get('POST_URL', '') 
    apim_key = environ.get('APIM_KEY', '') 
    model_id = environ.get('MODEL_ID', '') 
    
    logging.info(f"URL: {post_url}, KEY: {apim_key}")
    data = io.BytesIO(inputBlob.read())

    output = analyze_form(post_url, apim_key, model_id, data)
    outputBlob.set(output)