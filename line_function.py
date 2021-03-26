import requests
import json

def get_profile(LINE_API_BASE_URL, profile_access_token):
    options = LINE_API_BASE_URL + '/profile'
    auth_header = 'Bearer ' + profile_access_token
    headers = {'Authorization': auth_header}
    r = requests.get(options, headers=headers)
    return r.json()


# Messaging APIチャネルからpushメッセージを送信する
def push(to, message, LINE_API_BASE_URL, MESSAGING_API_ACCESSTOKEN):
    
    body = {"to": to, "messages":{}}
    objMessage = {"messages": [{"type":"text", "text":message}]}
    body.update(objMessage)
    
    url = LINE_API_BASE_URL + '/bot/message/push'
    header_authorization = 'Bearer ' + MESSAGING_API_ACCESSTOKEN
    headers = {'content-type': 'application/json; charset=UTF-8', 'authorization': header_authorization}
    
    r = requests.post(url, data=json.dumps(body), headers=headers)
    return r.status_code
