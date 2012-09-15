#!/usr/bin/python
import sys
import socket
import datetime

host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
port = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
toaddr = sys.argv[3] if len(sys.argv) > 3 else "nobody@example.com"
fromaddr = sys.argv[4] if len(sys.argv) > 4 else "nobody@example.com"

def sendmsg(msgid, hostname, portnum, sender, receiver):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((hostname, portnum))

    print s.send("HELO %s\r\n" % socket.gethostname())
    print s.recv(500)

    s.send("MAIL FROM: %s\r\n" % sender)
    print s.recv(500)

    s.send("RCPT TO: %s\r\n" % receiver)
    print s.recv(500)

    s.send("DATA\r\nFrom: %s\r\nTo: %s\r\nDate: %s -0500\r\nSubject: msg %d\r\n\r\nContents of message %d end here.\r\n.\r\n" % (sender, receiver, datetime.datetime.now().ctime(), msgid, msgid))
    print s.recv(500)

for i in range(1, 10):
    sendmsg(i, host, port, fromaddr, toaddr)
