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

X_DIM = 1000
Y_DIM = 700
SCREENSIZE = (X_DIM, Y_DIM)

wiimote_move = {0: 'l',  # D-pad left
                1: 'r',  # D-pad right
                2: 'u',  # D-pad up
                3: 'd'  # D-pad down
                }

wiimote_shield = {4: 's'}  # A button

wiimote_fire = {5: 'f'}  # B button

keyboard_move = {pygame.K_a: 'l',  # a
                 pygame.K_d: 'r',  # d
                 pygame.K_w: 'u',  # w
                 pygame.K_s: 'd'  # s
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
        self.image = pygame.Surface([120, 75])
        self.colour = BLACK
        self.image.fill(self.colour)
        self.rect = self.image.get_rect()
        self.rect.x = randrange(0, 100)
        self.rect.y = randrange(200, 300)
        self.bullets = pygame.sprite.Group()
        self.health = 0
        self.reset_health()

    def reset_health(self):
        self.health = 194

    def set_colour(self, colour):
        self.colour = colour
        self.image.fill(self.colour)
        self.rect = self.image.get_rect()

    def set_graphic(self, p1):
        if p1:
            self.image = pygame.image.load("images/p1.png")
        else:
            self.image = pygame.image.load("images/p2.png")
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


class Bullet(pygame.sprite.Sprite):
    """ This class represents the bullet . """
    def __init__(self):
        # Call the parent class (Sprite) constructor
        super(Bullet, self).__init__()
        self.image = pygame.Surface([10, 3])
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.bullet_speed = 1
        self.right = True

    def update(self):
        """ Move the bullet (PyGame-dictated function and signature). """
        if self.right:  # move right
            self.rect.x += self.bullet_speed
        else:  # move left
            self.rect.x -= self.bullet_speed


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
        self.down = False
        self.all_sprites_list = pygame.sprite.Group()
        self.bullet_list = pygame.sprite.Group() # Don't use the bullet list in players (no need to be separate lists)
        self.p1 = Starship()
        self.p1.set_p1(True)
        self.p2 = Starship()
        self.p2.set_p2(True)
        self.wiimote = None
        self.is_p1 = None

        self.Player_init()
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

    def Player_init(self):
        self.all_sprites_list.add(self.p1)
        self.all_sprites_list.add(self.p2)

    def P1_update(self, loc):
        [x, y] = loc
        self.p1.set_loc(x, y)

    def P2_update(self, loc):
        [x, y] = loc
        self.p2.set_loc(x, y)

    def Recreate_sprite_lists(self):  # Need to find a better solution...
        self.all_sprites_list.empty()
        self.all_sprites_list.add(self.p1)
        self.all_sprites_list.add(self.p2)
        self.all_sprites_list.add(self.bullet_list)

    def Win_or_lose(self, win):
        pass

    def Update_bullets(self, bullets):
        self.bullet_list.empty()
        for loc in bullets:
            bullet = Bullet()
            # Set the bullet's position
            bullet.rect.x = loc[0]
            bullet.rect.y = loc[1]
            # Add the bullet to the list
            self.bullet_list.add(bullet)

    def Check_for_button_held(self):
        if self.wiimote is not None:
            for button in xrange(0, 4):
                if self.wiimote.get_button(button):
                    self.Player_move(wiimote_move[button])

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
        self.Recreate_sprite_lists()
        self.all_sprites_list.draw(screen)
        pygame.display.flip()


