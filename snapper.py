import sys,time,os,random,cPickle, math
import traceback, socket
import pygame, thread, struct
from pygame.locals import *
import numpy
import atexit
import skeleton


class NetworkReceive:
    def __init__(self, port, format):
        self.port = port
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.socket.setblocking(0)
        self.format = format        
        
        atexit.register(self.close)
        self.socket.bind(("0.0.0.0", self.port))
        
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
                print self.port, vals
            except:
                print "Data problem..."
                
            return vals
        else:
            
            return None
        
    def close(self):
        self.socket.close()
        
            
class IntegratedControl:
    def __init__(self, speed, saturation = 1):
        self.reset()
        self.speed = speed
        self.saturation = saturation
        
    def update(self, val, dt):
        self.x += dt * val * self.speed
        if self.x<-self.saturation:
            self.x = -self.saturation
        
        if self.x>self.saturation:
            self.x = self.saturation
        
    def reset(self):
        self.x = 0
        

class Snapable:
    def __init__(self, start_x=0, k=40, damping=0.9, snap=95):
        self.x = start_x
        self.target_x = start_x
        self.k = k
        self.damping = damping
        self.snap = snap
        self.dx =0 
        
    def set_centers(self, centers):
    
        self.centers = centers
        
    def set_target(self, target):
        self.target_x = target
        
    def set_snapping(self, snapping):
        self.snap = snap
        
    def update(self, dt):
        ds = numpy.abs(self.centers-self.target_x)
        n = numpy.exp(-(ds*ds)/(self.snap*self.snap))
        n = n / numpy.sum(n)
        ddx = 0
        for i in range(len(self.centers)):
            ddx += self.k * (self.centers[i]-self.x) * n[i]        
        self.dx = self.dx + ddx*dt
        self.dx = self.dx * self.damping
        self.x = self.x + self.dx*dt
        
        
        
class Barrier:
    def __init__(self, time, lane, type, image):
        self.time = time
        self.lane = lane
        self.type = type
        self.image = image
        
class BarrierModel:
    def __init__(self, lanes, density):
        self.lanes = lanes
        self.density = density
        self.lane_data = [] 
                
    def add(self, barrier):
        self.lane_data.append(barrier)
        
    def update(self, shift, car_lane, car_height, collision=None):
        kill_list = []
        
        for event in self.lane_data:
            event.time = event.time - shift
            
            # collision!
            if event.time<car_height and car_lane == event.lane:
                kill_list.append(event)
                if collision:
                    collision(event)
                
            # off the screen
            if event.time<-event.image.get_height():
                kill_list.append(event)
                
        for kill in kill_list:
            self.lane_data.remove(kill)
            
    
        
STATE_WAITING = 0
STATE_RUNNING = 1


class Snapper:
    def __init__(self):
        self.skeleton = skeleton.Skeleton(draw_fn = self.draw, tick_fn = self.tick, event_fn = self.event)
        self.control = IntegratedControl(speed=1.0)
        self.receiver = NetworkReceive(2222, "!dddd")
        self.control_receiver = NetworkReceive(3333, "!d")
        
        atexit.register(self.quit)
        self.lane_image = pygame.image.load("base.png").convert()
        self.verge_image = pygame.image.load("verge.png").convert()
        self.car_image= pygame.image.load("car.png").convert_alpha()
        self.barrier_image = pygame.image.load("barrier.png").convert_alpha()
        self.coin_image = pygame.image.load("coin.png").convert_alpha()
        
        self.lane_sound = pygame.mixer.Sound("lane.wav")
        self.barrier_sound = pygame.mixer.Sound("barrier.wav")
        self.coin_sound = pygame.mixer.Sound("coin.wav")
        self.score_sound = pygame.mixer.Sound("score.wav")
        self.tyre_sound = pygame.mixer.Sound("tyres.wav")
        
        self.tyre_level = 0
       
        self.played_score = 0
        self.skeleton.fps = 120
        self.lane_width = self.lane_image.get_width()
        self.nlanes = 5
        
        self.barriers = BarrierModel(self.nlanes, 0.001)
        
        
        edge = (self.skeleton.w-self.nlanes*self.lane_width)/2
        self.car = Snapable()
        self.noise = 0
        centers = [edge+self.lane_width/2+i*self.lane_width for i in range(self.nlanes)]
        self.edge = edge
        self.car.set_centers(numpy.array(centers))
        
        self.control_value = 0
        self.position = 0
        self.speed = 1.5
        self.car_lane = 0
        self.score = 0
        self.state = STATE_WAITING
        
        self.create_back_surface()
        self.skeleton.main_loop()
        
        
    def quit(self):
        self.receiver.close()
        
        
    def event(self, event):
        if event.type == KEYUP:
            if event.key == K_SPACE:
                self.state = STATE_RUNNING
                
    def get_lane(self, lane):
        return self.edge+lane*self.lane_width
    
    
    def create_back_surface(self):
        self.back_surface = pygame.Surface((self.skeleton.w, self.skeleton.h+self.lane_image.get_height()))
        for j in range(11):
            y = j*self.lane_image.get_height()
            self.back_surface.blit(self.verge_image, (self.edge-128,y), (0,0,256,128))
            self.back_surface.blit(self.verge_image, (self.edge-128+self.nlanes*self.lane_width,y), (128,0,256,128))            
            for i in range(self.nlanes):
                x = self.get_lane(i)
                self.back_surface.blit(self.lane_image, (x,y))
        
        
    def draw(self, surface):
        
        self.skeleton.screen.unlock()
        
              
        self.skeleton.screen.blit(self.back_surface, (0, -(self.position % 128)))
        
                
        # car (with shake)
        offx = random.gauss(0, self.noise)        
        
        dir = (math.atan2(self.car.dx/500.0,1.0)/math.pi)*180.0
        rotated_car = pygame.transform.rotozoom(self.car_image, offx+dir, 1.0)
        self.skeleton.screen.blit(rotated_car, (self.car.x-rotated_car.get_width()/2, 200))
        
        #  barriers
        for barrier in self.barriers.lane_data:            
            x = self.get_lane(barrier.lane) + (self.lane_width-barrier.image.get_width())/2            
            self.skeleton.screen.blit(barrier.image, (x, barrier.time))
        
        #waiting text
        if self.state==STATE_WAITING:
            phase = math.sin(time.clock()*8)
            scale = (phase+1)/8.0+1.0
            text_surface = self.skeleton.default_font.render("Ready!", True, (255,255,255))
            
            
            text_surface = pygame.transform.rotozoom(text_surface, 0.0, scale)
            x = (self.skeleton.w-text_surface.get_width())/2
            y = (200-text_surface.get_height())/2
            self.skeleton.screen.blit(text_surface, (x,200))
        
        # points
        text_surface = self.skeleton.default_font.render("Score: %d" % int(self.played_score), True, (255,200,155))
        x = 80
        y = self.skeleton.h-50
        self.skeleton.screen.blit(text_surface, (x,y))
    
       
        
        
    def collide(self, event):
        if event.type=="coin":
            self.score += 50
            self.coin_sound.play()
        if event.type=="barrier":
            self.score -= 50
            self.barrier_sound.play()
        if self.score<0:
            self.score = 0
    
    def add_object(self, type, lane=None):
        y = self.skeleton.h+200
        if lane==None:
            lane = random.randint(0,self.nlanes-1)
        if type=="coin":        
            self.barriers.add(Barrier(y, lane, type, self.coin_image))
        if type=="barrier":
            self.barriers.add(Barrier(y, lane, type, self.barrier_image))
    
    def tick(self, dt):

        if self.state==STATE_WAITING:
            pass
        if self.state==STATE_RUNNING:
        
        
            new_lane = 0
            # what lane is the car in?
            for i in range(self.nlanes):
                left = self.get_lane(i)
                right = left + self.lane_width
                if self.car.x>=left and self.car.x<right:
                    new_lane = i
               

            if new_lane!=self.car_lane:
                    self.car_lane = new_lane
                    self.lane_sound.play()
                    
       #     add coins and blocks
            if random.random()<0.02:
                if random.random()<0.5:
                    self.add_object("coin")
                    
                else:
                    self.add_object("barrier")
                    
            control = self.control_receiver.recv()
            if control:
              
                if control[0]==3:
                    self.add_object("coin", lane=0)
                    self.add_object("coin", lane=1)
                if control[0]==2:
                    self.add_object("coin", lane=self.nlanes-1)
                    self.add_object("coin", lane=self.nlanes-2)
                    

                    
            new_data = self.receiver.recv()
            if new_data:
                lda, noise, _, _=  new_data
                self.control_value = lda
                self.noise = math.exp(noise/2)
                
            
            
            if self.noise>0.5:
                self.tyre_level += self.noise
                
            
            if self.tyre_level>2.0 and self.tyre_sound.get_num_channels()==0:
                self.tyre_sound.play()
                
            if self.tyre_level<0.5 and self.tyre_sound.get_num_channels()>0:
                self.tyre_sound.stop()
            
            self.tyre_level = self.tyre_level *0.85
            
            self.control.update(self.control_value, dt)
                   
            x,y = pygame.mouse.get_pos()
            self.control_value = ((x-self.skeleton.w/2)/float(self.skeleton.w))*4
          
            self.score += 0.02
            # convert -1 -- 1 to screen co-ordinates
            pos = self.control.x*self.skeleton.w/2+self.skeleton.w/2
            self.car.set_target(pos)
            self.car.update(dt)
            self.position = self.position + self.speed
            self.barriers.update(self.speed, self.car_lane, car_height = 200+self.car_image.get_height()/2, collision=self.collide)
            
            
            
            if self.played_score>self.score:
                self.played_score = self.score
            if int(self.played_score)<int(self.score):                
                
                new_score = self.played_score+0.5
                #if int(new_score)!=int(self.played_score):
                #    self.score_sound.play()
                self.played_score = new_score
            
        
# import pstats
# p = pstats.Stats("snapper")
# p.strip_dirs().sort_stats('cumulative').print_stats()

#import cProfile
#cProfile.run("s=Snapper()", "snapper")        
s = Snapper()
