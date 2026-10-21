"""Original Macabre Garden Folklore assets; deterministic, replaceable native surfaces.

All coordinates below are artwork coordinates, never simulation coordinates.
No random module, model access, clock or filesystem is used by asset generation.
"""
from functools import lru_cache
import pygame

OUTLINE=(36,31,35)
INK=(56,45,41); MUTED=(106,88,68); GOLD=(126,63,38); TEAL=(57,91,70)
PARCHMENT=(216,198,162); PAPER=(230,214,182); LEATHER=(72,48,40)
BONE=(224,213,184); MUSHROOM=(189,178,154); MOSS=(89,107,65); LICHEN=(137,151,97)
RUST=(161,77,61); COPPER=(191,117,80); SLATE=(101,114,116)
TERRAIN_COLORS={'grass':(90,109,65),'forest':(47,66,43),'rock':(99,105,96),
                'water':(48,79,84),'hazard':(96,65,55)}
HATS=(RUST,(140,67,51),(117,70,48),(102,111,64),(83,100,91),(158,91,52))
COATS=((70,78,68),(89,72,60),(65,80,83),(111,76,55))
# Eight different polygon silhouettes, not recolors of one triangle.
HAT_PATHS=(
 ((6,22),(8,15),(10,8),(14,3),(20,1),(25,3),(26,7),(24,10),(21,10),(23,7),(22,5),(19,5),(18,10),(19,16),(24,22),(21,24),(9,24)),
 ((5,23),(8,17),(9,12),(13,9),(19,11),(23,8),(25,10),(23,15),(20,16),(24,22),(22,24),(8,25)),
 ((5,23),(8,19),(9,13),(8,6),(11,3),(15,5),(18,10),(19,15),(23,20),(26,22),(24,25),(8,25)),
 ((5,23),(8,15),(10,6),(14,2),(17,3),(16,7),(21,9),(19,12),(22,17),(24,23),(20,25),(7,25)),
 ((3,23),(6,19),(9,14),(15,10),(21,12),(26,17),(29,22),(26,25),(19,24),(12,25),(5,25)),
 ((5,23),(8,16),(11,11),(15,8),(21,8),(25,11),(25,15),(22,18),(20,17),(22,14),(20,12),(17,13),(19,18),(24,23),(22,25),(7,25)),
 ((7,24),(10,17),(12,9),(13,2),(16,0),(19,2),(17,4),(17,11),(20,18),(24,24),(21,26),(9,26)),
 ((2,24),(6,22),(8,17),(8,10),(11,6),(17,5),(21,8),(20,12),(18,12),(19,10),(16,9),(14,12),(16,18),(23,21),(29,24),(25,27),(7,27)))


def appearance(identity):
    """Stable family resemblance, not sex, profession, personality or hat genetics."""
    return identity%8,(identity*7+3)%len(COATS),(identity*11+1)%3


def polygon(s,color,points):pygame.draw.polygon(s,color,points)


def _grain(index,variant):
    value=(index+1+variant*73)*0x45d9f3b
    value=(value^(value>>16))*0x45d9f3b
    return (value^(value>>16)) & 0xffffffff


def _specks(s,variant,colors,count=45):
    for i in range(count):
        # Coordinate hashing is cosmetic and independent of world RNG/seed.
        value=_grain(i,variant);x=value%32;y=(value>>8)%32
        pygame.draw.line(s,colors[i%len(colors)],(x,y),(min(31,x+1+(i%3==0)),y))


@lru_cache(maxsize=128)
def terrain_native(kind,variant):
    s=pygame.Surface((32,32));s.fill(TERRAIN_COLORS[kind])
    if kind in ('grass','forest'):
        _specks(s,variant,((79,96,57),(104,120,70),(115,126,78)))
        for i in range(9):
            value=_grain(i+50,variant);x=value%29+1;y=(value>>8)%27+3
            pygame.draw.lines(s,(130,138,83),False,[(x-1,y),(x,y-3),(x+1,y)])
        if kind=='grass':
            # Tiny botanical marks, not new modeled food types.
            for x,y in ((5+variant,12),(23,24-variant)):
                pygame.draw.line(s,(54,79,46),(x,y),(x+1,y-3))
                pygame.draw.rect(s,MUSHROOM,(x,y-4,2,1))
        else:
            polygon(s,OUTLINE,[(7,31),(11,25),(12,15),(7,9),(10,8),(16,15),(20,6),(23,7),(20,19),(19,28),(25,31)])
            pygame.draw.lines(s,(111,98,65),False,[(10,29),(15,25),(16,16),(20,10)],2)
            pygame.draw.line(s,(66,80,44),(16,26),(19,22),2)
            for j,(x,y,rad) in enumerate(((5,12,6),(10,6,7),(20,5,6),(27,11,6),(20,16,7),(9,17,6))):
                pygame.draw.circle(s,(29,47,34),(x,y),rad)
                pygame.draw.circle(s,(58,79,45),(x-1,y-1),max(1,rad-1))
                pygame.draw.arc(s,(97,112,60),(x-rad+1,y-rad+1,rad*2-3,rad*2-3),.6,2.8,2)
            pygame.draw.line(s,LICHEN,(13,22),(12,26))
            pygame.draw.rect(s,COPPER,(26,26,3,2));pygame.draw.rect(s,MUSHROOM,(27,28,1,2))
    elif kind=='rock':
        _specks(s,variant,((78,86,79),(119,122,106)),28)
        for dx,dy,scale in ((1,7,1),(17,19,0),(18,0,0)):
            points=[(dx+2,dy+2),(dx+10,dy),(dx+14,dy+6),(dx+12,dy+13),(dx+3,dy+14),(dx,dy+8)]
            polygon(s,OUTLINE,points);polygon(s,(132,139,126),[(dx+2,dy+3),(dx+9,dy+1),(dx+12,dy+6),(dx+5,dy+8)])
            polygon(s,(81,91,86),[(dx+1,dy+8),(dx+6,dy+9),(dx+13,dy+6),(dx+11,dy+12),(dx+4,dy+13)])
            pygame.draw.lines(s,(56,65,62),False,[(dx+9,dy+3),(dx+7,dy+6),(dx+8,dy+10)])
            pygame.draw.line(s,LICHEN,(dx+2,dy+4),(dx+4,dy+3),2)
    elif kind=='water':
        _specks(s,variant,((43,70,76),(53,85,87)),32)
        for j in range(5):
            x=(j*11+variant*7)%26;y=4+j*6
            pygame.draw.lines(s,(85,116,115),False,[(x,y),(x+3,y-1),(min(31,x+6),y)])
            pygame.draw.line(s,(36,63,71),(x+2,y+2),(min(31,x+8),y+2))
        pygame.draw.rect(s,(116,139,128),(7+variant*3,8,2,1))
    else:
        _specks(s,variant,((112,77,59),(80,57,51),(125,84,63)),40)
        for points in ([(0,8),(7,11),(12,8),(18,15),(23,16),(31,25)],[(12,8),(14,0)],[(18,15),(13,23),(15,31)],[(13,23),(2,29)]):
            pygame.draw.lines(s,(51,38,39),False,points,3)
            pygame.draw.lines(s,(28,27,31),False,points,1)
            pygame.draw.lines(s,(147,96,67),False,[(x+2,min(31,y+1)) for x,y in points],1)
    return s


@lru_cache(maxsize=512)
def terrain_tile(kind,variant,size):return pygame.transform.scale(terrain_native(kind,variant),(size,size))


@lru_cache(maxsize=256)
def gnome_native(style,sleeping=False,phase=0):
    shape,coat,beard=style;shape%=8
    s=pygame.Surface((32,40),pygame.SRCALPHA)
    # Boots and asymmetrical coat: upper-left highlights, lower-right shadows.
    pygame.draw.ellipse(s,(0,0,0,45),(5,35,24,4))
    polygon(s,OUTLINE,[(8,32),(14,32),(15,38),(5,38),(5,36)])
    polygon(s,OUTLINE,[(19,32),(24,32),(29,36-phase),(28,38-phase),(19,38-phase)])
    pygame.draw.line(s,(104,82,61),(7,36),(12,35),2)
    pygame.draw.line(s,(104,82,61),(21,35-phase),(25,36-phase),2)
    polygon(s,OUTLINE,[(9,23),(22,22),(26,29),(25,34),(18,36),(14,34),(7,35),(6,29)])
    polygon(s,COATS[coat%len(COATS)],[(10,24),(20,24),(24,30),(23,33),(16,34),(9,33),(8,29)])
    pygame.draw.line(s,(141,127,95),(10,26),(9,31))
    pygame.draw.line(s,(44,44,40),(20,28),(21,33),2)
    pygame.draw.rect(s,COPPER,(17,31,2,2))
    # Little hands, ragged beard, hidden face and oversized nose.
    for x,y in ((5,28),(25,29)):
        pygame.draw.circle(s,OUTLINE,(x,y),3);pygame.draw.circle(s,(183,135,93),(x-1,y-1),2)
    polygon(s,OUTLINE,[(7,22),(11,19),(21,20),(25,24),(23,30),(20,33),(17,32),(14,35),(10,31),(8,31)])
    shades=(BONE,MUSHROOM,(166,161,137));base=shades[beard%3]
    polygon(s,base,[(8,23),(12,20),(20,21),(24,25),(21,29),(20,31),(17,30),(14,33),(11,29),(9,30)])
    for x,y in ((11,24),(14,27),(18,26),(21,24)):
        pygame.draw.lines(s,(142,139,119),False,[(x,y),(x-1,y+3),(x,y+5)])
        pygame.draw.line(s,BONE,(x-1,y),(x-1,y+2))
    # Hat silhouette is individually built, with folded facets, worn seam and patch.
    points=HAT_PATHS[shape];polygon(s,OUTLINE,points)
    # Inner fill keeps a real one-pixel irregular border without smoothing.
    inner=pygame.Surface((32,40),pygame.SRCALPHA);polygon(inner,HATS[shape%len(HATS)],points)
    pygame.draw.lines(inner,OUTLINE,True,points,1);s.blit(inner,(0,0))
    # Creases follow the lower cloth, deliberately not a second geometric cone.
    pygame.draw.lines(s,(99,55,45),False,[(12,14 if shape!=4 else 17),(13,19),(10,22)],2)
    pygame.draw.lines(s,COPPER,False,[(10,18),(9,21),(13,22)],1)
    pygame.draw.lines(s,(89,47,39),False,[(19,17),(20,21),(23,23)],1)
    pygame.draw.lines(s,(64,43,36),False,[(7,23),(13,24),(19,23),(23,24)],1)
    # Frayed stitches and an irregular patch; they never imply abilities.
    pygame.draw.rect(s,(102,98,64),(15,18,4,3));pygame.draw.line(s,(188,161,111),(15,18),(18,20))
    for x,y in ((10,20),(13,22),(19,21)):pygame.draw.line(s,MUSHROOM,(x,y),(x+1,y-1))
    if shape in (2,3,7):
        for x,y in ((10,12),(9,14),(11,15),(20,22)):
            pygame.draw.rect(s,MOSS,(x,y,2,2));pygame.draw.rect(s,LICHEN,(x,y,1,1))
    if shape==4:
        for x,y in ((11,17),(16,14),(21,18),(24,21)):pygame.draw.rect(s,MUSHROOM,(x,y,2,1))
    pygame.draw.line(s,OUTLINE,(11,25),(13,25));pygame.draw.line(s,OUTLINE,(20,25),(22,25))
    pygame.draw.ellipse(s,OUTLINE,(13,23,8,6));pygame.draw.ellipse(s,(198,145,102),(14,23,6,5))
    pygame.draw.rect(s,(229,183,131),(14,24,3,1))
    if sleeping:
        # Reclining pose, eyes closed. No travel animation for sleeping individuals.
        s=pygame.transform.rotate(s,90)
    return s


@lru_cache(maxsize=512)
def gnome_sprite(identity_style,sleeping,size,phase=0):
    base=gnome_native(identity_style,sleeping,phase)
    scale=size/40
    image=pygame.transform.scale(base,(max(1,round(base.get_width()*scale)),max(1,round(base.get_height()*scale))))
    return image,pygame.mask.from_surface(image)


@lru_cache(maxsize=32)
def death_portrait(size):
    s=pygame.Surface((32,40),pygame.SRCALPHA)
    pygame.draw.ellipse(s,OUTLINE,(7,10,20,22));pygame.draw.ellipse(s,MUSHROOM,(8,10,18,19))
    pygame.draw.ellipse(s,BONE,(9,11,13,13))
    pygame.draw.ellipse(s,OUTLINE,(10,18,5,6));pygame.draw.ellipse(s,OUTLINE,(19,18,5,6))
    polygon(s,OUTLINE,[(16,23),(14,27),(18,27)])
    pygame.draw.rect(s,MUSHROOM,(11,27,12,5))
    for x in (13,16,19,22):pygame.draw.line(s,OUTLINE,(x,28),(x,31))
    pygame.draw.lines(s,MOSS,False,[(5,37),(4,30),(7,28),(4,32),(1,31)],1)
    return pygame.transform.scale(s,(round(size*.8),size))


@lru_cache(maxsize=128)
def icon(kind,size=20):
    """Small record/power glyphs. Icons add no factual event content."""
    s=pygame.Surface((20,20),pygame.SRCALPHA)
    if kind in ('birth','rewild'):
        pygame.draw.line(s,INK,(10,17),(10,6),2)
        polygon(s,MOSS,[(9,12),(3,11),(2,6),(7,7)])
        polygon(s,LICHEN,[(11,9),(13,3),(18,2),(17,7)])
    elif kind=='death':return pygame.transform.scale(death_portrait(20),(size,size))
    elif kind=='rain':
        for x,y in ((5,4),(11,1),(16,8)):
            pygame.draw.line(s,(91,137,149),(x,y),(x-2,y+6),2)
    elif kind=='drought':
        pygame.draw.circle(s,COPPER,(10,9),4)
        for a,b in (((10,1),(10,3)),((10,15),(10,18)),((2,9),(4,9)),((16,9),(19,9)),((3,2),(5,4)),((15,14),(17,16))):pygame.draw.line(s,GOLD,a,b)
    elif kind in ('rupture','hazard'):
        pygame.draw.lines(s,RUST,False,[(4,1),(10,7),(7,12),(15,18)],3)
        pygame.draw.line(s,OUTLINE,(10,7),(17,6),2)
    elif kind=='wellspring':
        pygame.draw.ellipse(s,SLATE,(2,10,16,8),2)
        pygame.draw.lines(s,(86,134,141),False,[(6,12),(7,6),(10,3),(13,6),(14,12)],2)
        pygame.draw.line(s,BONE,(9,7),(9,10))
    else:
        pygame.draw.circle(s,COPPER,(10,10),6,1);pygame.draw.line(s,GOLD,(10,3),(10,17))
    return pygame.transform.scale(s,(size,size))


@lru_cache(maxsize=64)
def journal_panel(width,height):
    s=pygame.Surface((max(1,width),max(1,height)));s.fill(PARCHMENT)
    pygame.draw.rect(s,LEATHER,s.get_rect(),2)
    pygame.draw.rect(s,(169,140,102),s.get_rect().inflate(-6,-6),1)
    # Sparse paper grain and botanical corners, behind the content margin.
    for y in range(8,height-8,13):
        x=(y*17)%max(1,width-16)+8
        pygame.draw.line(s,(207,188,151),(x,y),(min(width-8,x+4),y))
    for x,y,dx,dy in ((5,5,1,1),(width-6,height-6,-1,-1)):
        pygame.draw.lines(s,MOSS,False,[(x,y+16*dy),(x+2*dx,y+9*dy),(x+9*dx,y+2*dy),(x+16*dx,y)],1)
        pygame.draw.line(s,MOSS,(x+2*dx,y+9*dy),(x+6*dx,y+10*dy))
    return s


def terrain_decoration(kind,neighbors,history,size):
    edges=sum(1<<edge for edge,other in enumerate(neighbors) if other is not None and other!=kind)
    return _terrain_decoration(kind,edges,history,size)


@lru_cache(maxsize=1024)
def _terrain_decoration(kind,edges,history,size):
    """Transparent read-only neighbor/provenance treatment, bounded and cached.

    neighbors=N,E,S,W terrain names; history=last actual terrain intervention kind.
    Edge stippling stays inside the authoritative tile, never suggesting a bridge.
    """
    s=pygame.Surface((32,32),pygame.SRCALPHA)
    for edge in range(4):
        if not edges & (1<<edge):continue
        for i in range(2,31,5):
            x,y=((i,0),(31,i),(i,31),(0,i))[edge]
            pygame.draw.rect(s,OUTLINE,(x,y,1,1))
            # Broken shore/soil contours continue along neighboring tile edges.
            if kind in ('water','rock','hazard'):
                a,b=((i,1),(29,i),(i,29),(1,i))[edge]
                pygame.draw.line(s,(113,121,97) if kind=='rock' else (84,107,99) if kind=='water' else (127,88,67),(a,b),(min(31,a+1),min(31,b+1)))
            if kind in ('grass','forest'):
                x,y=((i,1),(29,i),(i,29),(1,i))[edge]
                pygame.draw.line(s,MOSS,(x,y),(min(31,x+1),min(31,y+1)))
    if history=='rupture':
        pygame.draw.lines(s,(168,100,68),False,[(2,26),(9,21),(15,22),(23,15),(30,16)],1)
        for x,y in ((8,22),(16,21),(24,15)):pygame.draw.line(s,OUTLINE,(x,y-2),(x+1,y+2))
    elif history=='rewild':
        pygame.draw.lines(s,(40,41,34),False,[(2,28),(10,25),(17,28),(25,23)],2)
        for x,y in ((5,27),(13,26),(23,24)):
            pygame.draw.line(s,LICHEN,(x,y),(x,y-4));pygame.draw.line(s,MOSS,(x,y-1),(x+3,y-3))
    elif history=='wellspring':
        pygame.draw.arc(s,(149,159,142),(5,4,22,24),.4,5.5,1)
        pygame.draw.arc(s,(91,128,125),(8,7,16,18),.6,3.6,1)
    return pygame.transform.scale(s,(size,size))


@lru_cache(maxsize=1024)
def illustrated_tile(kind,variant,edges,history,size):
    """Bake transparent edge/history marks into opaque terrain once per cache key.

    A single opaque map blit avoids paying alpha-blend cost across the 4K viewport
    every frame. The cached result never contains food stocks or agent state.
    """
    s=terrain_tile(kind,variant,size).copy()
    s.blit(_terrain_decoration(kind,edges,history,size),(0,0))
    return s
