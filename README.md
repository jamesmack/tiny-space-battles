tiny-space-battles
=========================

## About
This is my final project for the CENG 356 class at the University of Victoria (Fall 2014, taught by Michael Liu). The goal was to create something that used client-server interactions to communicate Wiimote data. 

## Installation and setup
1. Install [Python](https://www.python.org/downloads/) 2.7.x. Version 2.7.8 was used for development.
2. Install [PyGame](http://www.pygame.org/download.shtml) (or from [source](https://bitbucket.org/pygame/pygame/src)). Version 1.9.2a was used for development.
3. Install [PodSixNet](http://mccormick.cx/projects/PodSixNet/). Release 78 was used for development. 
4. Optionally, install a HID driver for your Wiimote. [WJoy](https://code.google.com/p/wjoy/) was used for development (Mac OS X only).

## To Play
1. Start a server instance
2. Start two client instances
3. Control your ship with the following commands:
  * Keyboard
    * Fire - space key
    * Shield - . (period key)
    * Move up - w
    * Move left - a 
    * Move down - s
    * Move right - d
    * Rotate ccw - q
    * Rotate cw - e
  * Wiimote
    * Fire - B
    * Shield - A
    * Rotate cw, ccw - D-pad right or up, D-pad left or down
  * Nunchuck
    * Fire - Z
    * Shield - C
    * Joystick - move

## Credits
* [Starship sprites](http://millionthvector.blogspot.ca/p/free-sprites.html)
* [Space background](http://opengameart.org/content/space)
