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
        self.Check_for_button_held()
        self.Draw()

        if "Connecting" in self.statusLabel:
            self.statusLabel = "Connecting" + ("." * ((self.frame / 30) % 4))

    def Send_action(self, action, loc_add=None):
        if self.is_p1:
            loc = self.p1.get_loc()
            if loc_add is not None:
                loc = [x + y for x, y in zip(self.p1.get_loc(), loc_add)]
            connection.Send({"action": action, "pp_data": dict({'p1': loc, 'p2': None})})
        else:
            loc = self.p2.get_loc()
            if loc_add is not None:
                loc = [x + y for x, y in zip(self.p2.get_loc(), loc_add)]
            connection.Send({"action": action, "pp_data": dict({'p1': None, 'p2': loc})})

    #######################
    ### Event callbacks ###
    #######################

    def Player_move(self, direction):
        add_pos = [0, 0]
        if 'l' in direction:
            add_pos[0] -= 5
        elif 'r' in direction:
            add_pos[0] += 5
        elif 'u' in direction:
            add_pos[1] -= 5
        elif 'd' in direction:
            add_pos[1] += 5
        self.Send_action('move', add_pos)

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
        print(data)
        if data["p"] == 'p1':
            self.is_p1 = True
            print("No other players currently connected. You are P1.")
        elif data["p"] == 'p2':
            self.is_p1 = False
            print('You are P2. The game will start momentarily.')
        else:
            sys.stderr.write("ERROR: Couldn't determine player from server.\n")
            sys.stderr.flush()
            sys.exit(1)

        # Send position to server
        self.Send_action('move')

    def Network_ready(self, data):
        self.playersLabel = "Battle!"
        self.ready = True

    def Network_move(self, data):
        if data['pp_data']['p1'] is not None:
            self.P1_update(data['pp_data']['p1'])
        if data['pp_data']['p2'] is not None:
            self.P2_update(data['pp_data']['p2'])

    def Network_bullets(self, data):
        self.Update_bullets(data['bullets'])
        if self.is_p1:
            self.Update_health(data['p1_hit'])
        else:
            self.Update_health(data['p2_hit'])

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
