
import requests
import json

class Session(object):
    def __init__(self, hmc_ip, userid, password):
        self.hmc_ip = hmc_ip
        self.userid = userid
	self.password = password

	self.auth_url = "{}{}{}" . format('https://', hmc_ip, ':6794')

        self.headers = {'Content-type' : 'application/json', 'Accept' : '*/*'}
        credentials = {'userid' : self.userid, 'password' : self.password}
        url = "{}{}" . format(self.auth_url, '/api/session')

        result = requests.post(url, data=json.dumps(credentials), headers=self.headers, verify=False)
        print result
        if result.status_code == 200:
            json_result = result.json()
            self.headers['X-API-Session'] = self.api_session = json_result['api-session']

    def get(self, command_url):
        url = "{}{}" . format(self.auth_url, command_url)
        result = requests.get(url, headers=self.headers, verify=False)
        if result.status_code == 200:
           return result.json()
        else:
           return None

