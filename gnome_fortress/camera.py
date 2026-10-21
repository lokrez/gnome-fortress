"""Presentation coordinates only. World and RNG are deliberately absent."""
import math
import pygame


class Camera:
    def __init__(self,width,height,viewport,tile=24):
        self.width,self.height=width,height
        self.viewport=pygame.Rect(viewport);self.tile=tile
        self.x=(width-self.viewport.w/tile)/2
        self.y=(height-self.viewport.h/tile)/2
        self.clamp()

    @property
    def minimum(self):return max(4,min(96,int(min(self.viewport.w/self.width,self.viewport.h/self.height))))

    @property
    def levels(self):return sorted({self.minimum,*[v for v in (8,12,16,20,24,32,40,48,64,80,96) if v>=self.minimum]})

    @property
    def offset(self):return self.viewport.x-round(self.x*self.tile),self.viewport.y-round(self.y*self.tile)

    def clamp(self):
        self.tile=max(self.minimum,min(96,self.tile))
        for key,extent,pixels in [('x',self.width,self.viewport.w),('y',self.height,self.viewport.h)]:
            span=pixels/self.tile
            setattr(self,key,(extent-span)/2 if span>=extent else max(0,min(getattr(self,key),extent-span)))

    def resize(self,viewport):
        cx=self.x+self.viewport.w/(2*self.tile);cy=self.y+self.viewport.h/(2*self.tile)
        self.viewport=pygame.Rect(viewport)
        self.center(cx,cy)

    def center(self,x,y):
        self.x=x-self.viewport.w/(2*self.tile);self.y=y-self.viewport.h/(2*self.tile);self.clamp()

    def center_tile(self,x,y):self.center(x+.5,y+.5)

    def pan(self,dx,dy):self.x+=dx/self.tile;self.y+=dy/self.tile;self.clamp()

    def fit(self):
        self.tile=self.minimum;self.center(self.width/2,self.height/2)

    def zoom(self,steps,anchor=None):
        anchor=anchor or self.viewport.center
        ox,oy=self.offset
        wx,wy=(anchor[0]-ox)/self.tile,(anchor[1]-oy)/self.tile
        levels=self.levels;index=min(range(len(levels)),key=lambda i:abs(levels[i]-self.tile))
        self.tile=levels[max(0,min(len(levels)-1,index+steps))]
        self.x=wx-(anchor[0]-self.viewport.x)/self.tile
        self.y=wy-(anchor[1]-self.viewport.y)/self.tile;self.clamp()

    def world_to_screen(self,x,y):
        ox,oy=self.offset;return ox+x*self.tile,oy+y*self.tile

    def tile_rect(self,x,y):return pygame.Rect(*self.world_to_screen(x,y),self.tile,self.tile)

    def screen_to_world(self,pos):
        if not self.viewport.collidepoint(pos):return None
        ox,oy=self.offset;x=math.floor((pos[0]-ox)/self.tile);y=math.floor((pos[1]-oy)/self.tile)
        return (x,y) if 0<=x<self.width and 0<=y<self.height else None

    def visible_bounds(self):
        ox,oy=self.offset;r=self.viewport;t=self.tile
        return (max(0,math.floor((r.left-ox)/t)),max(0,math.floor((r.top-oy)/t)),
                min(self.width,math.ceil((r.right-ox)/t)),min(self.height,math.ceil((r.bottom-oy)/t)))
