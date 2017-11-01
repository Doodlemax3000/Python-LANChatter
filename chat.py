import sys
import socket
import threading


# ------------------------------------------ SERVER CLASS ----------------------------------------------


class ChatServer:
    # declare variables
    CONNECTIONS = {}  # key is socket obj & value is username
    SERVER_SOCKET = socket.socket()
    RECV_BUFFER = 4096
    PORT = 0

    KICK_LIST = []  # temp list for users gotten kicked
    BAN_LIST = []  # self explanatory

    # -- constructor
    def __init__(self, port, banner):
        # welcome banner
        print(banner)

        self.PORT = port
        # init server_socket
        self.SERVER_SOCKET.bind(('0.0.0.0', self.PORT))
        self.CONNECTIONS[self.SERVER_SOCKET] = 'SERVER'  # add SERVER_SOCKET to list of active connections
        # log: initiated server
        print('Server initiated on port: ', str(self.PORT))

    # -- method to handle connections
    def handler(self, conn, username):  # username in case of /kick (user removed from list -> error in broadcast)
        while True:
            try:
                data = conn.recv(self.RECV_BUFFER)
                self.broadcast(conn, '[' + self.CONNECTIONS[conn] + '] ' + data.decode('utf-8'))
                if not data:
                    break
            except:
                # host disconnected
                # remove socket from CONNECTIONS
                if conn in self.CONNECTIONS:
                    del self.CONNECTIONS[conn]
                # check if only kicked or actually disconnected
                if username in self.KICK_LIST or username in self.BAN_LIST:
                    # if kicked remove from tmp list
                    if username in self.KICK_LIST:
                        self.KICK_LIST.remove(username)
                    # not send anything
                else:
                    # inform clients that a client disconnected
                    self.broadcast(self.SERVER_SOCKET, '[SERVER] ' + username + ' disconnected from server')
                break

    # -- input handling method
    def input_handler(self):
        while True:
            # wait for user input
            user_input = input('')
            # check input
            if user_input == '/exit':  # command to close the server
                print('Shutting down server')
                for conn in self.CONNECTIONS:
                    conn.close()
                sys.exit()
            elif '/kick' in user_input:  # command to kick a user
                command = user_input.split(' ')
                if len(command) >= 2:
                    usertokick = command[1]
                    if usertokick in self.CONNECTIONS.values():  # if user exists
                        # find out the user's address & remove that connection
                        for conn, user in self.CONNECTIONS.items():
                            if user == usertokick:
                                # kick/close socket
                                conn.send('You were kicked from the server'.encode('utf-8'))
                                conn.close()
                                # add to recently-kicked-users list
                                self.KICK_LIST.append(usertokick)
                                # remove from active connections
                                del self.CONNECTIONS[conn]
                                break
                        # inform clients that a client was kicked
                        self.broadcast(self.SERVER_SOCKET, '[SERVER] ' + usertokick + ' was kicked from server')
                    else:
                        print('User: ' + usertokick + ' does not exist!')
            elif '/ban' in user_input:  # command to ban a user
                command = user_input.split(' ')
                if len(command) >= 2:
                    usertoban = command[1]
                    if usertoban in self.CONNECTIONS.values():  # if user exists
                        # check if already banned
                        if usertoban in self.BAN_LIST:
                            print('User: ' + usertoban + ' is already banned!')
                        else:
                            # find out the user's address & remove that connection
                            for conn, user in self.CONNECTIONS.items():
                                if user == usertoban:
                                    # ban/close socket
                                    conn.send('You were banned from the server'.encode('utf-8'))
                                    conn.close()
                                    # add to banned list
                                    self.BAN_LIST.append(usertoban)
                                    # remove from active connections
                                    del self.CONNECTIONS[conn]
                                    break
                            # inform clients that a client was kicked
                            self.broadcast(self.SERVER_SOCKET, '[SERVER] ' + usertoban + ' was banned from server')

                    else:
                        print('User: ' + usertoban + ' does not exist!')

    # -- method to broadcast to all but the sender
    def broadcast(self, sender, msg):
        for conn in self.CONNECTIONS.keys():
            if conn != self.SERVER_SOCKET and conn != sender:
                # if not sender: try to send data
                conn.send(msg.encode('utf-8'))
        print('[CHAT]: ' + msg)

    # -- method to run server
    def run(self):
        self.SERVER_SOCKET.listen(10)  # start listening
        # log: running server
        print('Server now running on port: ', str(self.PORT))

        # start thread for input handling
        i_thread = threading.Thread(target=self.input_handler, daemon=True)
        i_thread.start()

        # check if new connections are requested
        while True:
            conn, addr = self.SERVER_SOCKET.accept()

            # client requests username: decide weather good or not
            username = conn.recv(1024)  # receive username
            username = username.decode('utf-8')
            taken = False
            # check if username e.g. [SERVER]
            if username.lower() in '[server]':
                taken = True
                conn.send('taken'.encode('utf-8'))  # send back 'taken'
                conn.close()  # close connection
            if not taken:
                # check if contains braces
                for c in ['(', ')', '[', ']', '{', '}', '/', '\\']:
                    if c in username:
                        taken = True
                        conn.send('taken'.encode('utf-8'))  # send back 'taken'
                        conn.close()  # close connection
                        break
            if not taken:
                # check if username is already taken
                for name in self.CONNECTIONS.values():
                    if name == username:  # see if username is already taken
                        taken = True
                        conn.send('taken'.encode('utf-8'))  # send back 'taken'
                        conn.close()  # close connection
                        break
            if not taken:
                # check if username is banned
                if username in self.BAN_LIST:
                    taken = True
                    conn.send('taken'.encode('utf-8'))  # send back 'taken'
                    conn.close()  # close connection
            if not taken:  # passed all checks
                conn.send('not-taken'.encode('utf-8'))  # send back 'not-taken'
                # add to nickname database & add to list of active connections
                self.CONNECTIONS[conn] = username

                # create new handling-thread for connection
                # it shall target the handler & be a daemon (die if parent dies)
                c_thread = threading.Thread(target=self.handler, args=(conn, username), daemon=True)
                c_thread.start()
                # inform client of the connect
                self.broadcast(self.SERVER_SOCKET, '[SERVER] ' + self.CONNECTIONS[conn] + ' connected to server')


# ------------------------------------------ CLIENT CLASS ----------------------------------------------------------
class ChatClient:
    # declare variables
    CLIENT_SOCKET = socket.socket()
    RECV_BUFFER = 4096
    USERNAME = ''

    # -- constructor
    def __init__(self, hostname, port, username, banner):
        # welcome banner
        print(banner)

        # try to connect to server
        try:
            print('Trying to connect to ' + str(hostname) + ' on port ' + str(port))
            self.CLIENT_SOCKET.connect((hostname, port))
        except:
            # no connection
            print('Could not connect to server')
            sys.exit()

        # see if username available
        self.CLIENT_SOCKET.send(username.encode('utf-8'))
        response = self.CLIENT_SOCKET.recv(1024)
        if response.decode('utf-8') == 'taken':
            print('Username not available')
            sys.exit()

        # username good -> continue with execution
        self.USERNAME = username
        # connection was successful:
        print('Connection successful')

        # create thread for input
        input_thread = threading.Thread(target=self.input_handler, daemon=True)
        input_thread.start()

        # start receiving routine
        while True:
            # try to receive data from server
            data = self.CLIENT_SOCKET.recv(self.RECV_BUFFER)
            if data:  # received data
                # print data
                print(data.decode('utf-8'))

    # -- input handling method
    def input_handler(self):
        while True:
            # wait for user input -> send to server
            user_input = input('[' + self.USERNAME + '] ')

            # check input
            if user_input == '/exit':  # if the user wants to close the program
                self.CLIENT_SOCKET.close()
                sys.exit()
            elif user_input != '':
                # if not empty try to send
                try:
                    self.CLIENT_SOCKET.send(user_input.encode('utf-8'))
                except:
                    pass


# ---------------------------------------------- ENTRY POINT ----------------------------------------------
# declare welcome banner
banner = "_____-----========== Python LAN-Chatter ==========-----_____\n" \
         "_____===================== V 1.2 ======================_____\n" \
         "     -----======== by Maximilian Rukavina ========-----     \n"

# given enough arguments?
if len(sys.argv) > 1:  # more than the standard argument?
    if str(sys.argv[1]) == 'server' and len(sys.argv) == 3:  # server & 3 argument in total?
        # try to run server
        try:
            server = ChatServer(int(sys.argv[2]), banner)
            server.run()
        except:
            print('SERVER CRASHED')
            sys.exit()
    elif str(sys.argv[1]) == 'client' and len(sys.argv) == 5:  # if client & 4 arguments in total?
        # try to create client
        try:
            client = ChatClient(str(sys.argv[2]), int(sys.argv[3]), str(sys.argv[4]), banner)
        except:
            print('CLIENT CRASHED')
            sys.exit()
# if no if was True:
print('usage: python chat_legacy.py server [port]\n' +
      '       python chat_legacy.py client [hostname] [port] [username]')
sys.exit()
