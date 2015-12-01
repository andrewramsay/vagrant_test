import os

### BASIC SETTINGS

# enable/disable mouse testing
mouse_test = False

# number of lanes (1--6)
nlanes = 6


# how fast the score counter goes up when just driving down the road
score_increment = 0


# show shadow car
show_shadow = False


### NETWORKING 
# udp ports
control_port = 2222
event_port = 3333

# port and address to send feedback events to
fbk_port = 5555
fbk_ip = 'localhost' #"129.27.145.113"



### CONTROL

# speed of car, in seconds to traverse from screen border to car vertically
speed = 4

# mode, can be "integrated" or "direct"
control_mode = "integrated" 

# how fast the integrator increases (integrated mode only) 
control_gain = 2


#how much scaling the input has (direct mode only)
control_scaling = 1

# smoothing (direct control only), larger numbers are smoother
control_smoothing = 1

# how much "snap" the lanes have. Smaller is more snap. Values in 10-100 are good.
# 0 disables snapping entirely.
snappiness = 100


# how much the car shakes as the noise input increases
noise_feedback_level = 0.1

# Mute Sound
mute = False

# Resolution
resolution = (1000,600)
fullscreen = False

# Use 2-lanes objects
bigobjects = True



### Auto add events
level = 5


pymitools_folder = os.path.join('..','pymitools')
