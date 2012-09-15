#!/usr/bin/python

import socket
import random
from threading import Thread, Lock

# This is the multi-threaded client.  This program should be able to run
# with no arguments and should connect to "127.0.0.1" on port 8765.  It
# should run a total of 1000 operations, and be extremely likely to
# encounter all error conditions described in the README.

def main():
    num_clients = 31
    ops_lock = Operations_lock()
    for i in range(1,num_clients+1):
        new_client = Client(i,ops_lock)
        new_client.start()

# A client that performs stress tests on the server
class Client(Thread):
    def __init__(self,id_num,ops_lock):
        Thread.__init__(self)
        self.id = id_num
        self.ops_lock = ops_lock
        self.step = "HELO"
        self.done = False

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1",8765))
        while not self.done:
            self.stress_test(s)

    def stress_test(self,s):
        with self.ops_lock.lock:
            if self.ops_lock.num_ops < 1000:
                random_int = random.randint(1,100)
                if self.step == "HELO":
                    if random_int <= 65:
                        s.send("HELO " + str(self.id) + "\r\n")
                        if s.recv(500) != "250 nm338\n":
                            print("ERROR!")
                        self.step = "MAIL FROM:"
                    elif 65 < random_int < 75:
                        s.send("HELO this msg is too long")
                        if s.recv(500) != "501 Syntax: HELO yourhostname\n":
                            print("ERROR!")
                    elif 75 < random_int < 85:
                        s.send("mkdir fakecommand")
                        if s.recv(500) != "502 5.5.2 Error: command not recognized\n":
                            print("ERROR!")
                    elif 85 < random_int < 95:
                        s.send("mail from:me")
                        if s.recv(500) != "503 Error: need " + self.step + " command\n":
                            print("ERROR!")
                    else:
                        s.send("")
                        if s.recv(500) != "500 Error: bad syntax\n":
                            print("ERROR!")
                elif self.step == "MAIL FROM:":
                    print("here")
                    if random_int <= 65:
                        s.send("MAIL FROM: nm338@cornell.edu\r\n")
                        if s.recv(500) != "250 2.1.0 Ok\n":
                            print("ERROR!")
                        self.step = "RCPT TO:"
                    elif 65 < random_int < 75:
                        s.send("MAIL FROM: nm338 @cornell.edu\r\n")
                        if s.recv(500) != "504 5.5.2 <nm338 @cornell.edu>: Sender address rejected\n":
                            print("ERROR!")
                    elif 75 < random_int < 85:
                        s.send("MAIL FROM: this is my email\r\n")
                        if s.recv(500) != "501 Syntax: MAIL FROM: <address>\n":
                            print("ERROR!")
                    elif 85 < random_int < 90:
                        s.send("what other_fake_command?")
                        if s.recv(500) != "502 5.5.2 Error: command not recognized\n":
                            print("ERROR!")
                    elif 90 < random_int < 95:
                        s.send("helo world")
                        if s.recv(500) != "503 Error: need " + self.step + " command\n":
                            print("ERROR!")
                    else:
                        s.send("")
                        if s.recv(500) != "500 Error: bad syntax\n":
                            print("ERROR!")
                elif self.step == "RCPT TO:":
                    if random_int <= 65:
                        s.send("RCPT TO: 4410@cornell.edu\r\n")
                        if s.recv(500) != "250 2.1.5 Ok\n":
                            print("ERROR!")
                        self.step = "DATA:"
                    elif 65 < random_int < 75:
                        s.send("RCPT TO: nm338 @cornell.edu\r\n")
                        if s.recv(500) != "504 5.5.2 <nm338 @cornell.edu>:  Recipient address invalid\n":
                            print("ERROR!")
                    elif 75 < random_int < 80:
                        s.send("RCPT TO:\r\n")
                        if s.recv(500) != "501 Syntax: RCPT TO: <address>\n":
                            print("ERROR!")
                    elif 80 < random_int < 85:
                        s.send("MAIL FROM: nm338@cornell.edu\r\n")
                        if s.recv(500) != "503 5.5.1 Error: nested MAIL command\n":
                            print("ERROR!")
                    elif 85 < random_int < 90:
                        s.send("MAIL")
                        if s.recv(500) != "502 5.5.2 Error: command not recognized\n":
                            print("ERROR!")
                    elif 90 < random_int < 95:
                        s.send("DATA")
                        if s.recv(500) != "503 Error: need " + self.step + " command\n":
                            print("ERROR!")
                    else:
                        s.send("")
                        if s.recv(500) != "500 Error: bad syntax\n":
                            print("ERROR!")
                elif self.step == "DATA:":
                    if random_int <= 65:
                        s.send("DATA\r\n")
                        if s.recv(500) != "354 End data with <CR><LR>.<CR><LF>\n":
                            print("ERROR!")
                        self.step = "DATA2:"
                    elif 65 < random_int < 75:
                        s.send("RCPT TO: nm338@cornell.edu\r\n")
                        if s.recv(500) != "250 2.1.5 Ok\n":
                            print("ERROR!")
                    elif 75 < random_int < 80:
                        s.send("RCPT TO:\r\n")
                        if s.recv(500) != "501 Syntax: RCPT TO: <address>\n":
                            print("ERROR!")
                    elif 80 < random_int < 85:
                        s.send("DaTa syntax\r\n")
                        if s.recv(500) != "501 Syntax: DATA\n":
                            print("ERROR!")
                    elif 85 < random_int < 90:
                        s.send("another bad command")
                        if s.recv(500) != "502 5.5.2 Error: command not recognized\n":
                            print("ERROR!")
                    elif 90 < random_int < 95:
                        s.send("Mail To: myname")
                        if s.recv(500) != "503 Error: need " + self.step + " command\n":
                            print("ERROR!")
                    else:
                        s.send("")
                        if s.recv(500) != "500 Error: bad syntax\n":
                            print("ERROR!")
                elif self.step == "DATA2:":
                    s.send("msg\r\n")
                    if random_int <= 85:
                        s.send(".\r\n")
                        if s.recv(500)[:25] != "250 OK: delivered message":
                            print("Error!")
                            self.step = "MAIL FROM:"
                    else:
                        s.send("not a comma\r\n")
                else:
                    print("else")
                self.ops_lock.num_ops += 1
            else:
                self.done = True
        
        
class Operations_lock:
    def __init__(self):
        self.lock = Lock()
        self.num_ops = 0
    
if __name__ == "__main__":
    main()
