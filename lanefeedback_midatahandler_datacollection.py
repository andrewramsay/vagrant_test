import sys,time,os,random,cPickle, math
import traceback
from socket import *
import pygame, thread, struct
from pygame.locals import *
import numpy
import atexit
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from glutils import *
import yaml
import glskeleton
import config_datacollection as config

# Send data from a UDP socket
# parses using struct.unpack()
class NetworkSend:
    # connect to given port, expect data in format
    # e.g. "!dd" is two doubles
    # "iid" would be two ints and a double
    def __init__(self, port, ip, format):
        self.port = port
        self.ip = ip
        self.socket = socket(AF_INET,SOCK_DGRAM)
        self.socket.setblocking(0)
        self.format = format        
        
        # make sure this socket is closed if we exit!
        atexit.register(self.close)
        
    # receive a packet, if there is one, and return the parsed values
    # returns None if no packets
    # reads all waiting packets (i.e. clears the buffer)
    def send(self, data):        
        print 'sending data', data
        try:
            if type(data) in [list, tuple]:
                datastring = ','.join([str(d) for d in data])
                print 'sending datastring', datastring
                msg = eval('struct.pack(self.format,%s)' % (datastring))
            else:
                msg = struct.pack(self.format, data)            
        except Exception, e:
            print "Data format problem...", e
            
        self.socket.sendto(msg, (self.ip, self.port))
        print data
        
        
        
    # close the connection
    def close(self):
        self.socket.close()

# Receive data from a UDP socket
# parses using struct.unpack()
class NetworkReceive:

    # connect to given port, expect data in format
    # e.g. "!dd" is two doubles
    # "iid" would be two ints and a double
    def __init__(self, port, format):
        self.port = port
        self.socket = socket(AF_INET,SOCK_DGRAM)
        self.socket.setblocking(0)
        self.format = format        
        
        # make sure this socket is closed if we exit!
        atexit.register(self.close)
        # listen to all incoming connections
        self.socket.bind(("0.0.0.0", self.port))
        
    # receive a packet, if there is one, and return the parsed values
    # returns None if no packets
    # reads all waiting packets (i.e. clears the buffer)
    def recv(self):        
        packet, addr = None, None        
        try:
            while 1:
                packet,addr =  self.socket.recvfrom(65535)
        except:
            pass                
        if packet!=None:            
            try:                
                vals = struct.unpack(self.format, packet)                            
##                print self.port, vals
            except:
                print "Data problem..."                
            return vals
        else:            
            return None
        
    # close the connection
    def close(self):
        self.socket.close()

class TokenGenerator(NetworkSend):
    def __init__(self, port):
        NetworkSend.__init__(self, port, 'localhost', '!dd')
        self.running = True
    
    def run(self):
        """ 
        Example TokenGenerator 
        """
        while self.running:
            time.sleep(self.getNextTime())
            self.send(random.choice([2,-2,3,-3,4,5]),0)
    
    def start(self):
        self.running = True
    
    def stop(self):
        self.running = False
            
    def close(self): 
        self.running = False
        NetworkSend.close(self)
    
    def getNextTime(self):
        """
        Specific to this tokenGenerator
        """
        return random.randint(1, 5)
        
# Simple saturating integrator
class IntegratedControl:
    # Init, with the integration rate and maximum absolute value
    def __init__(self, speed, mode="integrated", smoothing = 0,scaling=1, saturation = 1):
        self.reset()
        self.speed = speed
        self.set_smoothing(smoothing)
        self.mode = mode
        self.scaling = scaling
        self.saturation = saturation
        self.delta = 0
        
        
    def set_smoothing(self, smoothing):
        self.smoothing = smoothing
        self.alpha = 1-math.exp(-smoothing)
        
    # integrate a new value with a given time step
    def update(self, val, dt):
        if self.mode=="integrated":
            self.x += dt * val * self.speed
            self.delta = dt * self.speed
        elif self.mode=="direct":
            self.x = (1-self.alpha) * val * self.scaling + (self.alpha) * self.x
            self.delta = self.x - val*self.scaling
            
        
        # check saturation
        if self.x<-self.saturation:
            self.x = -self.saturation
        
        if self.x>self.saturation:
            self.x = self.saturation
        
    # reset the integrator to zero
    def reset(self):
        self.x = 0
        
# Model a series of one-dimensional attractors (second-order springs)
# Each spring has an influence zone defined by a Gaussian (width of Gaussian given by snap)
# k and damping affect the spring parameters
class Snapable:
    def __init__(self, start_x=0, k=60, damping=0.9, snap=1000):
        self.x = start_x
        self.target_x = start_x
        self.k = k
        self.damping = damping
        self.snap = snap
        self.dx =0 
        self.delta = 0
        
    # set the centers of the attractors
    def set_centers(self, centers):    
        self.centers = centers
        
    # set the target value we are trying to acquire (the incoming value)
    def set_target(self, target):
        self.target_x = target
        
    # adjust the snapping level (higher = broader basis functions, less snapping)
    def set_snapping(self, snapping):
        self.snap = snap
        
    # update a new time step
    def update(self, dt):
    
        # don't snap if disabled
        if self.snap==0:
            self.x = self.target_x
            
        # compute influence of each attractor 
        ds = numpy.abs(self.centers-self.target_x)
        n = numpy.exp(-(ds*ds)/(self.snap*self.snap))

        # compute total force on the point
        ddx = 0
        for i in range(len(self.centers)):
            ddx += self.k * (self.centers[i]-self.x) * n[i]        
            
        self.delta = self.target_x - self.x
        
        # integrate
        self.dx = self.dx + ddx*dt
        self.dx = self.dx * self.damping
        self.x = self.x + self.dx*dt
##        self.x = self.target_x

                
        
# Represent a single object on the road
# time: position on the road
# lane: lane of the road
# type: string giving the type of object
# image: image to be rendered for this object
# remove: if this object disappears when collided with
# visible: if this object is visible or not
class Barrier:
    def __init__(self, time, lane, descriptor):
        self.time = time
        self.lane = lane
        self.descriptor = descriptor
        
    
        
        
# Represent a collection of road objects
class BarrierModel:
    def __init__(self, lanes):
        self.lanes = lanes                
        self.lane_data = []                
                
    def add(self, barrier):
        self.lane_data.append(barrier)
        
    # move all the objects "up", check for collisions, and remove
    # objects that have gone offscreen
    def update(self, shift, car_lane, car_height, collision=None, car_length=50):
        kill_list = []
        
        for event in self.lane_data:
            event.time = event.time - shift
            
            # check for collision!
            if event.time<car_height and event.time>car_height-car_length and car_lane >= event.lane and car_lane<=event.lane+event.descriptor.lanespan-1:
##                print (event.lane,event.descriptor.lanespan,car_lane)
                if event.descriptor.collision_remove:
                    kill_list.append(event)
                if collision:
                    collision(event)
                
            # remove off the screen events
            if event.time<-event.descriptor.image.h:
                kill_list.append(event)
                
        # remove the old elements
        for kill in kill_list:            
            self.lane_data.remove(kill)
            
    
        
STATE_WAITING = 0 # gameplay paused
STATE_RUNNING = 1 # car moving on screen
STATE_PLAYING = 2 # collecting points


class BarrierDescriptor:
    def __init__(self, name, descriptor):
        self.__dict__ = descriptor
        self.type = name        
        if descriptor["sound"]:
            self.sound = pygame.mixer.Sound(descriptor["sound"])
        else:
            self.sound = None            
        if descriptor["image"]:
            self.image = GLSprite(descriptor["image"])
        else:
            self.image = None
                            
        #self.points = descriptor["points"]
        #self.lanespan = descriptor["lanespan"]
        #self.visible = descriptor["visible"]
        self.collision_remove = descriptor["collision-remove"]
            

    
class Snapper:

    def load_sounds(self):
        self.lane_sound = pygame.mixer.Sound("lane.wav")       
        self.score_sound = pygame.mixer.Sound("score.wav")
        self.tyre_sound = pygame.mixer.Sound("tyres.wav")
        
                
        
        
    def load_images(self):
        self.lane_image = pygame.image.load("base.png").convert()
        self.verge_image = pygame.image.load("verge.png").convert()
        self.car_sprite = GLSprite("firecar.png")
        
        # set font
        default_font_name = pygame.font.match_font('verdana', 'sans')
        if not default_font_name:           
            self.default_font_name = pygame.font.get_default_font()  
        self.font = pygame.font.Font(default_font_name, 64)
        
        
    def __init__(self, token_generator=None):
        self.skeleton = glskeleton.GLSkeleton(draw_fn=self.draw, tick_fn=self.tick, event_fn=self.event, w=config.resolution[0], h=config.resolution[1])
        
        self.control = IntegratedControl(speed=config.control_gain, smoothing=config.control_smoothing, mode=config.control_mode, scaling=config.control_smoothing)
        
        self.barrier_descriptors = {}
        f = open("barriers.yaml")
        yaml_barrier_descriptors = yaml.load(f)
        
        for barrier in yaml_barrier_descriptors:            
            name = barrier.keys()[0]
            entry = barrier[name]
            self.barrier_descriptors[name] = BarrierDescriptor(name,entry)
        f.close()
        
        self.token_generator = token_generator
        
        # connect to network ports
        # self.receiver = NetworkReceive(config.control_port, "!dddddd")
        self.control_receiver = NetworkReceive(config.event_port, "!ii")        
        self.fbk_port = NetworkSend(config.fbk_port, config.fbk_ip, "!c")
        
        self.car = Snapable(snap=config.snappiness)
        
        self.load_images()

        self.load_sounds()
                
        self.noise = 0
        
        self.tyre_level = 0       
        self.played_score = 0
        self.skeleton.fps = 60
        self.lane_width = self.lane_image.get_width()
        self.nlanes = config.nlanes
        
        self.barriers = BarrierModel(self.nlanes)
        edge = (self.skeleton.w-self.nlanes*self.lane_width)/2
                
        centers = [edge+self.lane_width/2+i*self.lane_width for i in range(self.nlanes)]

        self.edge = edge
        self.car.set_centers(numpy.array(centers))
        
        self.control_value = 0
        self.position = 0
        self.control_mode = 0
        self.info = 0

        self.trialnumber = 0
        self.maxscore = 0
        
        self.scoring = False
        self.speed = 4
        self.time_to_reach_end = config.speed
        
        self.car_jump = 0
        self.car_swivel = 0
        self.fps = 60
        self.car_lane = 0
        self.score = 0
        self.score_deflection = 0
        self.state = STATE_WAITING
        self.startline_timer = 0
    
        self.create_back_surface()

		with open("message.txt", "r") as f:
			self.message = f.read()
			self.message = self.message.strip()
    
    def run(self):
        self.skeleton.main_loop()
        
        
    def quit(self):
        pass
        
    def event(self, event):
        # update values of current controllers    
        if event.type == KEYUP:
            if event.key == K_SPACE:
                if self.state == STATE_PLAYING:
                    self.endPlay()
                else:
                    self.startPlay()
                
            # key events
            # if config.mouse_test:
            if event.key>=K_0 and event.key<=K_9:
                self.control_msg(event.key-K_0)
    
    def endPlay(self):
        self.add_object("finishline", lane=0)
        self.state = STATE_RUNNING
        self.startline_timer = 0
        if self.token_generator:
            self.token_generator.stop()
        
    def startPlay(self):
        self.state = STATE_PLAYING
        self.add_object("startline", lane=0)
        self.startline_timer = 0
        # self.control_msg(1)
        if self.token_generator: 
            self.token_generator.start()
            thread.start_new_thread(self.token_generator.run, ())
                
    def get_lane(self, lane):
        return self.edge+lane*self.lane_width
    
    
    def create_back_surface(self):
        self.back_surface = pygame.Surface((self.skeleton.w, self.skeleton.h+self.lane_image.get_height()*2))
        for j in range(22):
            y = j*self.lane_image.get_height()
            self.back_surface.blit(self.verge_image, (self.edge-128,y), (0,0,256,128))
            self.back_surface.blit(self.verge_image, (self.edge-128+self.nlanes*self.lane_width,y), (128,0,256,128))            
            for i in range(self.nlanes):
                x = self.get_lane(i)
                self.back_surface.blit(self.lane_image, (x,y))
        self.background_sprite = GLSprite(surface=self.back_surface, split=False)


    def show_info_text(self, text):
        glEnable(GL_TEXTURE_2D)        
        text_surface = self.font.render(text, True, (255,255,255))
        text_sprite = GLSprite(surface = text_surface)
                
        glColor4f(0.2,0.6,0.9,1)
        glPushMatrix()
        glTranslatef((self.skeleton.w)/2,self.skeleton.h/2, 0)
        glScalef(0.5*text_sprite.w, -0.5*text_sprite.h, 1)
        glCallList(text_sprite.sprite)
        glPopMatrix()
        text_sprite.delete()

        
    def draw_feedback_bar(self, text, bci, js):
        glDisable(GL_TEXTURE_2D)
        
        c = 200
        bci = bci*2
        js = js*2
        dl = self.skeleton.h-50
        du = dl-c-50
        a = 1.1
        
        # BCI:
        glColor4f(bci/200,1-bci/200,0,1)
        glBegin(GL_QUADS)
        if self.control_mode == 1:
            glVertex3f(0,dl-c*a+bci*a,0)
            glVertex3f(self.skeleton.w/12*a,dl-c*a+bci*a,0)
            glVertex3f(self.skeleton.w/12*a,dl,0)
            glVertex3f(0,dl,0)
        else:
            glVertex3f(0,dl-c+bci,0)
            glVertex3f(self.skeleton.w/12,dl-c+bci,0)
            glVertex3f(self.skeleton.w/12,dl,0)
            glVertex3f(0,dl,0)
        glEnd()

        # JS:
        glColor4f(js/200,1-js/200,0,1)
        glBegin(GL_QUADS)
        if self.control_mode == 2:
            glVertex3f(0,du-c*a+js*a,0)
            glVertex3f(self.skeleton.w/12*a,du-c*a+js*a,0)
            glVertex3f(self.skeleton.w/12*a,du,0)
            glVertex3f(0,du,0)
        else:
            glVertex3f(0,du-c+js,0)
            glVertex3f(self.skeleton.w/12,du-c+js,0)
            glVertex3f(self.skeleton.w/12,du,0)
            glVertex3f(0,du,0)
        glEnd()

        # BCI:
        glColor4f(1,1,1,1)
        if self.control_mode == 1:
            glLineWidth (3.0)
        else:
            glLineWidth (2.0)
        glBegin(GL_LINE_LOOP)
        if self.control_mode == 1:
            glVertex3f(0,dl,0)
            glVertex3f(self.skeleton.w/12*a,dl,0)
            glVertex3f(self.skeleton.w/12*a,dl-c*a,0)
            glVertex3f(0,dl-c*a,0)
        else:
            glVertex3f(0,dl,0)
            glVertex3f(self.skeleton.w/12,dl,0)
            glVertex3f(self.skeleton.w/12,dl-c,0)
            glVertex3f(0,dl-c,0)
        glEnd()

        # JS:
        glColor4f(1,1,1,1)
        if self.control_mode == 2:
            glLineWidth (3.0)
        else:
            glLineWidth (2.0)
        glBegin(GL_LINE_LOOP)
        if self.control_mode == 2:
            glVertex3f(0,du,0)
            glVertex3f(self.skeleton.w/12*a,du,0)
            glVertex3f(self.skeleton.w/12*a,du-c*a,0)
            glVertex3f(0,du-c*a,0)
        else:
            glVertex3f(0,du,0)
            glVertex3f(self.skeleton.w/12,du,0)
            glVertex3f(self.skeleton.w/12,du-c,0)
            glVertex3f(0,du-c,0)
        glEnd()
        
        # BCI
        glEnable(GL_TEXTURE_2D)
        text_surface = self.font.render("BCI", True, (255,255,255))
        text_sprite = GLSprite(surface = text_surface)
        glPushMatrix()
        if self.control_mode == 1:
            glTranslatef(self.skeleton.w/24*a,dl-0.2*c, 0)
            glColor4f(1,1,1,1)
            glScalef(1.2*text_sprite.w/2, -1.2*text_sprite.h/2, 1)
        else:
            glTranslatef(self.skeleton.w/24,dl-0.2*c, 0)
            glColor4f(0.5,0.5,0.5,0.5)
            glScalef(text_sprite.w/2, -text_sprite.h/2, 1)
        glCallList(text_sprite.sprite)
        glPopMatrix()
        text_sprite.delete()

        # JS
        glEnable(GL_TEXTURE_2D)
        text_surface = self.font.render("JS", True, (255,255,255))
        text_sprite = GLSprite(surface = text_surface)
        glPushMatrix()
        if self.control_mode == 2:
            glTranslatef(self.skeleton.w/24*a,du-0.2*c, 0)
            glColor4f(1,1,1,1)
            glScalef(1.2*text_sprite.w/2, -1.2*text_sprite.h/2, 1)
        else:
            glTranslatef(self.skeleton.w/24,du-0.2*c, 0)
            glColor4f(0.5,0.5,0.5,0.5)
            glScalef(text_sprite.w/2, -text_sprite.h/2, 1)
        glCallList(text_sprite.sprite)
        glPopMatrix()
        text_sprite.delete()

            
        
    def draw(self):
        
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glLoadIdentity()
        
        glPushMatrix()
        glScalef(1,-1,1)
        glTranslatef(0,-self.skeleton.h,0)
        
        glPushMatrix()
        glColor4f(1,1,1,1)
        
        glTranslatef(self.back_surface.get_width()/2, self.skeleton.h/2 + self.position % 128 , 0)
        glScalef(self.back_surface.get_width(), self.back_surface.get_height(), 1)       
        glCallList(self.background_sprite.sprite)
        
        glPopMatrix()
        
        self.car_swivel *= 0.95
        self.car_jump *= 0.9
        
        # car (with shake)
        offx = random.gauss(0, self.noise) * config.noise_feedback_level
        offx += random.gauss(0, self.car_swivel)
        
        
        
        dir = (math.atan2(self.car.dx/500.0,1.0)/math.pi)*180.0
        
        #  barriers
        for barrier in self.barriers.lane_data:
            x = self.get_lane(barrier.lane)# + (self.lane_width*barrier.descriptor.lanespan-barrier.descriptor.image.w)/2
            if barrier.descriptor.image.w < self.lane_width:
                x += (self.lane_width-barrier.descriptor.image.w)/2
                
            # draw visible barriers
            if barrier.descriptor.visible:
                glPushMatrix()       
                glTranslatef(x+barrier.descriptor.image.w/2,self.skeleton.h-barrier.time,1)            
                glScalef(barrier.descriptor.image.w,-barrier.descriptor.image.h,1)
                glCallList(barrier.descriptor.image.sprite)
                glPopMatrix()
            
        
        # draw car
        
        #shadow car
        
        if config.show_shadow:
            idelta = math.tanh(self.control.delta*20)                
            offset = self.car.x - idelta * self.lane_width        
            glColor4f(0,0,0,0.6)
            glPushMatrix()       
            glTranslatef(offset,self.skeleton.h-400,1)        
            glScalef(self.car_sprite.w,self.car_sprite.h,1)
            glCallList(self.car_sprite.sprite)
            glPopMatrix()
            
        # real car
        glColor4f(1,1,1,1)
        glPushMatrix()       
        glTranslatef(self.car.x,self.skeleton.h-200,1)
        glRotatef(dir+offx, 0, 0, 1)
        glScalef(self.car_sprite.w*(1+self.car_jump),self.car_sprite.h*(1+self.car_jump),1)
        glCallList(self.car_sprite.sprite)
        glPopMatrix()

        
        ##waiting text
        if self.state==STATE_WAITING:
            self.draw_feedback_bar("Ready!",0,0)            
        else:
            self.draw_points()
	    if self.message:
		print self.message
		self.show_info_text(self.message);
            if self.control_mode == 1:
                self.draw_feedback_bar("BCI",self.bcibar,self.jsbar)
            elif self.control_mode == 2:
                self.draw_feedback_bar("JS",self.bcibar,self.jsbar)
            if self.info == 1:
                self.show_info_text("Trying to switch from Joystick to BCI control!")
            elif self.info == 2:
                self.show_info_text("Trying to switch from BCI to Joystick control!")
            elif self.info == 3:
                self.show_info_text("Switching control mode!")
            elif self.info == 4:
                self.show_info_text("Switching from BCI to Joystick control!")
        
        glPopMatrix()
        
    def draw_points(self):
        ## points
        
        x = 80
        y = self.skeleton.h-50-self.score_deflection
        self.score_deflection *= 0.99
        glEnable(GL_TEXTURE_2D)
        
        text_surface = self.font.render("[%d/%d]" % (int(self.played_score), int(self.maxscore)), True, (255,255,255))
        text_sprite = GLSprite(surface = text_surface)
                
        glColor4f(0.7,1,0.4,1)
        glPushMatrix()
        glTranslatef((self.skeleton.w)/2,self.skeleton.h-60, 0)
        glScalef(text_sprite.w, -text_sprite.h, 1)
        glCallList(text_sprite.sprite)
        glPopMatrix()
        text_sprite.delete()

        glEnable(GL_TEXTURE_2D)
        
        text_surface = self.font.render("# %d" % int(self.trialnumber), True, (255,255,255))
        text_sprite = GLSprite(surface = text_surface)
                
        glColor4f(0.7,1,0.4,1)
        glPushMatrix()
        glTranslatef(11*self.skeleton.w/12,self.skeleton.h-60, 0)
        glScalef(text_sprite.w, -text_sprite.h, 1)
        glCallList(text_sprite.sprite)
        glPopMatrix()
        text_sprite.delete()
        
        
    # deal with the collision between the car and an object
    def collide(self, event):
        self.score += event.descriptor.points
        if event.descriptor.sound:
            if config.mute == False:
                event.descriptor.sound.play()
            
        if event.descriptor.jump:
            self.car_jump = event.descriptor.jump
        
        if event.descriptor.swivel:
            self.car_swivel = event.descriptor.swivel

        if event.descriptor.msg=="coin":            
            self.fbk_port.send("1")

        if event.descriptor.msg=="barrier":            
            self.fbk_port.send("2")
        
        if event.descriptor.msg=="start":            
            self.scoring = True
            self.trialnumber += 1;
            self.maxscore = 0
            self.score = 0
                        
        if event.descriptor.msg=="finish":
            self.scoring = False
            print 'Score for last trial %d/%d' % (self.score, self.maxscore)
            # self.maxscore += 6;
            
        if self.score<0:
            self.score = 0
    
    # add an object to the road 
    # takes a string type, and the lane to add it into (None = random lane)
    def add_object(self, obj_type, lane=None, visible=True):
        y = self.skeleton.h+32
        if lane==None:
            lane = random.randint(0,self.nlanes-1)
        
        if obj_type.find('coin') >= 0:
            self.maxscore += 1

        
        self.barriers.add(Barrier(y, lane, self.barrier_descriptors[obj_type]))
        
        
    
    
    # respond to control events from the network
    # add objects to the road when messages are received
    def handle_network_events(self):
        control = self.control_receiver.recv()
        if control:
            self.control_msg(control[0])
            self.log_msg = [0,0,0,0]
            if control[1]:
                self.log_msg[control[1]-1] = 1
                print 'log msg index',control[1]-1
        
        
    # put the car back in the middle
    def reposition_car(self):
        self.control.x = 0
    
    def control_msg(self, control):
        # print 'hi control', control
        if control and self.startline_timer > 1:
            if config.bigobjects == True:
                if control==3:
                    self.add_object("bigcoin", lane=0)
                if control==-3:
                    self.add_object("bigcoin", lane=0)
                    self.add_object("bigbarrier", lane=self.nlanes-2)
                if control==2:                
                    self.add_object("bigcoin", lane=self.nlanes-2)
                if control==-2:                
                    self.add_object("bigcoin", lane=self.nlanes-2)
                    self.add_object("bigbarrier", lane=0)
                if control==4:
                    self.add_object("bigbarrier", lane=0)
                if control==5:                
                    self.add_object("bigbarrier", lane=self.nlanes-2)
            else:
                if control==3:
                    self.add_object("coin", lane=random.randint(0,self.nlanes/2))
                if control==-3:
                    self.add_object("coin", lane=random.randint(0,self.nlanes/2))
                    self.add_object("barrier", lane=self.nlanes-1)
                if control==2:                
                    self.add_object("coin", lane=random.randint(self.nlanes/2,self.nlanes-1))
                if control==-2:                
                    self.add_object("coin", lane=random.randint(self.nlanes/2,self.nlanes-1))
                    self.add_object("barrier", lane=0)
                if control==4:
                    self.add_object("barrier", lane=0)
                if control==5:                
                    self.add_object("barrier", lane=self.nlanes-1)
            if control==6:                
                self.add_object("startline", lane=0)
            if control==7:                
                self.endPlay()
            if control==1:
                print "Resetting Score"
                self.score=0
                self.trialnumber = 0
                self.maxscore = 0
                self.reposition_car()
                
  
    # update the tyre squealing sound
    def update_tyres(self):
        if self.noise>0.5:
                self.tyre_level += self.noise                            
        if self.tyre_level>2.0 and self.tyre_sound.get_num_channels()==0:
            if config.mute == False:
                self.tyre_sound.play()                
        if self.tyre_level<0.5 and self.tyre_sound.get_num_channels()>0:
            if config.mute == False:
                self.tyre_sound.stop()            
        self.tyre_level = self.tyre_level *0.85
    
    
    # update the score
    def update_score(self):
        if not self.scoring:
            
            self.score = self.played_score
            return
            
        
        if self.played_score>self.score:
            self.played_score = self.score
            
        if int(self.played_score)<int(self.score):                 
                new_score = self.played_score+0.5
                #if int(new_score)!=int(self.played_score):
                #    self.score_sound.play()
                self.score_deflection = 30
                self.played_score = self.score
                
    
    
    
    def add_random_obstacles(self):
         if random.random()<0.02:
                if random.random()<0.5:
                    self.add_object("coin")                   
                else:
                    self.add_object("barrier")
        
        
    def update_speed(self, dt):
        # compute how fast we are moving
        if dt > 0:
            fps = 1.0/dt
        else:
            fps = 0
        self.fps = 0.9*self.fps + 0.1*fps
        y_resolution = self.skeleton.h-200
        
        # increment in position is height/frame rate
        # for 1 screen per second
        # so divide by time in seconds for screen traversal
        self.speed = (y_resolution/self.fps) / config.speed
        
        
    def tick(self, dt):
        # print 'speed', dt
        dt = dt/1000.0

        self.update_speed(dt)
        
        
    
        if self.state==STATE_WAITING:
            pass
        
        if self.state == STATE_PLAYING:
            self.startline_timer += dt
            
        if self.state in [STATE_RUNNING, STATE_PLAYING]:
            
                
            new_lane = 0
            # what lane is the car in?
            for i in range(self.nlanes):
                left = self.get_lane(i)
                right = left + self.lane_width
                if self.car.x>=left and self.car.x<right:
                    new_lane = i
                                   

            if new_lane!=self.car_lane:
                    self.car_lane = new_lane
                    if config.mute == False:
                        self.lane_sound.play()
                    
           

            self.handle_network_events()

            ##########################################################
            # LOADING THE DATA HERE:
            ##########################################################
            # new_data = self.receiver.recv()
            #             if new_data:
            #                 lda, noise, bcibar, jsbar, mode, info =  new_data
            #                 self.control_value = lda
            #                 self.noise = math.exp(noise/2)
            #                 self.bcibar = bcibar
            #                 self.jsbar = jsbar
            #                 self.control_mode = mode
            #                 self.info = info
            
            self.control_value = random.random()#new_data[0]
            print 'val', self.control_value
            self.control_value = self.control_value*2 - 1
                
            self.update_tyres()
            
            self.control.update(self.control_value, dt)

            if config.mouse_test:
                x,y = pygame.mouse.get_pos()
                self.control_value = ((x-self.skeleton.w/2)/float(self.skeleton.w*2))
          
            self.score += config.score_increment * self.speed
            
            # convert -1 -- 1 to screen co-ordinates
##            pos = self.control.x*self.skeleton.w/2+self.skeleton.w/2
            # pos = middle of the screen +- input * lanes left/right
            pos = self.skeleton.w/2 + self.control.x * self.lane_width * config.nlanes/2
##            print pos
            
            
            self.car.set_target(pos)
            self.car.update(dt)
            self.position = self.position + self.speed
            self.barriers.update(self.speed, self.car_lane, car_height = 200+32, collision=self.collide)
            
               
            self.update_score()
            
            
if __name__ == "__main__":
    # start sending tokens
    tokenGenerator = TokenGenerator(config.event_port)
    
    # simulate pyff for rapid testing
    s = Snapper(token_generator=tokenGenerator)
    s.run()
    
    tokenGenerator.close()
    time.sleep(0.1)
    
    print 'Exit gracefully'
        
