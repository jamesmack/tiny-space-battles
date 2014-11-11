import sys
from time import sleep

from PodSixNet.Connection import connection, ConnectionListener
from tinySpaceBattles import TinySpaceBattles


class Client(ConnectionListener, TinySpaceBattles):
    def __init__(self, host, port):
        self.Connect((host, port))
        self.players = {}
        TinySpaceBattles.__init__(self)

    def Loop(self):
        self.Pump()
        connection.Pump()
        self.Events()
        self.Check_for_button_held()
        self.Draw()

        if "Connecting" in self.statusLabel:
            self.statusLabel = "Connecting" + ("." * ((self.frame / 30) % 4))

    def Send_action(self, action, loc):
        connection.Send({"action": action, "pp_data": dict({'p1': loc, 'p2': None})})

    #######################
    ### Event callbacks ###
    #######################

    def Player_move(self, loc, dir):
        if 'l' in dir:
            loc[0] -= 5
            self.Send_action('move', loc)
        elif 'r' in dir:
            loc[0] += 5
            self.Send_action('move', loc)
        elif 'u' in dir:
            loc[1] -= 5
            self.Send_action('move', loc)
        elif 'd' in dir:
            loc[1] += 5
            self.Send_action('move', loc)

    def Player_fire(self, loc):
        self.Send_action('fire', loc)

    def Player_shield(self, loc):
        self.Send_action('shield', loc)

    ###############################
    ### Network event callbacks ###
    ###############################

    def Network_initial(self, data):
        if data["pp_data"] is None:
            print("No other players currently connected.")
        else:
            self.players = data['pp_data']  # Dictionary p1=x,y, p2=x,y

    def Network_players(self, data):
        mark = []

        for i in data['players']:
            if not i in self.players:
                self.players[i] = True

        for i in self.players:
            if not i in data['players'].keys():
                mark.append(i)

        for m in mark:
            del self.players[m]

        if str(len(data['players'])) == 2:
            self.playersLabel = 'Battle!'

    def Network_move(self, data):
        p1 = data['pp_data']['p1']
        p2 = data['pp_data']['p2']
        self.P1_update(p1)

    def Network(self, data):
        print 'network:', data
        pass

    def Network_connected(self, data):
        self.statusLabel = "Connected"

    def Network_error(self, data):
        print data
        import traceback
        traceback.print_exc()
        self.statusLabel = data['error'][1]
        connection.Close()

    def Network_disconnected(self, data):
        self.statusLabel = "Disconnected"

if len(sys.argv) != 2:
    print "Usage:", sys.argv[0], "host:port"
    print "e.g.", sys.argv[0], "localhost:31425"
else:
    host, port = sys.argv[1].split(":")
    c = Client(host, int(port))
    while 1:
        c.Loop()
        sleep(0.001)
