import sys
from time import sleep
from PodSixNet.Connection import connection, ConnectionListener
from tinySpaceBattles import TinySpaceBattles


class Client(ConnectionListener, TinySpaceBattles):
    def __init__(self, host, port):
        self.Connect((host, port))
        self.player_loc = dict()
        self.ready = False
        TinySpaceBattles.__init__(self)

    def Loop(self):
        self.Pump()
        connection.Pump()
        self.Events()
        self.Check_for_wiimote_move()
        self.Draw()

        if "Connecting" in self.statusLabel:
            self.statusLabel = "Connecting" + ("." * ((self.frame / 30) % 4))

    def Send_action(self, action, loc_add=(0, 0), angle_add=0):
        if self.is_p1 is None:
            return
        if self.is_p1:
            player = self.p1
        else:
            player = self.p2
        loc = player.get_loc()
        if loc_add:
            loc = [x + y for x, y in zip(player.get_loc(), loc_add)]
        if angle_add:
            loc.append((angle_add + player.angle) % 360)
        else:
            loc.append(player.angle)

        # Push to player position list
        player.position_hist.append(loc)

        # Send to server
        connection.Send({"action": action, "p": self.Which_player(), "p_pos": loc})

    #######################
    ### Event callbacks ###
    #######################

    def Player_move(self, direction, x_mag=1, y_mag=1):
        add_pos = [0, 0]
        add_angle = 0
        if 'l' in direction:
            add_pos[0] -= 8*x_mag
        if 'r' in direction:
            add_pos[0] += 8*x_mag
        if 'u' in direction:
            add_pos[1] -= 8*y_mag
        if 'd' in direction:
            add_pos[1] += 8*y_mag
        if 'ccw' in direction:
            add_angle += 5
        elif 'cw' in direction:
            add_angle -= 5
        self.Send_action('move', add_pos, add_angle)

    def Player_fire(self):
        if self.ready:
            self.Send_action('fire')

    def Player_shield(self):
        if self.ready:
            self.Send_action('shield')

    ###############################
    ### Network event callbacks ###
    ###############################

    def Network_init(self, data):
        if data["p"] == 'p1':
            self.is_p1 = True
            print("No other players currently connected. You are P1.")
            # Send position to server
            self.Send_action('move')
        elif data["p"] == 'p2':
            self.is_p1 = False
            print('You are P2. The game will start momentarily.')
            # Send position to server
            self.Send_action('move')
        elif data["p"] == 'full':
            print('Server is full. You have been placed in a waiting queue.')
            self.playersLabel = "Waiting for free slot in server"
        else:
            sys.stderr.write("ERROR: Couldn't determine player from server.\n")
            sys.stderr.write(str(data) + "\n")
            sys.stderr.flush()
            sys.exit(1)

    def Network_ready(self, data):
        self.playersLabel = "You are " + self.Which_player().capitalize() + ". Battle!"
        self.ready = True

    def Network_player_left(self, data):
        self.playersLabel = "Other player left server"
        self.ready = False

    def Network_move(self, data):
        position = data['p_pos']
        player = data['p']
        if player == 'p1':
            self.p1.update(position)
        elif player == 'p2':
            self.p2.update(position)
        else:
            sys.stderr.write("ERROR: Couldn't update player movement information.\n")
            sys.stderr.write(str(data) + "\n")
            sys.stderr.flush()
            sys.exit(1)

    def Network_bullets(self, data):
        self.Update_bullets(data['bullets'])
        self.p1.health = data['p1_health']
        self.p2.health = data['p2_health']

    def Network_death(self, data):
        print(data)
        print("A player has died") # TODO: improve this...

    def Network(self, data):
        # print 'network:', data
        pass

    ########################################
    ### Built-in network event callbacks ###
    ########################################

    def Network_connected(self, data):
        self.statusLabel = "Connected"

    def Network_error(self, data):
        self.ready = False
        print data
        import traceback
        traceback.print_exc()
        self.statusLabel = data['error'][1]
        connection.Close()

    def Network_disconnected(self, data):
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
        c.Loop()
        sleep(0.001)
