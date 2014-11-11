from sys import exit
from os import environ
import pygame
from random import randrange

# Define some colors
BLACK = (0,   0,   0)
WHITE = (255, 255, 255)
GREEN = (0, 255,   0)
RED = (255,   0,   0)
BLUE = (0,   0, 255)

X_DIM = 640
Y_DIM = 480
SCREENSIZE = (X_DIM, Y_DIM)

wiimote_move = {0: 'l',  # D-pad left
                1: 'r',  # D-pad right
                2: 'u',  # D-pad up
                3: 'd'  # D-pad down
                }

wiimote_shield = {4: 's'}  # A button

wiimote_fire = {5: 'f'}  # B button

environ['SDL_VIDEO_CENTERED'] = '1'
pygame.init()
screen = pygame.display.set_mode(SCREENSIZE)
pygame.display.set_caption("Tiny Space Battles")

pygame.font.init()
fnt = pygame.font.SysFont("Arial", 14)
txtpos = (100, 90)


class Starship(pygame.sprite.Sprite):
    """ This class represents a starship. """

    def __init__(self):
        """ Set up the player on creation. """
        # Call the parent class (Sprite) constructor
        super(Starship, self).__init__()
        self.image = pygame.Surface([30, 30])
        self.colour = BLUE
        self.image.fill(self.colour)
        self.rect = self.image.get_rect()
        self.rect.x = randrange(0, 100)
        self.rect.y = randrange(200, 300)

    def set_colour(self, colour):
        self.colour = colour
        self.image.fill(self.colour)
        self.rect = self.image.get_rect()

    def set_enemy(self, enemy):
        if enemy:
            self.set_colour(RED)
            self.update(randrange(550, 600), randrange(200, 300))

    def update(self, x, y):
        """ Update the player's position. """
        # Set position
        self.rect.x = x
        self.rect.y = y

    def get_loc(self):
        return [self.rect.x, self.rect.y]


class TinySpaceBattles:
    def __init__(self):
        self.statusLabel = "Connecting"
        self.playersLabel = "Waiting for player"
        self.frame = 0
        self.down = False
        self.all_sprites_list = pygame.sprite.Group()
        self.p1 = Starship()
        self.p2 = Starship()
        self.p2.set_enemy(True)
        self.wiimote = None

        self.Player_init()
        self.Wiimote_init()


    def Wiimote_init(self):
        # Count the joysticks the computer has
        if pygame.joystick.get_count() == 0:
            # No joysticks!
            print ("No Wiimote found! You need a Wiimote to play this game (for now...).")
            pygame.quit()
            exit()

        # Use joystick #0 and initialize it
        self.wiimote = pygame.joystick.Joystick(0)
        self.wiimote.init()

    def Player_init(self):
        self.all_sprites_list.add(self.p1)
        self.all_sprites_list.add(self.p2)

    def P1_update(self, loc):
        [x, y] = loc
        self.p1.update(x, y)

    def P2_update(self, loc):
        [x, y] = loc
        self.p2.update(x, y)

    def Check_for_button_held(self):
        for button in xrange (0,4):
            if self.wiimote.get_button(button):
                self.Player_move(self.p1.get_loc(), wiimote_move[button])

    def Events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == 27):
                exit()

            if event.type == pygame.JOYBUTTONDOWN:
                button = event.dict['button']
                if button in wiimote_move:
                    self.Player_move(self.p1.get_loc(), wiimote_move[button])
                elif button in wiimote_fire:
                    self.Player_fire(self.p1.get_loc())
                elif button in wiimote_shield:
                    self.Player_shield(self.p1.get_loc())


    def Draw(self):
        screen.fill(WHITE)
        txt = fnt.render(self.statusLabel, 1, (0, 0, 0))
        screen.blit(fnt.render(self.statusLabel, 1, (0, 0, 0)), [10, 10])
        txt = fnt.render(self.playersLabel, 1, (0, 0, 0))
        screen.blit(fnt.render(self.playersLabel, 1, (0, 0, 0)), [10, 20])
        self.all_sprites_list.draw(screen)
        pygame.display.flip()


