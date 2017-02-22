#!/usr/bin/python3

"""
Basic HTTP server to receive GitLab webhooks and update a repository
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import subprocess
import smtplib
from email.mime.text import MIMEText

LOCAL_DIR = '/var/nice_repo'
SECRET_TOKEN = 'FILLME'
IP_ADDRESS = ''
LISTEN_PORT = 8000
SEND_MAIL = True
MAIL_SENDER = 'test@example.com'
MAIL_RECIPIENT = 'test@example.com'
SMTP_HOST = 'localhost'
MAIL_PREFIX = '[ProjectA] '



class RequestHandler(BaseHTTPRequestHandler):
    def mail_report(self, out):
        content = "Executing git pull --ff-only\n\n"\
                + str(out)
        msg = MIMEText(content)
        msg['Subject'] = MAIL_PREFIX + "New push event received from GitLab"
        msg['From'] = MAIL_SENDER
        msg['To'] = MAIL_RECIPIENT
        s = smtplib.SMTP(SMTP_HOST)
        s.send_message(msg)
        s.quit()

    def answer_ok(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(bytes("<html><body><h1>200 OK</h1></body></html>","utf-8"))

    def answer_bad_request(self):
        self.send_response(400)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(bytes("<html><body><h1>400 Bad Request</h1></body></html>","utf-8"))

    def event_push(self, data):
        args = ['git','pull','--ff-only']
        proc = subprocess.Popen(args, cwd=LOCAL_DIR, stdout=subprocess.PIPE)
        if SEND_MAIL:
            print("Sending mail to %s" % MAIL_RECIPIENT)
            self.mail_report(proc.stdout.read())

    def do_POST(self):
        if not all (k in self.headers for k in ('Content-Length', 'X-Gitlab-Event', 'X-Gitlab-Token')):
            self.answer_bad_request()
        elif self.headers['X-Gitlab-Token'] == SECRET_TOKEN and not SECRET_TOKEN == '':
            length = int(self.headers['Content-Length'])
            payload = self.rfile.read(length).decode('utf-8')
            data = json.loads(payload)

            if data['object_kind'] == 'push':
                self.event_push(data)
            else:
                self.answer_bad_request()
                return

            self.answer_ok()
        else:
            self.answer_bad_request()



def run():
    httpd = HTTPServer((IP_ADDRESS, LISTEN_PORT), RequestHandler)
    httpd.serve_forever()

run()
