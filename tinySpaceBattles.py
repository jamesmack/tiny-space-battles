from sys import exit
from os import environ
import pygame
import math
from random import randrange

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
                1: 'cw'}  # D-pad right

wiimote_shield = {4: 's',   # A button
                  11: 's'}  # C button (Nunchuck)

wiimote_fire = {12: 'f',  # Z button (Nunchuck)
                5: 'f'}   # B button

keyboard_move = {pygame.K_a: 'l',  # a
                 pygame.K_d: 'r',  # d
                 pygame.K_w: 'u',  # w
                 pygame.K_s: 'd',  # s
                 pygame.K_q: 'ccw',  # q
                 pygame.K_e: 'cw'  # e
                 }

keyboard_shield = {pygame.K_PERIOD: 's'}  # .

keyboard_fire = {pygame.K_SPACE: 'f'}  # *space*

environ['SDL_VIDEO_CENTERED'] = '1'
pygame.init()
screen = pygame.display.set_mode(SCREENSIZE)
pygame.display.set_caption("Tiny Space Battles")
background_image = pygame.image.load("images/bg.png")
healthbar = pygame.image.load("images/healthbar.png")
healthbar_slices = pygame.image.load("images/health.png")

pygame.font.init()
fnt = pygame.font.SysFont("Arial", 14)
txtpos = (100, 90)


class Starship(pygame.sprite.Sprite):
    """ This class represents a starship. """

    def __init__(self):
        """ Set up the player on creation. """
        # Call the parent class (Sprite) constructor
        super(Starship, self).__init__()
        self.health = 0
        self.angle = 0
        self.image = pygame.Surface([120, 75])
        self.colour = BLACK
        self.image.fill(self.colour)
        self.image_orig = self.image
        self.rect = self.image.get_rect()
        self.rect.x = randrange(0, 100)
        self.rect.y = randrange(200, 300)
        self.bullets = pygame.sprite.Group()
        self.reset_health()

    def reset_health(self):
        self.health = 194

    def update(self, loc, assign_new_center=False):
        [x, y, angle] = loc
        self.set_loc(x, y)
        if angle != self.angle:
            self.rotate(angle, assign_new_center)

    def rotate(self, angle, assign_new_center=False):
        new_center = self.rect.center
        self.image = pygame.transform.rotate(self.image_orig, angle)
        if assign_new_center:
            self.rect = self.image.get_rect(center=new_center)
        self.angle = angle

    def set_colour(self, colour):
        self.colour = colour
        self.image.fill(self.colour)
        self.rect = self.image.get_rect()

    def set_graphic(self, p1):
        if p1:
            self.image = pygame.image.load("images/p1.png")
        else:
            self.image = pygame.image.load("images/p2.png")
        self.image_orig = self.image
        self.image.convert_alpha()
        self.rect = self.image.get_rect()

    def set_p1(self, p1):
        """ Set True for P1, False for P2. """
        if p1:
            self.set_graphic(True)
            self.set_loc(randrange(0, 50), randrange((Y_DIM/2)-50, (Y_DIM/2)+50))
        else:
            self.set_p2(True)

    def set_p2(self, p2):
        """ Set True for P2, False for P1. """
        if p2:
            self.set_graphic(False)
            self.set_loc(randrange(X_DIM-180, X_DIM-150), randrange((Y_DIM/2)-50, (Y_DIM/2)+50))
            self.rotate(180)
        else:
            self.set_p1(True)

    def set_loc(self, x, y):
        """ Update the player's position. """
        # Set position
        self.rect.x = x
        self.rect.y = y

    def get_loc(self):
        """ Return player position. """
        return [self.rect.x, self.rect.y]

    def draw(self, surface):
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
        self.frame = 0
        self.player_list = pygame.sprite.Group()
        self.bullet_list = pygame.sprite.Group() # Don't use the bullet list in players (no need to be separate lists)
        self.p1 = Starship()
        self.p1.set_p1(True)
        self.p2 = Starship()
        self.p2.set_p2(True)
        self.wiimote = None
        self.is_p1 = None
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

    def Win_or_lose(self, win):
        pass  # Overlay win or lose message on screen

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
            for button in xrange(0, 2):
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

            if event.type == pygame.JOYBUTTONDOWN:
                button = event.dict['button']
                if button in wiimote_move:
                    self.Player_move(wiimote_move[button])
                elif button in wiimote_fire:
                    self.Player_fire()
                elif button in wiimote_shield:
                    self.Player_shield()


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
        pygame.display.flip()


