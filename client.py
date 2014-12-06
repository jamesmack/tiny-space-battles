import sys
from time import sleep
from PodSixNet.Connection import connection, ConnectionListener
from tinySpaceBattles import TinySpaceBattles


class Client(ConnectionListener, TinySpaceBattles):
    """
    The main client class.
    """
    def __init__(self, host, port):
        """
        Initialize client: connect to server and init base game class.
        :str host: Server IP
        :int port: Server port
        :return: None
        """
        self.Connect((host, port))
        self.ready = False
        TinySpaceBattles.__init__(self)

    def loop(self):
        """
        Main game loop for client.
        :return: None
        """
        self.Pump()
        connection.Pump()
        self.events()
        self.check_for_wiimote_move()
        self.draw()

        if "Connecting" in self.statusLabel:
            self.statusLabel = "Connecting" + ("." * ((self.frame / 30) % 4))

    def send_action(self, action):
        """
        Send player data to server.
        :str action: A string containing the action to perform.
        :return: None
        """
        if self.is_p1 is None:
            return
        if self.is_p1:
            player = self.p1
        else:
            player = self.p2
        loc = player.rect_xy
        loc.append(player.angle)

        # Send to server
        connection.Send({"action": action, "p": self.which_player(), "p_pos": loc})

    #######################
    ### Event callbacks ###
    #######################

    def player_move(self, direction, x_mag=1, y_mag=1):
        """
        Moves the player.
        :param direction: Up, down, left, right
        :param x_mag: Magnitude of x (between 0 and 1 for Nunchuck joystick) for joystick sensitivity
        :param y_mag: Magnitude of y (between 0 and 1 for Nunchuck joystick) for joystick sensitivity
        :return: None
        """
        if self.is_p1 is None:
            return
        if self.is_p1:
            player = self.p1
        else:
            player = self.p2

        loc = player.rect_xy

        if 'l' in direction:
            loc[0] -= 8*x_mag
        if 'r' in direction:
            loc[0] += 8*x_mag
        if 'u' in direction:
            loc[1] -= 8*y_mag
        if 'd' in direction:
            loc[1] += 8*y_mag

        if 'ccw' in direction:
            loc.append((player.angle + 5) % 360)
        elif 'cw' in direction:
            loc.append((player.angle - 5) % 360)
        else:
            loc.append(player.angle)

        # Push to player position list and notify server
        player.update(loc, True)
        player.position_hist.append(loc)
        self.send_action('move')

    def player_restart(self):
        """
        Called when restart is requested
        :return: None
        """
        self.send_action('restart')

    def player_fire(self):
        """
        Called when player fires
        :return: None
        """
        if self.ready:
            self.send_action('fire')

    def player_shield(self):
        """
        Called when player activates shield
        :return: None
        """
        if self.ready:
            self.send_action('shield')

    ###############################
    ### Network event callbacks ###
    ###############################

    def Network_init(self, data):
        """
        Called when network init data is received by PodSixNet. Performs client setup.
        :dict data: Network data from server
        :return: None
        """
        if data["p"] == 'p1':
            self.is_p1 = True
            print("No other players currently connected. You are P1.")
            # Send position to server
            self.send_action('move')
        elif data["p"] == 'p2':
            self.is_p1 = False
            print('You are P2. The game will start momentarily.')
            # Send position to server
            self.send_action('move')
        elif data["p"] == 'full':
            print('Server is full. You have been placed in a waiting queue.')
            self.playersLabel = "Waiting for free slot in server"
        else:
            sys.stderr.write("ERROR: Couldn't determine player from server.\n")
            sys.stderr.write(str(data) + "\n")
            sys.stderr.flush()
            sys.exit(1)

    def Network_ready(self, data):
        """
        Called when network ready data is received. This is on game restart or when P2 joins.
        :dict data: Network data from server
        :return: None
        """
        self.playersLabel = "You are " + self.which_player().capitalize() + ". Battle!"
        self.ready = True

    def Network_player_left(self, data):
        """
        Called when player has left the server.
        :dict data: Network data from server
        :return: None
        """
        self.playersLabel = "Other player left server"
        self.ready = False

    def Network_move(self, data):
        """
        Called when player location date is received.
        :dict data: Network data from server
        :return: None
        """
        position = data['p_pos']
        player = data['p']
        if player == 'p1' and not self.is_p1:
            self.p1.update(position)
        elif player == 'p2' and self.is_p1:
            self.p2.update(position)
        elif player in ('p1', 'p2'):  # This is client's position coming back from player
            pass  # TODO: Anti-cheat detection here
        else:
            sys.stderr.write("ERROR: Couldn't update player movement information.\n")
            sys.stderr.write(str(data) + "\n")
            sys.stderr.flush()
            sys.exit(1)

    def Network_bullets(self, data):
        """
        Called when bulled data is received from server.
        :dict data: Network data from server
        :return: None
        """
        self.update_bullets(data['bullets'])
        self.p1.health = data['p1_health']
        self.p2.health = data['p2_health']

    def Network_death(self, data):
        """
        Called when player death is received from server.
        :dict data: Network data from server
        :return: None
        """
        self.win_or_lose(data['p'])
        self.ready = False

    def Network_restart(self, data):
        """
        Called when restart is received from server.
        :dict data: Network data from server
        :return: None
        """
        # Reset position and send to server
        if self.is_p1:
            self.p1.rand_pos(True)
        else:
            self.p2.rand_pos(False)
        self.send_action('move')

        # Clear game over flag
        self.game_over = False
        self.ready = True


    def Network(self, data):
        """
        Generic network data callback.
        :dict data: Network data from server
        :return: None
        """
        # print 'network:', data
        pass

    ########################################
    ### Built-in network event callbacks ###
    ########################################

    def Network_connected(self, data):
        """
        Called when player connects to server.
        :dict data: Network data from server
        :return: None
        """
        self.statusLabel = "Connected"

    def Network_error(self, data):
        """
        Called when there's a connection error when connecting to server.
        :dict data: Network data from server
        :return: None
        """
        self.ready = False
        print data
        import traceback
        traceback.print_exc()
        self.statusLabel = data['error'][1]
        connection.Close()

    def Network_disconnected(self, data):
        """
        Called when player is disconnected from server.
        :dict data: Network data from server
        :return: None
        """
        self.statusLabel = "Disconnected"
        self.playersLabel = "No other players"
        self.ready = False

if len(sys.argv) != 2:
    print "Usage:", sys.argv[0], "host:port"
    print "e.g.", sys.argv[0], "localhost:31425"
else:
    host, port = sys.argv[1].split(":")
    c = Client(host, int(port))
    while 1:
        c.loop()
        sleep(0.001)
