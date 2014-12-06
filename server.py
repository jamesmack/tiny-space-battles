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
        self.id = str(self._server.next_id())
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

    def which_player(self):
        return str("p1") if self.p1 else str("p2")

    def pass_on(self, data):
        """
        Pass data to all connected clients
        :dict data: Data to forward to clients
        :return: None
        """
        self._server.send_to_all(data)

    def Close(self):
        """
        PodSixNet-defined callback for closing connection.
        :return:
        """
        self._server.delete_player(self)

    ##################################
    ### Network specific callbacks ###
    ##################################

    def Network_move(self, data):
        """
        Processes move data from client.
        :dict data: Data from client.
        :return: None
        """
        self.player_pos = data['p_pos']
        self.pass_on(data)

    def Network_fire(self, data):
        """
        Processes fire data from client.
        :dict data: Data from client.
        :return: None
        """
        bullet = Bullet(self.sprite.angle)
        # Set the bullet so it is where the player is
        bullet.x = self.sprite.rect.center[0]
        bullet.y = self.sprite.rect.center[1]
        # Add the bullet to the list
        self.bullets.add(bullet)

    def Network_restart(self, data):
        """
        Processes restart from client.
        :dict data: Data from client.
        :return: None
        """
        self._server.restart()


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

    ###########################
    ### PodSixNet callbacks ###
    ###########################

    def Connected(self, channel, addr):
        """
        PodSixNet-defined callback for when a cient connects.
        :ServerChannel channel: Representation of player
        :str addr: IP address of channel
        :return: None
        """
        if self.p1 and self.p2:
            channel.Send({"action": "init", "p": "full"})
            self.waiting_player_list.append(channel)
        else:
            self.add_player(channel)

    ########################
    ### Server functions ###
    ########################

    def next_id(self):
        """
        Generates unique ID for each client.
        :return: ID number for client
        """
        self.id += 1
        return self.id

    def add_player(self, player):
        """
        Adds new player.
        :ServerChannel player: PLayer to add.
        :return: None
        """
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
            self.send_to_all({"action": "ready"})
            # Only send position data from P1 -> P2
            loc = list(self.p1.player_pos)
            loc.append(self.p1.sprite.angle)
            self.send_to_all({"action": "move", "p": "p1", "p_pos": loc})
            self.ready = True

    def delete_player(self, player):
        """
        Deletes player from server.
        :ServerChannel player: PLayer to delete.
        :return:
        """
        self.ready = False
        if self.p1 is player:
            self.p1 = None
            self.send_to_all({"action": "player_left"})
            print "Deleted P1 (" + str(player.addr) + ")"
        elif self.p2 is player:
            self.p2 = None
            self.send_to_all({"action": "player_left"})
            print "Deleted P2 (" + str(player.addr) + ")"
        elif player in self.waiting_player_list:
            self.waiting_player_list.remove(player)
        else:
            print("ERROR: Can't delete player")
        # Pull waiting player from queue
        if self.waiting_player_list:
            self.add_player(self.waiting_player_list.popleft())

    def handle_bullets(self):
        """
        Perform bullet handling here
        :return: None
        """
        # Check if there are bullets (if all bullets are cleared, still should update screen to clear bullets)
        player_had_bullets = True if (self.p1.bullets or self.p2.bullets) else False

        # Update bullet positions
        self.p1.bullets.update()
        self.p2.bullets.update()

        # Do collision detection
        self.handle_bullet_hits(self.p1)
        self.handle_bullet_hits(self.p2)

        # Generate position list
        bullet_list = self.gen_bullet_locs()

        # Send new bullet lists
        if bullet_list or player_had_bullets:
            self.send_to_all({"action": "bullets",
                            "bullets": bullet_list,
                            "p1_health": self.p1.sprite.health,
                            "p2_health": self.p2.sprite.health})

        # If any of the players have died, let both players know
        if self.p1.sprite.health <= 0 or self.p2.sprite.health <= 0:
            self.handle_death()

    def handle_death(self):
        """
        Process the death of a player.
        :return: None
        """
        if self.p1.sprite.health <= 0:
            dead = self.p1.which_player()
            print("P1 has died")
        else:
            dead = self.p2.which_player()
            print("P2 has died")
        # Send message to clients that a player has died
        self.send_to_all({"action": "death", "p": dead})
        self.ready = False

    def restart(self):
        """
        Handle game restart.
        :return: None
        """
        if self.p1 and self.p2:
            self.p1.sprite.reset_health()
            self.p2.sprite.reset_health()

            # Clear bullet lists
            self.p1.bullets.empty()
            self.p2.bullets.empty()
            self.send_to_all({"action": "bullets",
                            "bullets": list(),
                            "p1_health": self.p1.sprite.health,
                            "p2_health": self.p2.sprite.health})

            # Notify clients
            self.send_to_all({"action": "restart"})
            self.ready = True

    def gen_bullet_locs(self):
        """
        Generate locations of bullets to send to players.
        :return: list of bullet locations
        """
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

    def handle_bullet_hits(self, player):
        """
        Perform collision detection on bullets.
        :ServerChannel player: Player to check number of hits on
        :return: None
        """
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

    def send_to_all(self, data):
        """
        Send data to all connected clients.
        :param data: Data to send
        :return: None
        """
        if self.p1 is not None:
            self.p1.Send(data)
        if self.p2 is not None:
            self.p2.Send(data)

    def launch_server(self):
        """
        Main server loop.
        :return: None
        """
        while True:
            self.Pump()
            if self.ready:
                self.handle_bullets()
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
    s.launch_server()
