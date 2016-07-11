import json
import sys
import os
import webbrowser
import SocketServer
import SimpleHTTPServer

from urlparse import urlparse, parse_qs
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from boxsdk import Client, OAuth2
from pathlib import Path

import logging
logging.basicConfig(format='%(levelname)s: %(message)s')
log = logging.getLogger(__file__)
log.setLevel(logging.INFO)

class BoxPassport(object):

    def __init__(self):

        script_dir = os.path.dirname(os.path.realpath(__file__))
        config_file = Path(script_dir, 'passport_config.json')

        # Read the configuration file
        with config_file.open() as f:
            cfg = json.load(f)

        self.client_id = cfg['client_id']
        self.client_secret = cfg['client_secret']
        self.address = cfg['redirect_address']
        self.port = cfg['redirect_port']
        self.token_file = self._get_token_path()

    def _get_token_path(self):
        if sys.platform == 'darwin':
            user_name = os.environ['USER']
            path = Path('/Users/%s/.boxpass/token.json' % user_name)
        elif sys.platform == 'win32':
            user_name = os.environ['USERNAME']
            path = Path('C:/Users/%s/AppData/Local/.boxpass/token.json' % user_name)
        else:
            log.error('Can not retrive token file path for the %s OS' % sys.platform)
            path = Path('./token.json')

        if not path.parent.exists():
            path.parent.mkdir()

        return path

    def _store_tokens(self, access_token, refresh_token):

        # TODO(Kirill): Store the tokens at secure storage (e.g. Keychain)
        # It should be stored per user!
        data = {'access_token': access_token, 'refresh_token': refresh_token}
        with open(str(self.token_file), 'w') as f:
            log.debug('Storing tokings to %s' % self.token_file)
            json.dump(data, f)

    def authenticate(self):

        # Firs of all check if token file already exists
        # If soo use its info to update our access token
        if self.token_file.exists():

            with self.token_file.open() as f:
                data = json.load(f)

            oauth = OAuth2(
                client_id=self.client_id,
                client_secret=self.client_secret,
                access_token=data['access_token'],
                refresh_token=data['refresh_token'],
                store_tokens=self._store_tokens
            )

            access_token, refresh_token = oauth.refresh(data['access_token'])

            return oauth

        ########################################################################
        # First time authentication
        ########################################################################
        oauth = OAuth2(
            client_id=self.client_id,
            client_secret=self.client_secret,
            store_tokens=self._store_tokens,
        )

        auth_url, csrf_token = oauth.get_authorization_url('%s:%s' % (self.address, self.port))

        class myHandler(BaseHTTPRequestHandler):

            # Handler for the GET requests
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type','text/html')
                self.end_headers()
                # Send the html message
                self.wfile.write("Redirecting back to client!")

                path = self.path # Full responce url

                if '?' in path:
                    path, tmp = path.split('?', 1)
                    qs = parse_qs(tmp)

                assert qs['state'][0] == csrf_token # Check against cross forgery requests

                # Now we have oauth code. We can ask for tokens
                access_token, refresh_token = oauth.authenticate(qs['code'][0])

                return

        # Propt user for access confirmation and login
        webbrowser.open_new_tab(auth_url)

        httpd = SocketServer.TCPServer(('', self.port), myHandler)

        print "Waiting for auth responce on %s port", self.port
        httpd.handle_request()

        return oauth

    def get_auth_client(self):
        oauth = self.authenticate()
        client = Client(oauth)

        return client

def main():
    p = BoxPassport()
    oauth = p.authenticate()

    # Test request
    client = Client(oauth)
    me = client.user(user_id='me').get()
    log.info('User login: %s' % me['login'])

# Module test
if __name__ == '__main__':
    main()
