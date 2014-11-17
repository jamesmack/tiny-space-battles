import sys
import pygame
from time import sleep
from tinySpaceBattles import Bullet
from PodSixNet.Server import Server
from PodSixNet.Channel import Channel

X_DIM = 640
Y_DIM = 480
SCREENSIZE = (X_DIM, Y_DIM)


class ServerChannel(Channel):
    """
    This is the server representation of a single connected client.
    """
    def __init__(self, *args, **kwargs):
        Channel.__init__(self, *args, **kwargs)
        self.id = str(self._server.NextId())
        self.player_pos = [0, 0]
        self.p1 = None
        self.bullets = pygame.sprite.Group()  # Each player has their own list of bullets

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
        bullet.rect.y = self.player_pos[1]+15
        # Add the bullet to the list
        self.bullets.add(bullet)

class TinyServer(Server):
    channelClass = ServerChannel

    def __init__(self, *args, **kwargs):
        self.id = 0
        Server.__init__(self, *args, **kwargs)
        self.p1 = None
        self.p2 = None
        self.ready = False
        print 'Server launched'

    def NextId(self):
        self.id += 1
        return self.id

    def Connected(self, channel, addr):
        if self.p1 is not None and self.p2 is not None:
            channel.Send({"action": "init", "p": "full"})
        else:
            self.AddPlayer(channel)

    def AddPlayer(self, player):
        # Determine if P1 or P2
        if self.p1 is None and self.p2 is None:
            self.p1 = player
            player.p1 = True
            print "New P1 (" + str(player.addr) + ")"
        elif self.p1 is not None and self.p2 is None:
            self.p2 = player
            player.p1 = False
            print "New P2 (" + str(player.addr) + ")"
        else:
            sys.stderr.write("ERROR: Couldn't determine player from client.\n")
            sys.stderr.flush()
            sys.exit(1)

        # If only P1, tell client they're P1
        if self.p2 is None:
            player.Send({"action": "init", "p": 'p1'})
        # Else if P2, notify P2 and send position data
        else:
            self.p2.Send({"action": "init", "p": 'p2'})
            self.SendToAll({"action": "ready"})
            self.SendToAll({"action": "move", "pp_data": dict({'p1': self.p1.player_pos, 'p2': self.p2.player_pos})})
            self.ready = True

    def DelPlayer(self, player):
        self.ready = False
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

    def HandleBullets(self):
        for player in {self.p1, self.p2}:
            # Check if there are bullets (if all bullets are cleared, still should update screen to clear bullets)
            player_had_bullets = True if player.bullets else False

            # Do collision detection
            bullet_list = self.HandlePlayerBullet(player)

            # Send new bullet lists (can't use sets because of rencode.py)
            if bullet_list or player_had_bullets:
                self.SendToAll({"action": "bullets", "p": player.WhichPlayer(), "bullets": bullet_list})

    def HandlePlayerBullet(self, player):
        bullet_locs = list()
        player.bullets.update()
        for bullet in player.bullets:
            # See if it hit a player
            # player_hit_list = pygame.sprite.spritecollide(bullet, player.bullets, False)

            # For each block hit, remove the bullet and add to the score
            # for player in player_hit_list:
            #     player.bullets.remove(bullet)
            #     break

            # # Remove the bullet if it flies off the screen
            if bullet.rect.x < 5 or bullet.rect.x > (X_DIM - 5):
                player.bullets.remove(bullet)
                break

            # If we're here, bullet is still moving and should be sent to clients
            bullet_locs.append((bullet.rect.x, bullet.rect.y))

        return bullet_locs

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
            sleep(0.01)  # 0.001, 0.0001?

# Quit PyGame window as soon as server starts (need a better way to do this, or implement a status GUI!)
pygame.display.quit()

# get command line argument of server, port
if len(sys.argv) != 2:
    print "Usage:", sys.argv[0], "host:port"
    print "e.g.", sys.argv[0], "localhost:31425"
else:
    host, port = sys.argv[1].split(":")
    s = TinyServer(localaddr=(host, int(port)))
    s.Launch()
