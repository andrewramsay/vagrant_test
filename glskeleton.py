import sys,time,os,random,cPickle, math
import traceback

import pygame, thread
from pygame.locals import *

import thread
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import config



def create_sprite_list(texture, width, height, center=False):
    newList = glGenLists(1)
    glNewList(newList,GL_COMPILE);
    glBindTexture(GL_TEXTURE_2D, texture)
    glBegin(GL_QUADS)
    if center:
        glTexCoord2f(0, 0); glVertex2f(-width/2, -height/2)    # Bottom Left Of The Texture and Quad
        glTexCoord2f(0, 1); glVertex2f(-width/2, height/2)    # Top Left Of The Texture and Quad
        glTexCoord2f(1, 1); glVertex2f( width/2,  height/2)    # Top Right Of The Texture and Quad
        glTexCoord2f(1, 0); glVertex2f(width/2, -height/2)    # Bottom Right Of The Texture and Quad
    else:
        glTexCoord2f(0, 0); glVertex2f(0,0)    # Bottom Left Of The Texture and Quad
        glTexCoord2f(0, 1); glVertex2f(0, height)    # Top Left Of The Texture and Quad
        glTexCoord2f(1, 1); glVertex2f( width,  height)    # Top Right Of The Texture and Quad
        glTexCoord2f(1, 0); glVertex2f(width, 0)    # Bottom Right Of The Texture and Quad
    glEnd()
    glEndList()    
    return newList


def gen_texture():
    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    return texture

# load a texture and return it
def load_texture(surface, texture):    
    textureData = pygame.image.tostring(surface, "L", 1)    
    width = surface.get_width()
    height = surface.get_height()    
    glTexImage2D( GL_TEXTURE_2D, 0, GL_L, width, height, 0, GL_L, GL_UNSIGNED_BYTE, textureData)  
    
        
 
def basic_lighting():
    ambient = [0.25, 0.25, 0.25,1.0]
    position = [10.0, 0.0, 150.0, 1.0]
    mat_diffuse = [0.8, 0.8, 0.8, 1.0]
    mat_specular = [1.0, 1.0, 1.0, 1.0]
    mat_shininess = [1.0]

    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)

    glLightfv(GL_LIGHT0, GL_AMBIENT, ambient)
    glLightfv(GL_LIGHT0, GL_POSITION, position)

    glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, mat_diffuse)
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, mat_specular)
    glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS, mat_shininess)


    
# Skeleton class                                          
class GLSkeleton:

    
    #initialize opengl with a simple ortho projection
    def init_opengl(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.w, 0, self.h, -1, 500)
        glMatrixMode(GL_MODELVIEW)
        
        #enable texturing and alpha
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glEnable(GL_LINE_SMOOTH)
    
    # Initialise pygame, and load the fonts
    def init_pygame(self,w,h,fullscreen): 
        pygame.init()
        
        #nb: find biggest display mode
        modes = pygame.display.list_modes(32)
        if not modes:
            modes = pygame.display.list_modes(24)
        if fullscreen == True:
            self.screen = pygame.display.set_mode(modes[0],pygame.FULLSCREEN|pygame.OPENGL|pygame.DOUBLEBUF)
            self.w = self.screen.get_width()
            self.h = self.screen.get_height()
        else:
            self.screen = pygame.display.set_mode((w,h),pygame.OPENGL|pygame.DOUBLEBUF)
            self.w = w
            self.h = h
        self.init_opengl()
       
      
                                  
        
    # init routine, sets up the engine, then enters the main loop
    def __init__(self, w, h, draw_fn = None, tick_fn = None, event_fn = None, fullscreen=False):    
        self.init_pygame(w,h,fullscreen)
        self.fps = 60
        self.clock = pygame.time.Clock()
        self.start_time = time.clock()
        self.draw_fn = draw_fn
        self.tick_fn = tick_fn
        self.event_fn  = event_fn
        self.auto_clear = True
        self.running = True
        
    # handles shutdown
    def quit(self):
        self.running = False
        
    # this is the redraw code. Add drawing code between the "LOCK" and "END LOCK" sections
    def flip(self):
          # clear the transformation matrix, and clear the screen too
          glMatrixMode(GL_MODELVIEW)
          glLoadIdentity()
          if self.auto_clear:
            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
          
          if self.draw_fn:
            self.draw_fn()
          
          pygame.display.flip()
     
       
    # Get the array containing the up or down states for each key. For example, key_state[K_UP] is true if the up arrow key is pressed, [K_q] if Q is pressed, etc.
    def check_key_state(self):
          key_state = pygame.key.get_pressed()
          
            
           
    #frame loop. Called on every frame. all calculation shpuld be carried out here     
    def tick(self):          
          self.clock.tick(self.fps)                             
          self.handle_events()                   
          delta_t = time.clock() - self.start_time  
          self.start_time = time.clock()                  
          self.check_key_state()          
          if self.tick_fn:
            self.tick_fn(self.clock.get_time())
          self.flip()
                    
          

   
    #returns last mouse position
    def get_mouse(self):
          return self.mouse_pos
     
    #Event handlers. These are called as events arrive
    def keydown(self,event):
          return
     
    def keyup(self,event):
          if event.key == K_ESCAPE:
               self.quit()
          return
          
    def mouseup(self,event):
          return
     
    def mousedown(self,event):
          return
          
    def mousemove(self,event):
          (self.mouse_pos) = event.pos
          return
    
   
    
    #event handling code. Calls the relevant handlers
    def handle_events(self):
          for event in pygame.event.get():  
               if self.event_fn:
                self.event_fn(event)
               if event.type==KEYDOWN:
                 
                    if event.key==K_ESCAPE:
                        self.quit()
                                                                                                                                
               if event.type == QUIT:
                    self.quit()
               elif event.type == MOUSEBUTTONUP:
                    self.mouseup(event)
               elif event.type == MOUSEBUTTONDOWN:
                    self.mousedown(event)
               elif event.type == MOUSEMOTION:     
                    self.mousemove(event)

        
                    
         
    #main loop. Just runs tick until the program exits     
    def main_loop(self):
        while self.running:
            self.tick()
         
     
