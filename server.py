import sys
from time import sleep, localtime
from weakref import WeakKeyDictionary
import pygame
from random import randint

from PodSixNet.Server import Server
from PodSixNet.Channel import Channel

class ServerChannel(Channel):
    """
    This is the server representation of a single connected client.
    """
    def __init__(self, *args, **kwargs):
        Channel.__init__(self, *args, **kwargs)
        self.id = str(self._server.NextId())
        self.player_pos = [0, 0]
        self.bullets = pygame.sprite.Group()

    def PassOn(self, data):
        # pass on what we received to all connected clients
        self._server.SendToAll(data)

    def Close(self):
        self._server.DelPlayer(self)

    ##################################
    ### Network specific callbacks ###
    ##################################

    def Network_move(self, data):
        self.PassOn(data)

class TinyServer(Server):
    channelClass = ServerChannel

    def __init__(self, *args, **kwargs):
        self.id = 0
        Server.__init__(self, *args, **kwargs)
        self.p1 = None
        self.p2 = None
        print 'Server launched'

    def NextId(self):
        self.id += 1
        return self.id

    def Connected(self, channel, addr):
        if self.p1 is not None and self.p2 is not None:
            channel.Send({"action": "admin", "message": "server_full"})  # TODO: Make sure client handles this
        else:
            self.AddPlayer(channel)

    def AddPlayer(self, player):
        # Determine if P1 or P2
        if self.p1 is None and self.p2 is None:
            self.p1 = player
            print "New P1 (" + str(player.addr) + ")"
        elif self.p1 is not None and self.p2 is None:
            self.p2 = player
            print "New P2 (" + str(player.addr) + ")"
        else:
            sys.stderr.write("ERROR: Couldn't determine player\n")
            sys.stderr.flush()
            sys.exit(1)


        # If only P1, send "waiting" message
        if self.p2 is None:
            player.Send({"action": "initial", "pp_data": None})
        # Else if P2, exchange position info and start game
        else:
            player.Send('player data')  # TODO: Implement proper message

    def DelPlayer(self, player):
        if self.p1 is player:
            self.p1 = None
            # TODO: Send message to P2 that P1 has left
            print "Deleted P1 (" + str(player.addr) + ")"
        elif self.p2 is player:
            self.p2 = None
            # TODO: Send message to P1 that P2 has left
            print "Deleted P2 (" + str(player.addr) + ")"
        else:
            print("ERROR: Can't delete player")

    def SendToAll(self, data):
        if self.p1 is not None:
            self.p1.Send(data)
        if self.p2 is not None:
            self.p2.Send(data)

    def Launch(self):
        while True:
            self.Pump()
            sleep(0.0001)

# get command line argument of server, port
if len(sys.argv) != 2:
    print "Usage:", sys.argv[0], "host:port"
    print "e.g.", sys.argv[0], "localhost:31425"
else:
    host, port = sys.argv[1].split(":")
    s = TinyServer(localaddr=(host, int(port)))
    s.Launch()
