#!/usr/bin/env python
import sys
import time
import requests
import json
import re

sys.path.insert(0, '../python-sdc-client/')
from slackclient import SlackClient
from sdcclient import SdcClient

SYSDIG_URL = 'https://app-staging2.sysdigcloud.com'

###############################################################################
# Basic slack interface class
###############################################################################
class SlackWrapper(object):
    inputs = []

    def __init__(self, slack_client, slack_id):
        self.slack_client = slack_client
        self.slack_id = slack_id

        self.slack_users = {}
        for u in self.slack_client.server.users:
            self.slack_users[u.id] = u.name

    def say(self, channelid, text):
        message_json = {'type': 'message', 'channel': channelid, 'text': text}
        self.slack_client.server.send_to_websocket(message_json)

    def listen(self):
        self.inputs = []
        while True:
            try:
                rv = self.slack_client.rtm_read()
            except KeyboardInterrupt:
                sys.exit(0)
            except:
                rv = []


            for reply in rv:
                #print reply

                if 'channel' in reply:
                    if 'reply_to' in reply:
                        print '> ' + reply['text']
                    if 'type' in reply and reply['type'] == 'message':
                        # only accept direct messages
                        if reply['channel'][0] == 'D':
                            if not 'user' in reply:
                                continue

                            if reply['user'] != self.slack_id:
                                self.last_channel_id = reply['channel']

                                if not 'text' in reply:
                                    continue
                                
                                print '< (%s) %s' % (self.slack_users[reply['user']], reply['text'])
                                pass

                                txt = reply['text']

                                self.inputs.append(txt.strip(' \t\n\r?!.'))
            if len(self.inputs) != 0:
                return

###############################################################################
# Chat endpoint class
###############################################################################
class SlackBuddy(SlackWrapper):
    inputs = []

    def __init__(self, sdclient, slack_client, slack_id):
        self._sdclient = sdclient
        super(SlackBuddy, self).__init__(slack_client, slack_id)

    def print_help(self):
        self.say(self.last_channel_id, 'Basic syntax:')
        self.say(self.last_channel_id, 'Advanced syntax:')

    def run(self):
        while True:
            self.listen()

            #print self.inputs

            for i in self.inputs:
                if i == 'help':
                    self.print_help()
                else:
                    self._sdclient.post_event(i)
                    self.say(self.last_channel_id, 'event posted')


###############################################################################
# Entry point
###############################################################################
def init():
    if len(sys.argv) != 3:
        print 'usage: %s <sysdig-token> <slack-token>' % sys.argv[1]
        sys.exit(0)
    else:
        sdc_token = sys.argv[1]
        slack_token = sys.argv[2]

    #
    # Instantiate the SDC client and Retrieve the SDC user information to make sure we have a valid connection
    #
    sdclient = SdcClient(sdc_token, SYSDIG_URL)

    #
    # Make a connection to the slack API
    #
    sc = SlackClient(slack_token)
    sc.rtm_connect()

    slack_id = json.loads(sc.api_call('auth.test'))['user_id']

    #
    # Start talking!
    #
    dude = SlackBuddy(sdclient, sc, slack_id)
    dude.run()

init()
