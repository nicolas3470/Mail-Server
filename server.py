#!/usr/bin/python

import getopt
import socket
import sys
from threading import Lock, Thread, Timer, Condition
import shutil

# STOP!  Don't change this.  If you do, we will not be able to contact your
# server when grading.  Instead, you should provide command-line arguments to
# this program to select the IP and port on which you want to listen.  See below
# for more details.
host="127.0.0.1"
port=8765

# handle a single client request
class ConnectionHandler:
    def __init__(self, socket,file,monitor):
        self.socket = socket
        self.step = "HELO"
        self.client_hostname = ""
        self.id = 0
        self.mail_from = ""
        self.rcpt_to = []
        self.data = ""
        self.filename = file
        self.mailbox_monitor = monitor
 #       self.timeout = Timer(11.0,self.connection_timeout)
        self.done = False
        self.socket.settimeout(10.0)

    def handle(self):
        try:
            self.socket.send("220 nm338 SMTP CS4410MP3\n")
 #           self.timeout.start()
            self.helo_handler()
            while not self.done:
                self.mail_from_handler()
                self.rcpt_to_handler()
                self.data_handler()
                self.store_mail()
        except socket.timeout:
 #           self.timeout.cancel()
            self.socket.send("421 4.4.2 nm338 Error: timeout exceeded\n")
            self.socket.close()
            return
        except socket.error:
            return


    # waits for message to be complete before collecting it
    def collect_input(self):
        whole_msg = self.socket.recv(500)
        while whole_msg[len(whole_msg)-2:] != '\r\n':
            whole_msg = whole_msg + self.socket.recv(500)
        return whole_msg

    # returns True if two strings are identical (caps not sensitive)
    def str_equals(self,str1, str2):
        if str1.capitalize() == str2.capitalize():
            return True
        else:
            return False

    # returns the next message as a list of words with special cases for "mail to:" and "rcpt to:" commands
    def next_msg(self):
        msg = self.collect_input()
        msg_words = msg.split()
        email = ""
        if len(msg_words) >=2 and self.str_equals(msg_words[0],"MAIL") and self.str_equals(msg_words[1],"FROM:"):
            msg_words = msg_words[2:]
            msg_words.insert(0,"MAIL FROM:")
            email = msg.partition(":")[2][:-2]
        elif len(msg_words) >=2 and self.str_equals(msg_words[0],"RCPT") and self.str_equals(msg_words[1],"TO:"):
            msg_words = msg_words[2:]
            msg_words.insert(0,"RCPT TO:")
            email = msg.partition(":")[2][:-2]
        elif len(msg_words) >=2 and self.str_equals(msg_words[0],"RCPT") and self.str_equals(msg_words[1][:3],"TO:"):
            msg_words = msg_words[2:]
            msg_words.insert(0,"RCPT TO:")
            email = msg.partition(":")[2][:-2]
            msg_words.insert(1,email)
        elif len(msg_words) >=2 and self.str_equals(msg_words[0],"MAIL") and self.str_equals(msg_words[1][:5],"FROM:"):
            msg_words = msg_words[2:]
            msg_words.insert(0,"MAIL FROM:")
            email = msg.partition(":")[2][:-2]
            msg_words.insert(1,email)
        return (msg_words,email)

    # returns an error message due to command errors, and an empty string if there is no error
    def command_checker(self,msg_words):
        error = ""
        if len(msg_words) != 0:
            if not (self.str_equals(msg_words[0],"HELO") or self.str_equals(msg_words[0],"MAIL FROM:")
                    or self.str_equals(msg_words[0],"RCPT TO:") or self.str_equals(msg_words[0],"DATA")):
                error = "502 5.5.2 Error: command not recognized\n"
            elif self.step == "RCPT TO" and self.str_equals(msg_words[0],"MAIL FROM:"):
                error = "503 5.5.1 Error: nested MAIL command\n"
            elif self.step == "DATA" and self.str_equals(msg_words[0],"RCPT TO:"):
                # special multiple recipient exception, no error
                error = ""
            elif not self.str_equals(msg_words[0],self.step):
                error = "503 Error: need " + self.step + " command\n"
        else:
            error = "500 Error: bad syntax\n"
        return error

    # handles helo commands
    def helo_handler(self):
        while (not self.done) and self.step == "HELO":
            msg = self.next_msg()[0]
            helo_response = self.command_checker(msg)
            if helo_response == "":
                if len(msg) != 2:
                    helo_response = "501 Syntax: HELO yourhostname\n"
                else:
 #                   self.timeout.cancel()
                    helo_response = "250 nm338\n"
                    self.client_hostname = msg[1]
                    self.step = "MAIL FROM:"
 #                   self.timeout = Timer(10.0,self.connection_timeout)
 #                   self.timeout.start()
            self.socket.send(helo_response)

    # handles mail from commands
    def mail_from_handler(self):
        while (not self.done) and self.step == "MAIL FROM:":
            mail_msg = self.next_msg()
            msg = mail_msg[0]
            mail_response = self.command_checker(msg)
            if mail_response == "":
                if len(msg) == 3:
                    mail_response = "504 5.5.2 <" + mail_msg[1] + ">: Sender address rejected\n"
                elif len(msg) != 2:
                    mail_response = "501 Syntax: MAIL FROM: <address>\n"
                else:
 #                   self.timeout.cancel()
                    mail_response = "250 2.1.0 Ok\n"
                    self.mail_from = msg[1]
                    self.step = "RCPT TO:"
 #                   self.timeout = Timer(10.0,self.connection_timeout)
 #                   self.timeout.start()
            self.socket.send(mail_response)

    # handles rcpt to commands and also deals with the DATA keyword handling stage
    def rcpt_to_handler(self):
        while (not self.done) and (self.step == "RCPT TO:" or self.step == "DATA"):
            mail_msg = self.next_msg()
            msg = mail_msg[0]
            response = self.command_checker(msg)
            if response == "":
                if msg[0] == "RCPT TO:":
                    if len(msg) == 3:
                        response = "504 5.5.2 <" + mail_msg[1] + ">: Recipient address invalid\n"
                    elif len(msg) !=2:
                        response = "501 Syntax: RCPT TO: <address>\n"
                    else:
 #                       self.timeout.cancel()
                        response = "250 2.1.5 Ok\n"
                        self.rcpt_to.append(mail_msg[1])
                        self.step = "DATA"
 #                       self.timeout = Timer(10.0,self.connection_timeout)
 #                       self.timeout.start()
                else:
                    if len(msg) != 1:
                        response = "501 Syntax: DATA\n"
                    else:
 #                       self.timeout.cancel()
                        response = "354 End data with <CR><LR>.<CR><LF>\n"
                        self.step = "FINISH"
 #                       self.timeout = Timer(10.0,self.connection_timeout)
 #                       self.timeout.start()
            self.socket.send(response)

    # handles data input
    def data_handler(self):
        if not self.done:
            data = self.collect_input()
 #           self.timeout.cancel()
 #           self.timeout = Timer(10.0,self.connection_timeout)
 #           self.timeout.start()
            self.data = data
            while self.step == "FINISH":
                if self.collect_input() == ".\r\n":
 #                   self.timeout.cancel()
                    with self.mailbox_monitor.mailbox_lock:
                        self.id = self.mailbox_monitor.mail_id
                        self.mailbox_monitor.mail_id += 1
                    self.socket.send("250 OK: delivered message %d\n" % self.id)
                    self.step = "MAIL FROM:"

    # adds the complete message for this connection to a file
    def store_mail(self):
        if not self.done:
            with self.mailbox_monitor.mailbox_lock:
                file = open(self.filename,'a')
                file.write("Received: from ")
                file.write(self.client_hostname)
                file.write(" by nm338 (CS4410MP3)\nNumber: ")
                file.write(str(self.id))
                file.write("\nFrom: ")
                file.write(self.mail_from)
                for x in self.rcpt_to:
                    file.write("\nTo: ")
                    file.write(x)
                file.write("\n\n")
                file.write(self.data)
                file.write("\n")
            del self.rcpt_to[:]
 #           self.timeout = Timer(10.0,self.connection_timeout)
 #           self.timeout.start()

    # closes the connection to the socket upon timeout
    def connection_timeout(self):
        self.socket.send("421 4.4.2 nm338 Error: timeout exceeded\n")
        self.socket.close()
        self.done = True

# the main server loop
def serverloop():
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # mark the socket so we can rebind quickly to this port number 
    # after the socket is closed
    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # bind the socket to the local loopback IP address and special port
    serversocket.bind((host, port))
    # start listening with a backlog of 5 connections
    serversocket.listen(5)

    # open and flush mailbox file
    filename = "mailbox.txt"
    file = open(filename,'w')
    file.close()

    # create mailbox monitor and consumer monitors
    monitor_mailbox = Mailbox_monitor()
    monitor_consumer = Consumer_monitor()

    # create mailbox backup thread
    mailbox_backup = Backup_Mailbox(monitor_mailbox)
    mailbox_backup.start()

    # create thread pool of 32 threads
    for i in range(1,33):
        new_thread = Thread_pool_consumer(monitor_consumer,monitor_mailbox)
        new_thread.start()

    while True:
        try:
            # Producer thread
            # accept a connection
            (clientsocket, address) = serversocket.accept()
            ct = ConnectionHandler(clientsocket,filename,monitor_mailbox)
            with monitor_consumer.monitor_lock:
                monitor_consumer.handler_list.append(ct)
                monitor_consumer.no_connections.notify()
        except KeyboardInterrupt:
            exit()

# thread pool acting as consumer of connections
class Thread_pool_consumer(Thread):
    def __init__(self,monitor,mail_monitor):
        Thread.__init__(self)
        self.monitor = monitor
        self.mail_monitor = mail_monitor

    def run(self):
        while True:
            self.monitor.consumer_ready()
            self.mail_monitor.consumer_done()

# monitor for synchronizing file output
class Mailbox_monitor:
    def __init__(self):
        self.mailbox_lock = Lock()
        self.mail_id = 1
        self.need_backup = Condition(self.mailbox_lock)
        self.num_backups = 0

    def consumer_done(self):
        with self.mailbox_lock:
            if self.mail_id - self.num_backups > 32:
                self.need_backup.notify()

    def backup_ready(self):
        with self.mailbox_lock:
            while self.mail_id - self.num_backups <= 32:
                self.need_backup.wait()
            new_filename = "mailbox." + str(self.num_backups+1) + "-" + str(self.num_backups+32) + ".txt"
            shutil.copy("mailbox.txt",new_filename)
            file = open("mailbox.txt",'w')
            file.close()
            self.num_backups += 32
            

# monitor for synchronizing multi-threaded connections
class Consumer_monitor:
    def __init__(self):
        self.monitor_lock = Lock()
        self.handler_list = []
        self.no_connections = Condition(self.monitor_lock)

    # consumer waits for a connection to be available, then handles it
    def consumer_ready(self):
        with self.monitor_lock:
            while len(self.handler_list) == 0:
                self.no_connections.wait()
            next_to_handle = self.handler_list[0]
            del self.handler_list[0]
        next_to_handle.handle()

# backs up the mailbox
class Backup_Mailbox(Thread):
    def __init__(self,mail_monitor):
        Thread.__init__(self)
        self.mail_monitor = mail_monitor

    def run(self):
        while True:
            self.mail_monitor.backup_ready()

# You don't have to change below this line.  You can pass command-line arguments
# -h/--host [IP] -p/--port [PORT] to put your server on a different IP/port.
opts, args = getopt.getopt(sys.argv[1:], 'h:p:', ['host=', 'port='])

for k, v in opts:
    if k in ('-h', '--host'):
        host = v
    if k in ('-p', '--port'):
        port = int(v)

print ("Server coming up on %s:%i" % (host, port))
serverloop()
