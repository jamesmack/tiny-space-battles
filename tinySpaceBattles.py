from sys import exit
from os import environ
import pygame
import math
from random import randrange
from collections import deque

# Define some colors
BLACK = (0,   0,   0)
WHITE = (255, 255, 255)
GREEN = (0, 255,   0)
RED = (255,   0,   0)
BLUE = (0,   0, 255)

X_DIM = 1000
Y_DIM = 700
SCREENSIZE = (X_DIM, Y_DIM)

# Nunchuck joystick threshold
JOY_THRESH = 0.08

wiimote_move = {0: 'ccw',  # D-pad left
                2: 'ccw',  # D-pad up
                1: 'cw',  # D-pad down
                3: 'cw'}  # D-pad right

wiimote_shield = {4: 's',   # A button
                  11: 's'}  # C button (Nunchuck)

wiimote_fire = {12: 'f',  # Z button (Nunchuck)
                5: 'f'}   # B button

wiimote_restart = {8: 'restart'}

keyboard_move = {pygame.K_a: 'l',  # a
                 pygame.K_d: 'r',  # d
                 pygame.K_w: 'u',  # w
                 pygame.K_s: 'd',  # s
                 pygame.K_q: 'ccw',  # q
                 pygame.K_e: 'cw'  # e
                 }

keyboard_shield = {pygame.K_PERIOD: 's'}  # .

keyboard_fire = {pygame.K_SPACE: 'f'}  # *space*

keyboard_restart = {pygame.K_j: 'restart'}

environ['SDL_VIDEO_CENTERED'] = '1'
pygame.init()
screen = pygame.display.set_mode(SCREENSIZE)
pygame.display.set_caption("Tiny Space Battles")
background_image = pygame.image.load("images/bg.png")
win_lose_bg_image = pygame.image.load("images/win_lose_bg.png")
healthbar = pygame.image.load("images/healthbar.png")
healthbar_slices = pygame.image.load("images/health.png")

pygame.font.init()
fnt = pygame.font.SysFont("Arial", 14)
fnt_big = pygame.font.SysFont("Arial", 50)
fnt_med = pygame.font.SysFont("Arial", 30)
txtpos = (100, 90)


class Starship(pygame.sprite.Sprite):
    """ This class represents a starship, which is the client's representation of a player. """

    def __init__(self):
        """ Set up the player on creation. """
        # Call the parent class (Sprite) constructor
        super(Starship, self).__init__()
        self.health = 0
        self.angle = 0
        self.position_hist = deque(iter([]), 10)
        self.image = pygame.Surface([120, 75])
        self.colour = BLACK
        self.image.fill(self.colour)
        self.image_orig = self.image
        self.rect = self.image.get_rect()
        self.rect.x = randrange(0, 100)
        self.rect.y = randrange(200, 300)
        self.bullets = pygame.sprite.Group()
        self.reset_health()

    @property
    def rect_xy(self):
        return [self.rect.x, self.rect.y]

    @rect_xy.setter
    def rect_xy(self, (x, y)):
        self.rect.x = x
        self.rect.y = y

    def reset_health(self):
        """
        Reset the player's health (194 due to 1:1 mapping of health blocks in bar to health attribute).
        :return: None
        """
        self.health = 194

    def update(self, loc, assign_new_center=False):
        """
        Called to update the player's location.
        :list loc: New player location [x, y, angle]
        :bool assign_new_center: Whether rotation should maintain rotation around image's center
        :return: None
        """
        [x, y, angle] = loc
        self.rect_xy = (x, y)
        if angle != self.angle:
            self.rotate(angle, assign_new_center)

    def rotate(self, angle, assign_new_center=False):
        """
        Rotates player's sprite.
        :int angle: Amount of angle in degrees to rotate
        :bool assign_new_center: Whether rotation should maintain rotation around image's center
        :return: None
        """
        new_center = self.rect.center
        self.image = pygame.transform.rotate(self.image_orig, angle)
        if assign_new_center:
            self.rect = self.image.get_rect(center=new_center)
        self.angle = angle

    def set_graphic(self, p1):
        """
        Set a player's sprite to an image.
        :bool p1: True if setting P1's sprite, False otherwise
        :return: None
        """
        if p1:
            self.image = pygame.image.load("images/p1.png")
        else:
            self.image = pygame.image.load("images/p2.png")
        self.image_orig = self.image
        self.image.convert_alpha()
        self.rect = self.image.get_rect()

    def rand_pos(self, p1):
        """
        Randomize position of sprite.
        :bool p1: True if setting P1's sprite, False otherwise
        :return: None
        """
        self.rotate(0)
        if p1:
            self.rect_xy = (randrange(0, 50), randrange((Y_DIM/2)-50, (Y_DIM/2)+50))
        else:
            self.rect_xy = (randrange(X_DIM-180, X_DIM-150), randrange((Y_DIM/2)-50, (Y_DIM/2)+50))
            self.rotate(180)

    def set_p1(self, p1):
        """
        Set graphic and randomize position of sprite.
        :bool p1: True if setting P1's sprite, False otherwise
        :return: None
        """
        if p1:
            self.set_graphic(True)
            self.rand_pos(True)
        else:
            self.set_p2(True)

    def set_p2(self, p2):
        """
        Set graphic and randomize position of sprite.
        :bool p2: True if setting P2's sprite, False otherwise
        :return: None
        """
        if p2:
            self.set_graphic(False)
            self.rand_pos(False)
        else:
            self.set_p1(True)

    def draw(self, surface):
        """
        Draw the player on the screen.
        :pygame.surface surface: The surface on which to draw the sprite.
        :return:
        """
        surface.blit(self.image, self.rect)


class Bullet(pygame.sprite.Sprite):
    """ This class represents the bullet . """
    def __init__(self, angle):
        # Call the parent class (Sprite) constructor
        super(Bullet, self).__init__()
        self.angle = angle
        self.image = pygame.Surface([10, 3])
        self.image.fill(GREEN)
        self.image_orig = self.image.convert_alpha()
        self.image = pygame.transform.rotate(self.image_orig, self.angle)
        self.rect = self.image.get_rect()
        self.bullet_speed = 1
        self.x = 0
        self.y = 0
        self.dx = math.cos(math.radians(self.angle)) * self.bullet_speed
        self.dy = math.sin(math.radians(-self.angle)) * self.bullet_speed

    def update(self):
        """ Move the bullet (PyGame-dictated function and signature). """
        self.x += self.dx
        self.y += self.dy
        self.rect.x = self.x
        self.rect.y = self.y

    def set_loc(self, x, y):
        """ Update the bullet's position. """
        # Set position
        self.rect.x = x
        self.rect.y = y

    def get_loc(self):
        """ Return bullet position. """
        return [self.rect.x, self.rect.y]


class TinySpaceBattles(object):
    def __init__(self):
        self.statusLabel = "Connecting"
        self.playersLabel = "Waiting for player"
        self.winLoseLabel = ''
        self.restartLabel = 'Press Home button or j key to restart'
        self.frame = 0
        self.player_list = pygame.sprite.Group()
        self.bullet_list = pygame.sprite.Group() # Don't use the bullet list in players (no need to be separate lists)
        self.p1 = Starship()
        self.p1.set_p1(True)
        self.p2 = Starship()
        self.p2.set_p2(True)
        self.wiimote = None
        self.is_p1 = None
        self.game_over = False
        self.has_won = False
        self.Wiimote_init()

    def Wiimote_init(self):
        # Count the joysticks the computer has
        if pygame.joystick.get_count() == 0:
            # No joysticks!
            print ("No Wiimote found!")
            pygame.key.set_repeat(1, 50)
        else:
            # Use joystick #0 and initialize it
            self.wiimote = pygame.joystick.Joystick(0)
            self.wiimote.init()

    def Which_player(self):
        return str("p1") if self.is_p1 else str("p2")

    def Win_or_lose(self, player):
        self.game_over = True
        if (self.is_p1 and player == 'p2') or (not self.is_p1 and player == 'p1'):
            self.has_won = True
            self.winLoseLabel = 'You won!'
        else:
            self.winLoseLabel = 'You lost.'

    def Update_bullets(self, bullets):
        self.bullet_list.empty()
        for loc in bullets:
            bullet = Bullet(loc[2])
            # Set the bullet's position
            bullet.rect.x = loc[0]
            bullet.rect.y = loc[1]
            # Add the bullet to the list
            self.bullet_list.add(bullet)

    def Check_for_wiimote_move(self):
        if self.wiimote is not None:
            move = set()

            # Handle Nunchuck joystick
            axis_0 = self.wiimote.get_axis(0)
            axis_1 = self.wiimote.get_axis(1)
            y_mag = 0
            x_mag = 0
            if abs(axis_0) > JOY_THRESH:
                x_mag = axis_0
                if axis_0 > JOY_THRESH:
                    move.add('r')
                else:
                    move.add('l')
            if abs(axis_1) > JOY_THRESH:
                y_mag = axis_1
                if axis_1 > JOY_THRESH:
                    move.add('d')
                else:
                    move.add('u')

            # Handle Wiimote D-Pad here
            for button in xrange(0, 4):
                if self.wiimote.get_button(button):
                    move.add(wiimote_move[button])
            if x_mag or y_mag:
                self.Player_move(move, pow(x_mag, 2), pow(y_mag, 2))
            elif move:
                self.Player_move(move)

    def Events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()

            if event.type == pygame.KEYDOWN:
                button = event.key
                if button in keyboard_move:
                    self.Player_move(keyboard_move[button])
                elif button in keyboard_fire:
                    self.Player_fire()
                elif button in keyboard_shield:
                    self.Player_shield()
                elif button in keyboard_restart and self.game_over:
                    self.Player_restart()

            if event.type == pygame.JOYBUTTONDOWN:
                button = event.dict['button']
                if button in wiimote_move:
                    self.Player_move(wiimote_move[button])
                elif button in wiimote_fire:
                    self.Player_fire()
                elif button in wiimote_shield:
                    self.Player_shield()
                elif button in wiimote_restart and self.game_over:
                    self.Player_restart()


    def Draw(self):
        #Draw background image
        screen.blit(background_image, [0, 0])

        # P1 health
        screen.blit(healthbar, [5, 5])
        for health_increments in range(self.p1.health):
            screen.blit(healthbar_slices, (health_increments + 8, 8))
        screen.blit(fnt.render("P1 health", 1, BLACK), [10, 7])

        # P2 health
        screen.blit(healthbar, [X_DIM - 5 - 200, 5])
        for health_increments in range(self.p2.health):
            screen.blit(healthbar_slices, (X_DIM - health_increments + 8 - 17, 8))
        screen.blit(fnt.render("P2 health", 1, BLACK), [X_DIM - 10 - 60, 7])

        # Draw connection and player status
        screen.blit(fnt.render(self.statusLabel, 1, WHITE), [10, 25])
        screen.blit(fnt.render(self.playersLabel, 1, WHITE), [10, 40])

        # Draw players and bullets
        self.bullet_list.draw(screen)
        self.p1.draw(screen)
        self.p2.draw(screen)

        # If game over, notify player
        if self.game_over:
            # Transparency overlay
            screen.blit(win_lose_bg_image, [0, 0])

            # Win/lose font
            text = fnt_big.render(self.winLoseLabel, 1, WHITE)
            textpos = text.get_rect()
            textpos.centerx = background_image.get_rect().centerx
            textpos.centery = background_image.get_rect().centery - 200
            screen.blit(text, textpos)

            # Restart font
            text = fnt_med.render(self.restartLabel, 1, WHITE)
            textpos = text.get_rect()
            textpos.centerx = background_image.get_rect().centerx
            textpos.centery = background_image.get_rect().centery + 100
            screen.blit(text, textpos)

        pygame.display.flip()


