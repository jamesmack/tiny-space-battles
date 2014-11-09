import pygame
import random

# Define some colors
BLACK = (0,   0,   0)
WHITE = (255, 255, 255)
GREEN = (0, 255,   0)
RED = (255,   0,   0)
BLUE = (0,   0, 255)

# --- Classes
class Block(pygame.sprite.Sprite):
    """ This class represents the block. """
    def __init__(self, color):
        # Call the parent class (Sprite) constructor
        super(Block, self).__init__()

        self.image = pygame.Surface([20, 15])
        self.image.fill(color)

        self.rect = self.image.get_rect()


class Player(pygame.sprite.Sprite):
    """ This class represents the Player. """

    def __init__(self):
        """ Set up the player on creation. """
        # Call the parent class (Sprite) constructor
        super(Player, self).__init__()

        self.image = pygame.Surface([20, 20])
        self.image.fill(BLUE)

        self.rect = self.image.get_rect()

    def update(self):
        """ Update the player's position. """
        # Set the player position
        self.rect.x = x_coord
        self.rect.y = y_coord


class Bullet(pygame.sprite.Sprite):
    """ This class represents the bullet . """
    def __init__(self):
        # Call the parent class (Sprite) constructor
        super(Bullet, self).__init__()

        self.image = pygame.Surface([10, 3])
        self.image.fill(RED)

        self.rect = self.image.get_rect()

    def update(self):
        """ Move the bullet. """
        self.rect.x += 5

# --- Case defines


def d_left():
    global x_coord
    x_coord -= 5


def d_right():
    global x_coord
    x_coord += 5


def d_up():
    global y_coord
    y_coord -= 5


def d_down():
    global y_coord
    y_coord += 5


def button_a():
    print("Implement shield (disable weapons but make user invincible for n hits) here!")


def button_b():
    # Fire a bullet if the user clicks the mouse button
    bullet = Bullet()
    # Set the bullet so it is where the player is
    bullet.rect.x = player.rect.x+20
    bullet.rect.y = player.rect.y+10
    # Add the bullet to the lists
    all_sprites_list.add(bullet)
    bullet_list.add(bullet)


def button_other():
    print("Button not used.")

wiimote_event = {   0: d_left,
                    1: d_right,
                    2: d_up,
                    3: d_down,
                    4: button_a,
                    5: button_b
                    }

# --- Create the window

# Initialize Pygame
pygame.init()
   
# Set the width and height of the screen [width,height]
screen_width = 1000
screen_height = 700
screen = pygame.display.set_mode([screen_width, screen_height])
  
pygame.display.set_caption("Tiny Space Battles")
  
#Loop until the user clicks the close button.
done = False

# Used to manage how fast the screen updates
clock = pygame.time.Clock()

score = 0

# Current position
x_coord = 10
y_coord = 350

# --- Sprite lists
# This is a list of every sprite. All blocks and the player block as well.
all_sprites_list = pygame.sprite.Group()

# List of each block in the game
block_list = pygame.sprite.Group()

# List of each bullet
bullet_list = pygame.sprite.Group()
# ------

# --- Create the sprites
for i in range(50):
    # This represents a block
    block = Block(BLACK)

    # Set a random location for the block
    block.rect.x = random.randrange(100, screen_width)
    block.rect.y = random.randrange(screen_height)

    # Add the block to the list of objects
    block_list.add(block)
    all_sprites_list.add(block)

# Create a red player block
player = Player()
all_sprites_list.add(player)
# ------

# --- Wiimote control setup
# Count the joysticks the computer has
joystick_count = pygame.joystick.get_count()
if joystick_count == 0:
    # No joysticks!
    print ("No Wiimote found.")
else:
    # Use joystick #0 and initialize it
    my_joystick = pygame.joystick.Joystick(0)
    my_joystick.init()
# ------

while not done:
 
    # ALL EVENT PROCESSING SHOULD GO BELOW THIS COMMENT
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True

        elif event.type == pygame.JOYBUTTONDOWN:
            wiimote_event.get(event.dict['button'], button_other)()

    # ALL EVENT PROCESSING SHOULD GO ABOVE THIS COMMENT
 
    # ALL GAME LOGIC SHOULD GO BELOW THIS COMMENT

    # Call the update() method on all the sprites
    all_sprites_list.update()

    # Calculate mechanics for each bullet
    for bullet in bullet_list:

        # See if it hit a block
        block_hit_list = pygame.sprite.spritecollide(bullet, block_list, True)

        # For each block hit, remove the bullet and add to the score
        for block in block_hit_list:
            bullet_list.remove(bullet)
            all_sprites_list.remove(bullet)
            score += 1
            print(score)

        # Remove the bullet if it flies up off the screen
        if bullet.rect.y < -10:
            bullet_list.remove(bullet)
            all_sprites_list.remove(bullet)

    # If one of the D-pad buttons is still pressed, execute
    for i in xrange(0, 4):  # Iterates from 0 to 3 (not 0 to 4)
        if my_joystick.get_button(i):
            wiimote_event[i]()

    # ALL GAME LOGIC SHOULD GO ABOVE THIS COMMENT    
 
    # ALL CODE TO DRAW SHOULD GO BELOW THIS COMMENT
      
    # First, clear the screen to WHITE. Don't put other drawing commands
    # above this, or they will be erased with this command.
    screen.fill(WHITE)    
 
    # Draw the item at the proper coordinates
    all_sprites_list.draw(screen)
 
    # ALL CODE TO DRAW SHOULD GO ABOVE THIS COMMENT    
 
    pygame.display.flip()
    clock.tick(60)
pygame.quit()
