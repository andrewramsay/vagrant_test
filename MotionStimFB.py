import sys,time,os,random,cPickle, math
import traceback, socket
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
import config


# Receive data from a UDP socket
# parses using struct.unpack()
class NetworkSend:

    # connect to given port, expect data in format
    # e.g. "!dd" is two doubles
    # "iid" would be two ints and a double
    def __init__(self, port, ip, format):
        self.port = port
        self.ip = ip
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.socket.setblocking(0)
        self.format = format        
        
        # make sure this socket is closed if we exit!
        atexit.register(self.close)
        
    # receive a packet, if there is one, and return the parsed values
    # returns None if no packets
    # reads all waiting packets (i.e. clears the buffer)
    def send(self, data):        
        try:
            msg = struct.pack(self.format, data)            
        except:
            print "Data format problem..."
            
        self.socket.sendto(msg, (self.ip, self.port))
        
        
        
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
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
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
        
STATE_WAITING = 0
STATE_RUNNING = 1

class Snapper:

##    def load_sounds(self):
##        self.lane_sound = pygame.mixer.Sound("lane.wav")       
##        self.score_sound = pygame.mixer.Sound("score.wav")
##        self.tyre_sound = pygame.mixer.Sound("tyres.wav")
        
                
        
        
    def load_images(self):
        self.background_image = pygame.image.load("background.png").convert()
##        self.verge_image = pygame.image.load("verge.png").convert()
##        self.car_sprite = GLSprite("taxi.png")
        
        # set font
        default_font_name = pygame.font.match_font('verdana', 'sans')
        if not default_font_name:           
            self.default_font_name = pygame.font.get_default_font()  
        self.font = pygame.font.Font(default_font_name, 64)
        
        
    def __init__(self):
        self.skeleton = glskeleton.GLSkeleton(draw_fn = self.draw, tick_fn = self.tick, event_fn = self.event)
##        self.control = IntegratedControl(speed=config.control_gain, smoothing=config.control_smoothing, mode=config.control_mode, scaling=config.control_smoothing)
        
##        self.barrier_descriptors = {}
##        f = open("barriers.yaml")
##        yaml_barrier_descriptors = yaml.load(f)
        
##        for barrier in yaml_barrier_descriptors:            
##            name = barrier.keys()[0]
##            entry = barrier[name]
##            self.barrier_descriptors[name] = BarrierDescriptor(name,entry)
##        f.close()
        
        
        
        # connect to network ports
        self.receiver = NetworkReceive(config.control_port, "!dddd")
        self.control_receiver = NetworkReceive(config.event_port, "!d")        
        self.fbk_port = NetworkSend(config.fbk_port, config.fbk_ip, "!c")
        
        
##        self.car = Snapable(snap=config.snappiness)
        
        self.load_images()

        self.background_width = self.background_image.get_width()
        edge = 0
        self.edge = edge
        
        self.active_mode = 1
        self.JS_value = 0
        self.lock_state = 1
        self.orthosis_angle = 0

        self.state = STATE_WAITING
        
        self.create_back_surface()
        self.skeleton.main_loop()
        
        
    def quit(self):
        self.receiver.close()
        
        
    def event(self, event):
        if event.type == KEYUP:
            if event.key == K_SPACE:
                self.state = STATE_RUNNING
                
            # key events
            if config.mouse_test:
                if event.key>=K_0 and event.key<=K_9:
                    self.control_msg(event.key-K_0)
                    
                
##    def get_lane(self, lane):
##        return self.edge+lane*self.lane_width
    
    
    def create_back_surface(self):
        self.back_surface = pygame.Surface((self.skeleton.w, self.skeleton.h+self.background_image.get_height()*2))
##        for j in range(22):
##            y = j*self.lane_image.get_height()
##            self.back_surface.blit(self.verge_image, (self.edge-128,y), (0,0,256,128))
##            self.back_surface.blit(self.verge_image, (self.edge-128+self.nlanes*self.lane_width,y), (128,0,256,128))            
##            for i in range(self.nlanes):
##                x = self.get_lane(i)
##                self.back_surface.blit(self.lane_image, (x,y))
        self.back_surface.blit(self.background_image, (self.edge,self.skeleton.h/2), (0,0,256,128))
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

        
    def draw_feedback_bar(self, active_mode, JS_value, lock_state, angle):
        glDisable(GL_TEXTURE_2D)
        
        ROM = (self.skeleton.w/2 - 5*self.skeleton.w/16)/100.00
##        ROM = 192.00/100.00
##        print ROM

        #General Frame
        glColor4f(1,1,1,1)
        glLineWidth (2.0)
        glBegin(GL_LINE_LOOP)
        glVertex3f(self.skeleton.w/4,self.skeleton.h/4,0)
        glVertex3f(3*self.skeleton.w/4,self.skeleton.h/4,0)
        glVertex3f(3*self.skeleton.w/4,3*self.skeleton.h/4,0)
        glVertex3f(self.skeleton.w/4,3*self.skeleton.h/4,0)
        glEnd()

        #Frame for Arm
        if active_mode == 1:
            glColor4f(0,1,0,1)
            glLineWidth (5.0)
        else:
            glColor4f(1,1,1,0.5)
            glLineWidth (2.0)
        glBegin(GL_LINE_LOOP)
        glVertex3f(5*self.skeleton.w/16,5*self.skeleton.h/16,0)
        glVertex3f(7*self.skeleton.w/16,5*self.skeleton.h/16,0)
        glVertex3f(7*self.skeleton.w/16,7*self.skeleton.h/16,0)
        glVertex3f(5*self.skeleton.w/16,7*self.skeleton.h/16,0)
        glEnd()

        #Frame for Hand
        if active_mode == 2:
            glColor4f(0,1,0,1)
            glLineWidth (5.0)
        else:
            glColor4f(1,1,1,0.5)
            glLineWidth (2.0)
        glBegin(GL_LINE_LOOP)
        glVertex3f(9*self.skeleton.w/16,5*self.skeleton.h/16,0)
        glVertex3f(11*self.skeleton.w/16,5*self.skeleton.h/16,0)
        glVertex3f(11*self.skeleton.w/16,7*self.skeleton.h/16,0)
        glVertex3f(9*self.skeleton.w/16,7*self.skeleton.h/16,0)
        glEnd()

        #Frame for Pause
        if active_mode == 3:
            glColor4f(0,1,0,1)
            glLineWidth (5.0)
        else:
            glColor4f(1,1,1,0.5)
            glLineWidth (2.0)
        glBegin(GL_LINE_LOOP)
        glVertex3f(7*self.skeleton.w/16,5*self.skeleton.h/16,0)
        glVertex3f(9*self.skeleton.w/16,5*self.skeleton.h/16,0)
        glVertex3f(9*self.skeleton.w/16,7*self.skeleton.h/16,0)
        glVertex3f(7*self.skeleton.w/16,7*self.skeleton.h/16,0)
        glEnd()

        # Draw FB for Arm, Hand, or Pause state:
        if active_mode < 4:
            glEnable(GL_TEXTURE_2D)
            text_surface = self.font.render("Arm", True, (255,255,255))
            text_sprite = GLSprite(surface = text_surface)
            glPushMatrix()
            glTranslatef(3*self.skeleton.w/8,3*self.skeleton.h/8, 0)
            if active_mode == 1:
                glColor4f(0,1,0,1)
                glScalef(1.2*text_sprite.w/2, -1.2*text_sprite.h/2, 1)
            else:
                glColor4f(0.5,0.5,0.5,0.5)
                glScalef(text_sprite.w/2, -text_sprite.h/2, 1)
            glCallList(text_sprite.sprite)
            glPopMatrix()
            text_sprite.delete()

            glEnable(GL_TEXTURE_2D)
            text_surface = self.font.render("Pause", True, (255,255,255))
            text_sprite = GLSprite(surface = text_surface)
            glPushMatrix()
            glTranslatef(self.skeleton.w/2,3*self.skeleton.h/8, 0)
            if active_mode == 3:
                glColor4f(0,1,0,1)
                glScalef(1.2*text_sprite.w/2, -1.2*text_sprite.h/2, 1)
            else:
                glColor4f(0.5,0.5,0.5,0.5)
                glScalef(text_sprite.w/2, -text_sprite.h/2, 1)
            glCallList(text_sprite.sprite)
            glPopMatrix()
            text_sprite.delete()

            glEnable(GL_TEXTURE_2D)
            text_surface = self.font.render("Hand", True, (255,255,255))
            text_sprite = GLSprite(surface = text_surface)
            glPushMatrix()
            glTranslatef(5*self.skeleton.w/8,3*self.skeleton.h/8, 0)
            if active_mode == 2:
                glColor4f(0,1,0,1)
                glScalef(1.2*text_sprite.w/2, -1.2*text_sprite.h/2, 1)
            else:
                glColor4f(0.5,0.5,0.5,0.5)
                glScalef(text_sprite.w/2, -text_sprite.h/2, 1)
            glCallList(text_sprite.sprite)
            glPopMatrix()
            text_sprite.delete()


        # JS Bar: range from -100 to +100

        glColor4f(1,1,1,1)
        glLineWidth (2.0)
        glBegin(GL_LINE_LOOP)
        glVertex3f(5*self.skeleton.w/16,9*self.skeleton.h/16,0)
        glVertex3f(11*self.skeleton.w/16,9*self.skeleton.h/16,0)
        glVertex3f(11*self.skeleton.w/16,11*self.skeleton.h/16,0)
        glVertex3f(5*self.skeleton.w/16,11*self.skeleton.h/16,0)
        glEnd()
        
        glColor4f(0,1,0,1)
        glBegin(GL_QUADS)
        glVertex3f(self.skeleton.w/2+JS_value*ROM,9*self.skeleton.h/16,0)
        glVertex3f(self.skeleton.w/2,9*self.skeleton.h/16,0)
        glVertex3f(self.skeleton.w/2,11*self.skeleton.h/16,0)
        glVertex3f(self.skeleton.w/2+JS_value*ROM,11*self.skeleton.h/16,0)
        glEnd()
##
##        # JS:
##        glColor4f(js/200,1-js/200,0,1)
##        glBegin(GL_QUADS)
##        if self.control_mode == 2:
##            glVertex3f(0,du-c*a+js*a,0)
##            glVertex3f(self.skeleton.w/12*a,du-c*a+js*a,0)
##            glVertex3f(self.skeleton.w/12*a,du,0)
##            glVertex3f(0,du,0)
##        else:
##            glVertex3f(0,du-c+js,0)
##            glVertex3f(self.skeleton.w/12,du-c+js,0)
##            glVertex3f(self.skeleton.w/12,du,0)
##            glVertex3f(0,du,0)
##        glEnd()
##
##        # BCI:
##        glColor4f(1,1,1,1)
##        if self.control_mode == 1:
##            glLineWidth (3.0)
##        else:
##            glLineWidth (2.0)
##        glBegin(GL_LINE_LOOP)
##        if self.control_mode == 1:
##            glVertex3f(0,dl,0)
##            glVertex3f(self.skeleton.w/12*a,dl,0)
##            glVertex3f(self.skeleton.w/12*a,dl-c*a,0)
##            glVertex3f(0,dl-c*a,0)
##        else:
##            glVertex3f(0,dl,0)
##            glVertex3f(self.skeleton.w/12,dl,0)
##            glVertex3f(self.skeleton.w/12,dl-c,0)
##            glVertex3f(0,dl-c,0)
##        glEnd()
##
##        # JS:
##        glColor4f(1,1,1,1)
##        if self.control_mode == 2:
##            glLineWidth (3.0)
##        else:
##            glLineWidth (2.0)
##        glBegin(GL_LINE_LOOP)
##        if self.control_mode == 2:
##            glVertex3f(0,du,0)
##            glVertex3f(self.skeleton.w/12*a,du,0)
##            glVertex3f(self.skeleton.w/12*a,du-c*a,0)
##            glVertex3f(0,du-c*a,0)
##        else:
##            glVertex3f(0,du,0)
##            glVertex3f(self.skeleton.w/12,du,0)
##            glVertex3f(self.skeleton.w/12,du-c,0)
##            glVertex3f(0,du-c,0)
##        glEnd()
##        
##        # BCI
##        glEnable(GL_TEXTURE_2D)
##        text_surface = self.font.render("BCI", True, (255,255,255))
##        text_sprite = GLSprite(surface = text_surface)
##        glPushMatrix()
##        if self.control_mode == 1:
##            glTranslatef(self.skeleton.w/24*a,dl-0.2*c, 0)
##            glColor4f(1,1,1,1)
##            glScalef(1.2*text_sprite.w/2, -1.2*text_sprite.h/2, 1)
##        else:
##            glTranslatef(self.skeleton.w/24,dl-0.2*c, 0)
##            glColor4f(0.5,0.5,0.5,0.5)
##            glScalef(text_sprite.w/2, -text_sprite.h/2, 1)
##        glCallList(text_sprite.sprite)
##        glPopMatrix()
##        text_sprite.delete()
##
##        # JS
##        glEnable(GL_TEXTURE_2D)
##        text_surface = self.font.render("JS", True, (255,255,255))
##        text_sprite = GLSprite(surface = text_surface)
##        glPushMatrix()
##        if self.control_mode == 2:
##            glTranslatef(self.skeleton.w/24*a,du-0.2*c, 0)
##            glColor4f(1,1,1,1)
##            glScalef(1.2*text_sprite.w/2, -1.2*text_sprite.h/2, 1)
##        else:
##            glTranslatef(self.skeleton.w/24,du-0.2*c, 0)
##            glColor4f(0.5,0.5,0.5,0.5)
##            glScalef(text_sprite.w/2, -text_sprite.h/2, 1)
##        glCallList(text_sprite.sprite)
##        glPopMatrix()
##        text_sprite.delete()

            
        
    def draw(self):
        
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glLoadIdentity()
        glScalef(1,-1,1)
        glTranslatef(0,-self.skeleton.h,0)
        glPushMatrix()
        glColor4f(1,1,1,1)
        
##        glTranslatef(self.back_surface.get_width()/2, self.skeleton.h/2 + self.position % 128 , 0)
        glScalef(self.back_surface.get_width(), self.back_surface.get_height(), 1)       
        glCallList(self.background_sprite.sprite)
        
        glPopMatrix()

##        ##waiting text
        if self.state==STATE_WAITING:
            self.draw_feedback_bar(3,0,0,0)
            
        else:
            self.draw_feedback_bar(self.active_mode, self.JS_value, self.lock_state, self.orthosis_angle)
##            self.draw_points()
##            if self.control_mode == 1:
##                self.draw_feedback_bar("BCI",self.bcibar,self.jsbar)
##                print "trying"
##            elif self.control_mode == 2:
##                self.draw_feedback_bar("JS",self.bcibar,self.jsbar)
##            if self.info == 1:
##                self.show_info_text("Trying to switch from Joystick to BCI control!")
##            elif self.info == 2:
##                self.show_info_text("Trying to switch from BCI to Joystick control!")
##            elif self.info == 3:
##                self.show_info_text("Switching control mode!")
##            elif self.info == 4:
##                self.show_info_text("Switching from BCI to Joystick control!")
            
 
    
    
    # respond to control events from the network
    # add objects to the road when messages are received
    def handle_network_events(self):
        control = self.control_receiver.recv()
        if control:
            self.control_msg(control[0])
  
        
        
    def tick(self, dt):

##        self.update_speed(dt)
        
        
    
        if self.state==STATE_WAITING:
            pass
        if self.state==STATE_RUNNING:
                
           

            self.handle_network_events()

            ##########################################################
            # LOADING THE DATA HERE:
            ##########################################################
            new_data = self.receiver.recv()
            if new_data:
                active_mode, JS_value, lock_state, orthosis_angle =  new_data
                self.active_mode = active_mode
                self.JS_value = JS_value
                self.lock_state = lock_state
                self.orthosis_angle = orthosis_angle


s = Snapper()
