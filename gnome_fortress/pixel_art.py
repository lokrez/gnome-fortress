"""Original procedural pixel art. Cosmetics encode identity, never model traits."""
from functools import lru_cache
import pygame

TERRAIN_COLORS={'grass':(91,131,76),'forest':(57,103,68),'rock':(124,131,137),
                'water':(54,128,164),'hazard':(139,78,65)}
HATS=((209,77,65),(74,136,181),(219,163,60),(125,103,176),(74,157,136),(199,111,149))
COATS=((68,98,129),(151,105,62),(100,124,69),(142,85,81),(97,88,128))
OUTLINE=(34,39,38)


def appearance(identity):return identity%len(HATS),(identity*7+3)%len(COATS),identity%3


@lru_cache(maxsize=256)
def terrain_native(kind,variant):
    s=pygame.Surface((24,24));s.fill(TERRAIN_COLORS[kind])
    if kind in ('grass','forest'):
        for i in range(6):
            x=(i*7+variant*3)%22+1;y=(i*11+variant*5)%20+2
            pygame.draw.line(s,(112,151,85),(x,y),(x+1,y-2))
        if kind=='forest':
            pygame.draw.rect(s,(76,65,47),(11,13,3,8))
            pygame.draw.polygon(s,(29,69,48),[(12,1),(3,15),(21,15)])
            pygame.draw.polygon(s,(46,88,55),[(12,0),(6,10),(17,10)])
            pygame.draw.line(s,(83,121,65),(11,4),(8,9))
    elif kind=='water':
        for i in range(4):
            x=(i*7+variant*3)%19;y=3+i*5
            pygame.draw.line(s,(108,179,195),(x,y),(min(23,x+5),y))
        pygame.draw.line(s,(37,102,145),(0,22),(23,22))
    elif kind=='rock':
        pygame.draw.polygon(s,(67,78,85),[(3,19),(1,11),(8,5),(17,4),(23,12),(21,21)])
        pygame.draw.polygon(s,(165,169,165),[(3,10),(8,4),(16,4),(20,10),(13,13)])
        pygame.draw.polygon(s,(113,124,129),[(3,11),(13,14),(21,11),(20,19),(5,19)])
    else:
        pygame.draw.lines(s,(61,43,42),False,[(0,5),(8,9),(10,16),(16,18),(20,24)],2)
        pygame.draw.lines(s,(231,149,84),False,[(7,0),(8,7),(15,11),(24,9)])
        pygame.draw.line(s,(74,45,42),(11,15),(2,21),2)
    return s


@lru_cache(maxsize=512)
def terrain_tile(kind,variant,size):return pygame.transform.scale(terrain_native(kind,variant),(size,size))


@lru_cache(maxsize=256)
def gnome_native(style,sleeping=False,phase=0):
    hat,coat,beard=style;s=pygame.Surface((16,22),pygame.SRCALPHA)
    # Boots, outlined coat, head/ears and tall hat remain readable at modest zoom.
    pygame.draw.rect(s,OUTLINE,(3,17,4,4));pygame.draw.rect(s,OUTLINE,(9,17,4,4))
    if phase:
        pygame.draw.rect(s,(80,65,53),(3,18,4,3));pygame.draw.rect(s,(80,65,53),(9,17,4,3))
    pygame.draw.rect(s,OUTLINE,(3,11,10,7))
    pygame.draw.rect(s,COATS[coat],(4,12,8,5))
    pygame.draw.rect(s,(203,161,117),(2,12,2,3));pygame.draw.rect(s,(203,161,117),(12,12,2,3))
    pygame.draw.rect(s,OUTLINE,(4,6,8,7))
    pygame.draw.rect(s,(237,197,149),(5,7,6,5))
    if beard:
        pygame.draw.polygon(s,(228,224,207) if beard==1 else (152,110,71),[(4,10),(12,10),(8,15)])
    pygame.draw.rect(s,(244,206,163),(7,9,3,2))
    pygame.draw.rect(s,OUTLINE,(5,8,1,1));pygame.draw.rect(s,OUTLINE,(10,8,1,1))
    pygame.draw.polygon(s,OUTLINE,[(2,7),(7,0),(13,7)])
    pygame.draw.polygon(s,HATS[hat],[(3,6),(7,1),(12,6)])
    pygame.draw.line(s,(245,208,117),(4,6),(11,6))
    if sleeping:
        pygame.draw.line(s,(75,96,117),(5,8),(6,8));pygame.draw.line(s,(75,96,117),(9,8),(10,8))
        # Reclining appearance is cosmetic, not a second position.
        s=pygame.transform.rotate(s,90)
    return s


@lru_cache(maxsize=512)
def gnome_sprite(identity_style,sleeping,size,phase=0):
    base=gnome_native(identity_style,sleeping,phase)
    scale=size/22
    image=pygame.transform.scale(base,(max(1,round(base.get_width()*scale)),max(1,round(base.get_height()*scale))))
    return image,pygame.mask.from_surface(image)
