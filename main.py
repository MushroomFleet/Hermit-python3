""" by Lingdong Huang
"""

# =============================================================================
# IMPORT MODULES
# =============================================================================

## built-in modules
import sys
import math
import _thread as thread
import random
import string
import os

## dependencies
import pygame
# import pygame._view is no longer needed in newer Pygame versions
import numpy

## custom modules
import lib.noise as noise
import lib.tree as tree
import lib.creature as creature
import lib.utilities as u
import lib.filter as filter
import lib.parse as parse
import lib.pattern as pattern
import lib.particle as particle
import lib.font as font
import lib.settings as settings


# =============================================================================
# INITIALIZATION
# =============================================================================
pygame.init()
settings.init()

# =============================================================================
# VARIABLES
# =============================================================================

## window
## ----------------------------------------------------------------------------
size = width, height = 1280, 320
buff = 200
screen = pygame.display.set_mode([int(width/2),height+50])#,pygame.FULLSCREEN )
canvas = pygame.Surface([int(width/2),height])
pygame.display.set_caption("")
fullscreen = False

box = pygame.Surface([240,50])
box.fill([0,0,0])
box.set_alpha(50,pygame.RLEACCEL)


## terrain
## ----------------------------------------------------------------------------
treeDensity = 32
landDensity = 32
allloads = width/treeDensity
loaded = 0

Ls = [None]*4
Lrs = [None]*4

lspds = [0.1,0.2,0.5,1]
terrain = [0]*4
totalMade = [0]*4

locs = [0,0,0,0]
locrs = [width,width,width,width]

land = [0]*(int(((width)/2)/landDensity+2))
landloc = 0
landni = 0

## style
## ----------------------------------------------------------------------------
COLOR_KEY = [255,0,255]
scheme = [(70,69,63),(225,225,210)]
gfont = font.GFont(10,2,)
screen.fill([240,240,240])

## game
## ----------------------------------------------------------------------------
x = 0
SPEED = 0.5
gamestart = False
clock = pygame.time.Clock()
icon = pygame.Surface([512,512])
icon.set_colorkey(COLOR_KEY)

keyseq = []
commandlist = ["set time","set speed","spawn","fullscreen","restart","set terrain","set tree density","eval"]
showconsole  = False
T = 0

## objects
## ----------------------------------------------------------------------------
vine = pattern.Vine(0,160)
pctrl = particle.ParticleCtrl()

birds = []
deers = []
cranes = []
arrows = []

horse = creature.Horse(100,0)
horse.yo = height
horse.s = 1
horse.aspd = 0.09
horse.color = (140,140,140)

man = creature.Man(150,0)
man.yo = height
man.s = 0.7
man.color = (140,140,140)
man.arrows = arrows
man.walk()



# =============================================================================
# Functions
# =============================================================================

## icon
## ----------------------------------------------------------------------------

def Icon():
	global icon, scheme
	iconhorse = creature.Horse(200,0)
	iconhorse.yo = 240
	iconhorse.color = scheme[0]
	iconhorse.s=7
	iconman = creature.Man(250,0)
	iconman.yo = 250
	iconman.s=6
	iconman.color = scheme[0]
	iconman.mount(iconhorse)
	for i in range(0,200):
		iconman.animate()
		iconhorse.animate()
	icon.fill(scheme[1])
	pygame.draw.rect(icon,scheme[0],[0,0,512,512],50)
	iconman.draw(icon)
	iconhorse.draw(icon)
	pygame.display.set_icon(icon)


## making terrain
## ----------------------------------------------------------------------------

def makeBGLayer(n):
	global loaded, allloads, terrain, lspds, totalMade
	#print("Making Background...")
	l = pygame.Surface([width+buff*2,height])
	l.fill(COLOR_KEY)
	l.set_colorkey(COLOR_KEY)

	if terrain[n] == 0:
		treesum = width/(0.0+len(Ls)*treeDensity)
		for i in range(0,int(treesum)):
			thetree = [ random.choice([tree.tree2]),
						random.choice([tree.tree1,tree.tree1,tree.tree2]),
						random.choice([tree.tree1,tree.tree4,tree.tree3]),
						random.choice([tree.tree1,tree.tree4,tree.tree3]) ][n]
			thetree(l,random.random()*width+buff,height,(120-n*30)+random.randrange(-10,10))
			loaded += 1
	elif terrain[n] == 1:

		treesum = (width/(0.0+len(Ls)*treeDensity))
		for i in range(0,int(math.ceil(treesum/2.0))):
			thetree = [ random.choice([tree.tree1,tree.tree3]),
						random.choice([tree.tree1,tree.tree3]),
						random.choice([tree.tree1,tree.tree3]),
						random.choice([tree.tree1,tree.tree3]) ][n]
			thetree(l,random.random()*width+buff,height,(120-n*30)+random.randrange(-10,10))
			loaded += 2
		if n != 3:
			poly = []
			poly.append([0,height])
			for i in range(buff,width+buff,landDensity):
				poly.append([i,height-makeLand(i*0.05,n*0.5,500-n*90)])
			poly[1][1] = (poly[1][1]-height)/2.0+height
			poly[-1][1] = (poly[-1][1]-height)/2.0+height
			poly.append([width+buff*2,height])
			pygame.draw.polygon(l,(210-n*20,210-n*20,210-n*20),poly)

	totalMade[n] += 1
	if totalMade[n]%int(lspds[n]*10) == 0:
		terrain[n] = (terrain[n]+1) % 2
	#print(str(loaded)+"/"+str(allloads))
	return l

def mt(LN,*args):
	global Ls, Lrs, loaded, allloads
	allloads = len(args)*(width/(len(Ls)*treeDensity))
	loaded = 0
	if LN == 1:
		for a in args:
			Ls[a] = makeBGLayer(a)
	elif LN == 2:
		for a in args:
			Lrs[a] = makeBGLayer(a)

def makeLand(n,m=0,maxheight = 20):
	return max(noise.noise(n*0.1,m*0.5)*maxheight,2)-2

for landni in range(0,len(land)):
	land[landni]=makeLand(landni,maxheight=20+terrain[3]*120)


## loading
## ----------------------------------------------------------------------------

def loadscreen():
	while loaded < allloads-1 and not gamestart:
		for i in range(2):
			vine.grow(screen)
		pygame.draw.rect(screen,(240,240,240),[0,170,100,20])
		u.text(screen,10,height/2+15,"Loading... "+str(loaded)+"/"+str(allloads),(180,180,180))
		u.line(screen,(180,180,180),[0,height/2],[(float(loaded)/allloads)*width/2,height/2],1)
		pygame.display.flip()

## spawning
## ----------------------------------------------------------------------------

def makeBirds(n):
	global birds
	for i in range(0,n):
		b = creature.Bird(random.randrange(int(width/2+10),int(width/2+60)),0)
		b.s = 0.5
		b.aspd = 0.3
		b.yo = height
		b.color = (140,140,140)
		b.dir = random.choice([1,-1])
		birds.append(b)

def makeDeers(n):
	global deers
	for i in range(0,n):
		r = random.randrange(-5,5)
		deer = creature.Deer(int(width/2)+landDensity+50+r*10,0,color = (160+r,160+r,160+r))
		deer.yo = height
		deer.s = 1.1
		deer.aspd = 0.15
		deers.append(deer)


def makeCranes(n):
	global cranes
	for j in range(0,n):
		r = random.randrange(-5,5)
		crane = creature.Crane(int(width/2)+landDensity+random.randrange(0,200),0)
		crane.color = (180+r,180+r,180+r)
		crane.yo = height-150-120*random.random()
		crane.s = 0.5+random.random()*0.2
		crane.aspd = 0.05
		crane.dir = -1
		crane.t = (j/5.0)*200
		cranes.append(crane)

## calculation
## ----------------------------------------------------------------------------

def onLandY(instx):
	if x== 0:ep = -0.01
	else:ep = 0.01
	lastAlt = land[int(((x-ep)%landDensity + instx)//landDensity)]
	nextAlt = land[int(((x-ep)%landDensity + instx)//landDensity)+1]
	return lastAlt+(nextAlt-lastAlt)*((((x-ep)%landDensity + instx)%landDensity)/landDensity)


## object control
## ----------------------------------------------------------------------------
def deerCtrl():
	global deers
	for d in deers:
		d.yo = height-30-onLandY(max(min(d.x,width/2),0))
		if noise.noise(T*0.001,deers.index(d))<0.5:
			d.x -= d.spd
			d.walk()
		else:
			d.rest()
		if d.x<-100:
			deers.remove(d)

def craneCtrl():
	global cranes
	for c in cranes:
		c.x -= 2*c.s
		c.fly()
		if c.x<-100:
			cranes.remove(c)

def arrowCtrl():
	global arrows
	for a in arrows:
		if a.x > width/2 or a.x < -10 or height-onLandY(a.x) >= a.calcHead()[1]:
			a.fly()
		else:
			a.v[0] = 0
			a.v[1] = 0
			a.flicker = 0
		if a.x > width/2:
			arrows.remove(a)

def birdCtrl():
	global birds, arrows, pctrl
	for b in birds:
		if b.health > 0:
			if ((abs(man.x - b.x) < 100 and random.random()<0.05) or random.random()<0.0002) and b.on == 0:
				b.on = 1
				ra = math.pi/20.0+random.random()*math.pi/6.0*2.1
				rl = random.choice([3,4,5])
				b.v=[rl*math.cos(ra),-rl*math.sin(ra)]
			if b.on == 1:
				b.simpFly()

				if abs(man.x - b.x) > 160 and random.random()<1:
					b.v[1] = min(b.v[1]+0.05,0.4)
				if b.y >= 2:
					b.on = 0

			else:
				b.rest()
				if 0 < b.x < width/2:
					b.yo=height-3-onLandY(b.x)

			for a in arrows:
				if u.dist(a.x,a.y,b.x,b.y+b.yo) < b.s*30 and a.v[0] > 0:
					a.v[0]/= 2
					b.arrow = a
					b.health = 0
					b.x = a.calcFeather()[0]
					b.y = a.calcFeather()[1] - b.yo
					for i in range(0,12):
						pctrl.particles.append(particle.Particle(a.calcFeather()[0],a.calcFeather()[1],[8*(random.random()-0.5),8*(random.random()-0.3)]))

			if b.x<0 or b.x>width or b.yo<0:
				birds.remove(b)
		else:
			b.fall()

## console command handling
## ----------------------------------------------------------------------------

def exe(command):
	global T, SPEED,fullscreen,terrain,totalMade,landni,land, treeDensity
	try:
		com = parse.parse(command.split("-")[0],commandlist)[0]
		par = command.split("-")[1:]
		for i in range(0,len(par)):
			par[i] = par[i].strip()

		if com == "set time":
			T = int(par[0])
			settings.msg = ["TIME SET TO "+par[0]+".",settings.msgt]
		elif com == "set speed":
			SPEED = float(par[0])
			settings.msg = ["SPEED SET TO "+par[0]+".",settings.msgt]
		elif com == "restart":
			python = sys.executable
			os.execl(python, python, "-B", * sys.argv)
		elif com == "fullscreen":
			if len(par) == 0:
				fullscreen = not fullscreen
			else:
				fullscreen = [False,True][int(par[0])]
			if fullscreen:
				pygame.display.set_mode([int(width/2),height+50],pygame.FULLSCREEN)

			else:
				pygame.display.set_mode([int(width/2),height+50])
			pygame.display.set_caption("")
			settings.msg = ["FULLSCREEN "+["OFF.","ON."][fullscreen],settings.msgt]
		elif com == "spawn":
			animal = par[0]
			xn = int(par[1])
			if animal == "bird":
				makeBirds(xn)
			elif animal == "deer":
				makeDeers(xn)
			elif animal == "crane":
				makeCranes(xn)
			elif animal == "unicorn":
				for i in range(xn):
					r = random.randrange(-5,5)
					unicorn = creature.Unicorn(int(width/2)+landDensity+50+r*10,0)
					unicorn.yo = height
					unicorn.s = 1.0
					unicorn.aspd = 0.2
					unicorn.dir = -1
					unicorn.spd = 2
					deers.append(unicorn)
			settings.msg = [str(xn)+" "+animal+" SPAWNED.",settings.msgt]
		elif com == "set terrain":
			#settings.msg = ["PLEASE WAIT",settings.msgt]
			if int(par[0]) > 1:
				raise
			terrain = [int(par[0])]*4
			totalMade = [0]*4
			for landni in range(0,len(land)):
				land[landni]=makeLand(landni,maxheight=20+terrain[3]*120)
			mt(1, 3,2,1,0)
			mt(2, 3,2,1,0)
			settings.msg = ["TERRAIN SET TO "+par[0]+".",settings.msgt]
		elif com == "set tree density":
			print(terrain)
			terrain = [terrain[3]]*4
			totalMade = [0]*4
			for landni in range(0,len(land)):
				land[landni]=makeLand(landni,maxheight=20+terrain[3]*120)
			treeDensity = int(width/float(par[0]))
			mt(1, 3,2,1,0)
			mt(2, 3,2,1,0)
		elif com == "eval":
			settings.msg = [str(eval(par[0])),settings.msgt]
	except Exception as e:
		print("%s" % e)
		settings.msg = ["COMMAND NOT EXECUTED.",settings.msgt]


## keyboard controls
## ----------------------------------------------------------------------------

def keyupdowncontrol(event):
	global keyseq, showconsole, fullscreen
	if event.type == pygame.QUIT: sys.exit()
	man.keyupdowncontrol(event,horse)

	if event.type == pygame.KEYDOWN:
		if showconsole:
			k = pygame.key.name(event.key)
			#print(k)
			if k == "return":
				exe("".join(keyseq))
				showconsole = False
			elif k == "space":
				keyseq.append(" ")
			elif k == "-":
				keyseq.append("-")
			elif len(k) == 1:
				keyseq.append(k)
			elif event.key == pygame.K_BACKSPACE :
				if len(keyseq) > 0:
					keyseq.pop()

		if event.key == pygame.K_SLASH:
			showconsole = not showconsole
			if showconsole:
				settings.msg = ["CONSOLE READY.",settings.msgt]
			else:
				settings.msg = ["",settings.msgt]
			keyseq = []

		if event.key == pygame.K_f and not showconsole:
			fullscreen = not fullscreen
			if fullscreen:
				pygame.display.set_mode([width/2,height+50],pygame.FULLSCREEN)
			else:
				pygame.display.set_mode([width/2,height+50])
				pygame.display.set_caption("")

def keyholdcontrol():
	global x
	man.keyholdcontrol()
	if (0 or pygame.key.get_pressed()[pygame.K_RIGHT]) and not man.status[0].endswith("ing"):
		for a in arrows:
			a.x -= SPEED
		for b in birds:
			b.x -= SPEED
		for p in pctrl.particles:
			p.x -= SPEED
		for d in deers:
			d.x-=SPEED*0.5
		for c in cranes:
			c.x-=SPEED
		x+=SPEED
		horse.walk()

		if random.random()<0.0005:
			makeBirds(random.randrange(6,12))
		if random.random() < 0.0005 and terrain[3] == 0:
			makeDeers(1)
		if random.random() < 0.001 and terrain[3] == 1:
			makeCranes(random.randrange(1,5))
	else:
		horse.rest()


## drawing
## ----------------------------------------------------------------------------

def drawTitle():
	gfont.s = 10
	gfont.w = 1
	gfont.color = (120,120,120)
	gfont.drawStr(canvas,"Hermit",300-x*0.7,260)
	gfont.s = 5
	gfont.w = 1
	gfont.color = (120,120,120)
	gfont.drawStr(canvas,"by lingdong",450-x*0.7,280)

def drawLand():
	global landni, land, landloc
	if -x+landloc<-landDensity:
		landni += 1
		land.append(makeLand(landni,maxheight=20+terrain[3]*120))
		land.pop(0)
		landloc += landDensity

	u.polygon(canvas,(130,130,130),[[0,height]]+[[landloc-x+i*landDensity,height-land[i]] for i in range(0,len(land))]+[[width/2,height]])


def drawReflection():
	reflection = canvas
	pygame.draw.rect(screen,(180,180,180),[0,height,width/2,50])
	for i in range(0,2*(screen.get_height()-height),2):
		screen.blit(reflection,[(math.sin(i*0.5))*i*0.5+(noise.noise(pygame.time.get_ticks()*0.001,i*0.2)-0.5)*20,height+i-1],(0,height-i,width/2,1))


def drawConsole():
	if settings.msg[0] != "":
		screen.blit(box,[5,height+33-showconsole*20])
		u.text(screen,10,height+35-showconsole*20,settings.msg[0],(240,240,240))

	if settings.msg[1] <= 0 and not showconsole:
		settings.msg[0] = ""
	else:
		settings.msg[1]-=1

	if showconsole:
		input = "".join(keyseq)
		u.text(screen,10,height+25,">"+input.lower(),(240,240,240))
		u.text(screen,10,height+35," "+" | ".join(parse.parse(input.split("-")[0],commandlist)[:3]),(240,240,240))


def drawFilter():
	array = [pygame.surfarray.pixels_red(screen),pygame.surfarray.pixels_green(screen),pygame.surfarray.pixels_blue(screen)]
	filter.filter(array,T)
	array = []

def draw():
	global Ls, Lrs, locs, locrs, x
	canvas.fill([240,240,240])
	for i in range(0,len(Ls)):
		if i == 2:
			for c in cranes:
				c.draw(canvas)
		if i == 3:
			drawTitle()

			for d in deers:
				d.draw(canvas)

			horse.draw(canvas)
			man.draw(canvas)
			for a in arrows:
				a.draw(canvas)
			for b in birds:
				b.simpDraw(canvas)

			pctrl.draw(canvas)

		if Ls[i] != None:
			canvas.blit(Ls[i],[locs[i]-x*lspds[i]-buff,0])

		if locs[i]-x*lspds[i] < -width-buff:
			locs[i] += width*2
			Ls[i] = None
			thread.start_new_thread(mt,(1, i))


		if Lrs[i] != None:
			canvas.blit(Lrs[i],[locrs[i]-x*lspds[i]-buff,0])

		if locrs[i]-x*lspds[i] < -width-buff:
			locrs[i] += width*2
			Lrs[i] = None
			thread.start_new_thread(mt,(2, i))
	drawLand()




# =============================================================================
# MAIN
# =============================================================================

## main loop
## ----------------------------------------------------------------------------

def main():
	global T
	gamestart = True
	while 1:
		for event in pygame.event.get():
				keyupdowncontrol(event)
		keyholdcontrol()
		draw()
		clock.tick()
		T += 1
		u.text(canvas,10,10,"FPS: %.1f" % clock.get_fps(),(160,160,160))

		man.yo = height-20-onLandY(man.x)
		horse.yo = height-30-onLandY(horse.x)
		man.animate()
		horse.animate()

		deerCtrl()
		craneCtrl()
		arrowCtrl()
		birdCtrl()

		pctrl.emit()

		screen.blit(canvas,[0,0])
		drawReflection()
		drawConsole()
		drawFilter()

		pygame.display.flip()

## run program
## ----------------------------------------------------------------------------

Icon()
makeBirds(10)

t1 = thread.start_new_thread( mt, (1, 3,2,1,0) )
loadscreen()

while loaded<allloads:
	pass
print('loaded')

treeDensity = 16
t3 = thread.start_new_thread(mt, (2, 3,2,1,0))
main()
