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
        self.sprite.update(value)
        self._player_pos = self.sprite.rect.x, self.sprite.rect.y

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
        self.player_pos = data['p_pos']
        self.PassOn(data)

    def Network_fire(self, data):
        bullet = Bullet(self.sprite.angle)
        # Set the bullet so it is where the player is
        bullet.x = self.sprite.rect.center[0]
        bullet.y = self.sprite.rect.center[1]
        # Add the bullet to the list
        self.bullets.add(bullet)

    def Network_restart(self, data):
        self._server.Restart()

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
            loc = list(self.p1.player_pos)
            loc.append(self.p1.sprite.angle)
            self.SendToAll({"action": "move", "p": "p1", "p_pos": loc})
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

        # If any of the players have died, let both players know
        if self.p1.sprite.health <= 0 or self.p2.sprite.health <= 0:
            self.HandleDeath()

    def HandleDeath(self):
        if self.p1.sprite.health <= 0:
            dead = self.p1.WhichPlayer()
            print("P1 has died")
        else:
            dead = self.p2.WhichPlayer()
            print("P2 has died")
        # Send message to clients that a player has died
        self.SendToAll({"action": "death", "p": dead})
        self.ready = False

    def Restart(self):
        if self.p1 and self.p2:
            self.p1.sprite.reset_health()
            self.p2.sprite.reset_health()

            # Clear bullet lists
            self.p1.bullets.empty()
            self.p1.bullets.empty()
            self.SendToAll({"action": "bullets",
                            "bullets": list(),
                            "p1_health": self.p1.sprite.health,
                            "p2_health": self.p2.sprite.health})

            # TODO: Reset player positions

            # Notify clients
            self.SendToAll({"action": "restart"})
            self.ready = True

    def GenerateBulletLocs(self):
        bullet_locs = list()
        for player in {self.p1, self.p2}:
            for bullet in player.bullets:
                # Remove the bullet if it flies off the screen
                if bullet.rect.x < -15 or bullet.rect.x > (X_DIM + 15) or bullet.rect.y < -15 or bullet.rect.y > (X_DIM + 15):
                    bullet.kill()
                    break
                # If we're here, bullet is still moving and should be sent to clients
                bullet_locs.append((bullet.rect.x, bullet.rect.y, bullet.angle))
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
