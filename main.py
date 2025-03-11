'''
模拟百万像素倍增游戏
UI：
左侧是游戏主区域，右侧是小球倍增区域
逻辑：
准备使用一个np.array来存储主区域的每个像素
右边有六个选项：小球数值*1.5，*2，*3；数值转为血量，数值转为旋转发射的子弹，数值转为大方块
子弹：碰到己方像素无反应，碰到其他像素则消失并转为己方像素；碰到敌方大方块消失并给它扣血，碰到己方大方块消失并给它加血
大方块：碰到己方像素无反应，碰到其他像素则扣血并转为己方像素；碰到己方小球加血，碰到敌方小球扣血
家：碰到敌方大方块则随机将双方扣血，碰到敌方子弹则扣一滴血
'''
import random
from pgz.my_pgzero import *
import numpy as np
import time
from queue import Queue

def timer(func):
    def aaa(*args, **kwargs):
        s = time.time()
        res = func(*args, **kwargs)
        print(time.time()-s)
        return res
    return aaa

gamesize = 500
blocks = np.zeros((gamesize, gamesize), dtype=np.uint8)
colormap = [(0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
SCREENSIZE = (gamesize+50*6, gamesize)
origin_area_l = 150

addbullet = 1
tickcnt = 0

gamesurface = pygame.Surface((gamesize, gamesize))
gamechanges = Queue() # tuple(x, y, width, height, color)

class Tower(Actor):
    def __init__(self, coloridx:int=1, pos:Tuple[int, int]=(49, 49)):
        super().__init__('tower.png', (255, 255, 255))
        self.rect.center = pos
        self.health = 100
        self.bullet = 0
        self.coloridx = coloridx
    def update(self):
        global Bullet
        super().update()
        self.rotate += 1
        bulletcnt = len(busy_bullet)
        for i in range(5):
            if self.bullet > 0 and random.random() > (bulletcnt-500)/500:
                make_bullet(self.coloridx)
                self.bullet -= 1

class Bullet(Actor):
    def __init__(self):
        global towers
        super().__init__('bullet.png', (255, 255, 255))
        self.rect.width = self.rect.height = 1
        self.step = 3
        # 以下的数值其实用不上
        self.truex, self.truey = self.rect.center = self.addx, self.addy = (0,0)
        self.coloridx = 1
    def update(self):
        super().update()
        global gamesize, blocks, gamechanges
        for i in range(self.step):
            self.truex += self.addx
            self.truey += self.addy
            self.rect.centerx, self.rect.centery = self.truex, self.truey
            # 碰到边缘就反弹
            if self.rect.left < 0 or self.rect.right > gamesize-1:
                self.addx = -self.addx
                self.truex += self.addx
            if self.rect.top < 0 or self.rect.bottom > gamesize-1:
                self.addy = -self.addy
                self.truey += self.addy
            self.rect.centerx, self.rect.centery = self.truex, self.truey

            for tower in towers:
                if self.rect.colliderect(tower.rect):
                    if tower.coloridx != self.coloridx:
                        tower.health -= 1
                        self.free()
            
            for i in range(-1,2):
                for j in range(-1,2):
                    if blocks[self.rect.left+i, self.rect.top+j] != self.coloridx:
                        blocks[self.rect.left+i, self.rect.top+j] = self.coloridx
                        gamechanges.put((self.rect.left+i, self.rect.top+j, 1, 1, self.coloridx))
                        self.free()

    def free(self):
        self.remove(busy_bullet)
        self.add(free_bullet)
        
    def draw(self, surface):
        pygame.draw.rect(surface, (255,255,255), self.rect)

def make_bullet(coloridx:int=1):
    global free_bullet, busy_bullet
    bullet = free_bullet.sprites()[0]
    bullet.coloridx = coloridx
    bullet.rect.center = towers[coloridx-1].rect.center
    bullet.addx, bullet.addy = dir2pos(towers[coloridx-1].rotate, 1)
    bullet.truex, bullet.truey = bullet.rect.center
    bullet.add(busy_bullet)
    bullet.remove(free_bullet)

def init():
    global gamesurface, origin_area_l, towers, addbullet, free_bullet, busy_bullet
    gamesurface.fill((0, 0, 0))
    gamechanges.put((0, 0, origin_area_l, origin_area_l, 1))
    gamechanges.put((gamesize-1-origin_area_l, 0, origin_area_l, origin_area_l, 2))
    gamechanges.put((0, gamesize-1-origin_area_l, origin_area_l, origin_area_l, 3))
    gamechanges.put((gamesize-1-origin_area_l, gamesize-1-origin_area_l, origin_area_l, origin_area_l, 4))
    towers = [
        Tower(1, (origin_area_l//2, origin_area_l//2)),
        Tower(2, (gamesize-1-origin_area_l//2, origin_area_l//2)),
        Tower(3, (origin_area_l//2, gamesize-1-origin_area_l//2)),
        Tower(4, (gamesize-1-origin_area_l//2, gamesize-1-origin_area_l//2))
    ]
    for tower in towers:
        tower.bullet = 100
    
    free_bullet = pygame.sprite.Group()
    for i in range(1000):
        free_bullet.add(Bullet())
    busy_bullet = pygame.sprite.Group()

def update():
    global gamechanges, addbullet, tickcnt, busy_bullet
    sprite_groups[Tower].update()
    busy_bullet.update()
    # for _ in range(1000):
    #     gamechanges.put((random.randint(0, gamesize-1), random.randint(0, gamesize-1), 1, 1, random.randint(1, 4)))
    tickcnt += 1
    if tickcnt % 6 == 0:
        if random.random() < 0.1:
            random.choice(towers).bullet += addbullet
            addbullet = 1
        addbullet *= 2

# @timer
def draw():
    global blocks, colormap, gamechanges, gamesurface, towers
    while not gamechanges.empty():
        x, y, width, height, color = gamechanges.get()
        blocks[x:x+width-1, y:y+height-1] = color
        pygame.draw.rect(gamesurface, colormap[color], pygame.Rect(x, y, width, height))
    screen.blit(gamesurface, (0, 0))
    sprite_groups[Tower].draw(screen)
    for i in busy_bullet.sprites():
        i.draw(screen)

    for tower in towers:
        # pygame.draw.rect(screen, (255, 255, 255), tower.rect, 5)
        draw_text(f'子弹：{tower.bullet}', tower.rect.centerx, tower.rect.centery+30, 18, (0,0,0))
        draw_text(f'防御：{tower.health}', tower.rect.centerx, tower.rect.centery-30, 18, (0,0,0))

    # logger
    global starttime
    print(f'{len(busy_bullet.sprites())},{1/(time.time()-starttime)}')
    starttime = time.time()
    
init()
starttime = time.time()
go(draw=draw, update=update, screensize=SCREENSIZE)