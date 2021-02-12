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


def analyze_text(page_no, text):
    configuration = get_configuration()
    terms = json.loads(configuration['terms'])
   
    keys = list(terms.keys())

    for key in keys:

        if terms[key]['text'] == text and int(terms[key]['page']) == page_no:

            print("%s==%s" % (terms[key]['text'], text))

            return terms[key]

    return None        
            

def analyze_response(resp_json):
    configuration = get_configuration()

    page_results = resp_json['analyzeResult']['pageResults']

    page_no = 0

    items = []

    for page_result in page_results:

        key_value_pairs= page_result['keyValuePairs']
        page_no += 1

        for key_value_pair in key_value_pairs:
            key = key_value_pair['key']
            value = key_value_pair['value']
            
            entry = analyze_text(page_no, key['text'])

            if entry != None:
                item = {}
                item['entry'] = entry    
                item['result'] = {
                    'key' : {
                        'text' : key['text'],
                        'bounding_box' : key['boundingBox']
                    },
                    'value' : {
                        'text' : value['text'],
                        'bounding_box' : value['boundingBox'],
                       
                    }
                }

                print(json.dumps(item))

                items.append(item)

    return items



def main(inputBlob: func.InputStream, outputBlob: func.Out[str]):
  
    logging.info(f"Blob trigger executed!")
    logging.info(f"Blob Name: {inputBlob.name} ({inputBlob.length}) bytes")
    logging.info(f"Full Blob URI: {inputBlob.uri}")

    configuration = get_configuration()
    logging.info(f"Terms: {configuration['terms']}")
    
    data = json.loads(io.BytesIO(inputBlob.read()).getvalue())

    output =  json.dumps(analyze_response(data))
    outputBlob.set(output)