import sys
import os
import pygame
from collections import deque
from time import sleep
from tinySpaceBattles import Bullet, Starship
from PodSixNet.Server import Server
from PodSixNet.Channel import Channel

X_DIM = 1000
Y_DIM = 700
SCREENSIZE = (X_DIM, Y_DIM)


class ServerChannel(object, Channel):
    """
    This is the server representation of a single connected client.
    """
    def __init__(self, *args, **kwargs):
        Channel.__init__(self, *args, **kwargs)
        self.id = str(self._server.NextId())
        self._player_pos = [0, 0]
        self.p1 = None
        self.sprite = Starship()  # Each player needs a sprite representation
        self.bullets = pygame.sprite.Group()  # Each player has their own list of bullets

    @property
    def player_pos(self):
        return self._player_pos

    @player_pos.setter
    def player_pos(self, value):
        self.sprite.set_loc(value[0], value[1])
        self._player_pos = value

    def WhichPlayer(self):
        return str("p1") if self.p1 else str("p2")

    def PassOn(self, data):
        # pass on what we received to all connected clients
        self._server.SendToAll(data)

    def Close(self):
        self._server.DelPlayer(self)

    ##################################
    ### Network specific callbacks ###
    ##################################

    def Network_move(self, data):
        if self.p1:
            self.player_pos = data['pp_data']['p1']
        else:
            self.player_pos = data['pp_data']['p2']
        self.PassOn(data)

    def Network_fire(self, data):
        bullet = Bullet()
        bullet.right = self.p1  # True when P1 (right), False when P2 (left)
        # Set the bullet so it is where the player is
        bullet.rect.x = self.player_pos[0]
        bullet.rect.y = self.player_pos[1]
        # Adjust the bullet's position so that it looks a little better
        if self.p1:
            bullet.rect.x += 105
            bullet.rect.y += 37
        else:
            bullet.rect.y += 37
        # Add the bullet to the list
        self.bullets.add(bullet)

class TinyServer(object, Server):
    channelClass = ServerChannel

    def __init__(self, *args, **kwargs):
        self.id = 0
        Server.__init__(self, *args, **kwargs)
        self.p1 = None
        self.p2 = None
        self.ready = False
        self.waiting_player_list = deque()  # Make a FIFO queue for waiting clients (no limit to waiting clients)
        print 'Server launched'

    def NextId(self):
        self.id += 1
        return self.id

    def Connected(self, channel, addr):
        if self.p1 and self.p2:
            channel.Send({"action": "init", "p": "full"})
            self.waiting_player_list.append(channel)
        else:
            self.AddPlayer(channel)

    def AddPlayer(self, player):
        # Determine if P1 or P2
        if self.p1 is None:
            self.p1 = player
            player.p1 = True
            print "New P1 (" + str(player.addr) + ")"
        elif self.p1 and self.p2 is None:
            self.p2 = player
            player.p1 = False
            print "New P2 (" + str(player.addr) + ")"
        else:
            sys.stderr.write("ERROR: Couldn't determine player from client (P1 = "
                             + str(self.p1) + ",  P2 = "
                             + str(self.p2) + ".\n")
            sys.stderr.flush()
            sys.exit(1)
        # If only P1, tell client they're P1
        if self.p2 is None:
            player.Send({"action": "init", "p": 'p1'})
        # Else if P2, notify P2 and send position data
        else:
            self.p2.Send({"action": "init", "p": 'p2'})
            self.SendToAll({"action": "ready"})
            # Only send position data from P1 -> P2
            self.SendToAll({"action": "move", "pp_data": dict({'p1': self.p1.player_pos, 'p2': None})})
            self.ready = True

    def DelPlayer(self, player):
        self.ready = False
        if self.p1 is player:
            self.p1 = None
            self.SendToAll({"action": "player_left"})
            print "Deleted P1 (" + str(player.addr) + ")"
        elif self.p2 is player:
            self.p2 = None
            self.SendToAll({"action": "player_left"})
            print "Deleted P2 (" + str(player.addr) + ")"
        elif player in self.waiting_player_list:
            self.waiting_player_list.remove(player)
        else:
            print("ERROR: Can't delete player")
        # Pull waiting player from queue
        if self.waiting_player_list:
            self.AddPlayer(self.waiting_player_list.popleft())

    def HandleBullets(self):
        # Check if there are bullets (if all bullets are cleared, still should update screen to clear bullets)
        player_had_bullets = True if (self.p1.bullets or self.p2.bullets) else False

        # Update bullet positions
        self.p1.bullets.update()
        self.p2.bullets.update()

        # Do collision detection
        self.HandleBulletHits(self.p1)
        self.HandleBulletHits(self.p2)

        # Generate position list
        bullet_list = self.GenerateBulletLocs()

        # Send new bullet lists
        if bullet_list or player_had_bullets:
            self.SendToAll({"action": "bullets",
                            "bullets": bullet_list,
                            "p1_health": self.p1.sprite.health,
                            "p2_health": self.p2.sprite.health})

    def GenerateBulletLocs(self):
        bullet_locs = list()
        for player in {self.p1, self.p2}:
            for bullet in player.bullets:
                # Remove the bullet if it flies off the screen
                if bullet.rect.x < 5 or bullet.rect.x > (X_DIM - 5):
                    bullet.kill()
                    break
                # If we're here, bullet is still moving and should be sent to clients
                bullet_locs.append((bullet.rect.x, bullet.rect.y))
        return bullet_locs

    def HandleBulletHits(self, player):
        if player.p1:
            other_player = self.p2
        else:
            other_player = self.p1

        # Perform collision detection
        bullets_hit = pygame.sprite.spritecollide(player.sprite, other_player.bullets, False)

        # For each block hit, subtract health
        for bullet in bullets_hit:
            player.sprite.health -= 10
            bullet.kill()

    def SendToAll(self, data):
        if self.p1 is not None:
            self.p1.Send(data)
        if self.p2 is not None:
            self.p2.Send(data)

    def Launch(self):
        while True:
            self.Pump()
            if self.ready:
                self.HandleBullets()
            sleep(0.001)  # 0.01, 0.0001?

# Assign dummy SDL screen and init headless PyGame
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
screen = pygame.display.set_mode((1, 1))

# get command line argument of server, port
if len(sys.argv) != 2:
    print "Usage:", sys.argv[0], "host:port"
    print "e.g.", sys.argv[0], "localhost:31425"
else:
    host, port = sys.argv[1].split(":")
    s = TinyServer(localaddr=(host, int(port)))
    s.Launch()
