import sys,time,os,random,cPickle, math
import traceback
import pygame, thread
from pygame.locals import *
                                                                              
        
        
        
        
# Skeleton class                                          
class Skeleton:


    
    # Initialise pygame, and load the fonts
    def init_pygame(self, w, h): 
        pygame.init()
        default_font_name = pygame.font.match_font('bitstreamverasansmono', 'verdana', 'sans')
        if not default_font_name:           
            self.default_font_name = pygame.font.get_default_font()  
        self.default_font = pygame.font.Font(default_font_name, 36)
        self.screen = pygame.display.set_mode((w,h), FULLSCREEN)                  
        #store screen size
        self.w = self.screen.get_width()
        self.h = self.screen.get_height()
        self.centre_x = self.w/2
        self.centre_y = self.h/2
        
       
      
    #initialise any surfaces that are required
    def init_surfaces(self):        
        self.draw_buf = pygame.Surface(self.screen.get_size())    
        self.draw_buf.fill((255,255,255))
        
            

               
    # init routine, sets up the engine,
    def __init__(self, size=(800,1200), draw_fn=None, tick_fn=None, event_fn=None, quit_fn=None):    
        # screen size
        self.init_pygame(size[0],size[1])
        self.init_surfaces()
        self.fps = 60        
        self.clock = pygame.time.Clock()        
        self.last_frame_time = time.clock()
        self.draw_fn = draw_fn
        self.tick_fn = tick_fn
        self.quit_fn = quit_fn
        self.handle_event = event_fn
        self.looping = True
        
        
    # handles shutdown
    def quit(self):
        if self.quit_fn:
            self.quit_fn()
        self.looping = False
        
    # wrapper for drawing text on screen
    def text(self, buffer, text,  color, position):       
        textImage = self.default_font.render(text, True, color)
        buffer.blit(textImage, position)
    
    def transparent_text(self, buffer, text,  color, position, alpha=255):       
        textImage = self.default_font.render(text, False, color)
        textImage.set_alpha(alpha)
        buffer.blit(textImage, position)
        
                     
    def screen_text(self, text, position, color=(0,0,0)):
        self.text(self.screen, text, color, position)

        
    # this is the redraw code. Add drawing code between the "LOCK" and "END LOCK" sections
    def flip(self):
          self.screen.blit(self.draw_buf, (0,0))          
          
          if self.draw_fn!=None:
            self.draw_fn(self.screen)
          pygame.display.flip()
     
       
    # Get the array containing the up or down states for each key. For example, key_state[K_UP] is true if the up arrow key is pressed, [K_q] if Q is pressed, etc.
    def check_key_state(self):
          self.key_state = pygame.key.get_pressed()
          
            
           
    #frame loop. Called on every frame. all calculation shpuld be carried out here     
    def tick(self):          
          #self.clock.tick(self.fps)                             
          self.handle_events()                   
          delta_t = time.clock() - self.last_frame_time            
          self.last_frame_time = time.clock()                  
          self.check_key_state()     

          if self.tick_fn!=None:
            self.tick_fn(delta_t)
          self.flip()

                   
   
    #returns last mouse position
    def get_mouse(self):
          return self.mouse_pos
     
    #Event handlers. These are called as events arrive
    def keydown(self,event):
          return
     
    def keyup(self,event):
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
               if event.type==KEYDOWN:
                
                    if event.key==K_ESCAPE:
                        self.quit()
                    else:
                        self.keydown(event)
                        
               if event.type==KEYUP:
                self.keyup(event)
                
               if event.type == QUIT:
                    self.quit()
                     
               elif event.type == MOUSEBUTTONUP:
                    self.mouseup(event)
               elif event.type == MOUSEBUTTONDOWN:
                    self.mousedown(event)
               elif event.type == MOUSEMOTION:     
                    self.mousemove(event)
               if self.handle_event:
                self.handle_event(event)

    #main loop. Just runs tick until the program exits     
    def main_loop(self):
        while self.looping:
            self.tick()
        pygame.quit()
         
     


          



 