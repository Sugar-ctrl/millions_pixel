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
from math import *
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

def ez_num(num:int) -> str:
    if abs(num) < 1000:
        return str(num)
    elif abs(num) < 10000000:
        return str(num//1000/10) + '万'
    elif abs(num) < 100000000000:
        return str(num//10000000/10) + '亿'
    else:
        return ez_num(num/100000000) + '亿'

gamesize = 500
blocks = np.zeros((gamesize, gamesize), dtype=np.uint8)
colormap = [(0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
SCREENSIZE = (gamesize+50*6, gamesize)
origin_area_l = 150

addbullet = 1
tickcnt = 0

gamesurface = pygame.Surface((gamesize, gamesize))
gamechanges = Queue() # tuple(x, y, width, height, color)

randsurface = pygame.Surface((50*6, gamesize))

holepos = 0
real_fps = 0
into15 = False

filled = -1

# logger
lastloglen = 0

class Tower(Actor):
    def __init__(self, coloridx:int=1, pos:Tuple[int, int]=(49, 49)):
        super().__init__('tower.png', (255, 255, 255))
        self.rect.center = pos
        self.health = 100
        self.bullet = 0
        self.coloridx = coloridx
    def update(self):
        global Bullet, real_fps
        super().update()
        self.rotate += 1
        bulletcnt = len(busy_bullet)
        for i in range(10):
            if self.bullet > 0 and random.random() > (bulletcnt-500)/500 and random.random() > (30-real_fps)/20: # 根据场上子弹数与当前帧数限制发射
                make_bullet(self.coloridx)
                self.bullet -= 1
        
        if self.health <= 0:
            self.kill()

class Bullet(Actor):
    def __init__(self):
        global towers
        super().__init__('empty.png', (255, 255, 255))
        self.rect.width = self.rect.height = 1
        self.step = 3
        # 以下的数值其实用不上
        self.truex, self.truey = self.rect.center = self.addx, self.addy = (0,0)
        self.coloridx = 1
        # logger
        self.duang = 999999999 # 如果碰撞过墙壁，则记录其死因与用时
    def update(self):
        super().update()
        global gamesize, blocks, gamechanges, tickcnt
        for i in range(self.step):
            self.truex += self.addx
            self.truey += self.addy
            self.rect.centerx, self.rect.centery = self.truex, self.truey
            # 碰到边缘就反弹
            if self.rect.left < 0 or self.rect.right > gamesize-1:
                self.addx = -self.addx
                self.truex += self.addx
                # logger
                if self.duang == 999999999:
                    self.duang = tickcnt
            if self.rect.top < 0 or self.rect.bottom > gamesize-1:
                self.addy = -self.addy
                self.truey += self.addy
                # logger
                if self.duang == 999999999:
                    self.duang = tickcnt
            self.rect.centerx, self.rect.centery = self.truex, self.truey

            for tower in towers:
                if self.rect.colliderect(tower.rect):
                    if tower.coloridx != self.coloridx:
                        tower.health -= 1
                        self.free()
            
            for i in range(-1,1):
                for j in range(-1,1):
                    if blocks[self.rect.left+i, self.rect.top+j] != self.coloridx and self.rect.left+i >= 0 and self.rect.right+i < gamesize-1 and self.rect.top+j >= 0 and self.rect.bottom+j < gamesize-1:
                        gamechanges.put((self.rect.left+i-1, self.rect.top+j-1, 3, 3, self.coloridx))
                        # logger
                        if self.duang == tickcnt:
                            print(f'{self.coloridx}颜色子弹因碰撞{blocks[self.rect.left+i, self.rect.top+j]}颜色方块（坐标：{self.truex, self.truey, self.rect.center}）而死亡，用时{tickcnt-self.duang}帧')
                        self.free()

            for i in pygame.sprite.spritecollide(self, sprite_groups.get(Square, pygame.sprite.Group()), False):
                if i.coloridx == self.coloridx:
                    i.num += 1
                    self.free()
                else:
                    i.num -= 1
                    if i.num <= 0:
                        i.kill()
                    self.free()


    def free(self):
        self.remove(busy_bullet)
        self.add(free_bullet)
        
    def draw(self, surface):
        pygame.draw.rect(surface, (255,255,255), self.rect)

class Square(Actor):
    def __init__(self, coloridx:int=1, num:int=1):
        super().__init__('empty.png', (255, 255, 255))
        global towers
        self.rect.center = towers[coloridx-1].rect.center
        self.coloridx = coloridx
        self.num = num
        self.addx, self.addy = dir2pos(towers[coloridx-1].rotate, 5)
        self.colliding = set()
    def update(self):
        super().update()
        if self.num <= 0:
            self.kill()
        try:
            self.rect.width = self.rect.height = log2(sqrt(self.num))*10+10
        except ValueError as e:
            print(self.num, e)
        self.rect.centerx += self.addx
        self.rect.centery += self.addy
        if self.rect.left < 0:
            self.rect.left = 0
            self.addx = -self.addx
        if self.rect.right > gamesize-1:
            self.rect.right = gamesize-1
            self.addx = -self.addx
        if self.rect.top < 0:
            self.rect.top = 0
            self.addy = -self.addy
        if self.rect.bottom > gamesize-1:
            self.rect.bottom = gamesize-1
            self.addy = -self.addy
        
        for i in pygame.sprite.spritecollide(self, sprite_groups[Tower], False):
            if i.coloridx != self.coloridx:
                if self.num <= 0:
                    self.kill()
                    break
                damage = random.randint(self.num//2, self.num)
                i.health -= damage
                self.num -= damage
                if abs(self.rect.x-i.rect.x) > abs(self.rect.y-i.rect.y):
                    self.addx = -self.addx
                else:
                    self.addy = -self.addy

        mask = blocks[self.rect.left:self.rect.right, self.rect.top:self.rect.bottom] != self.coloridx
        gamechanges.put((self.rect.left, self.rect.top, self.rect.width, self.rect.height, self.coloridx))
        self.num -= mask.sum()

        collided = self.colliding.copy()
        self.colliding.clear()
        for i in pygame.sprite.spritecollide(self, sprite_groups[Square], False):
            if i is self: continue
            self.colliding.add(i)
            if i in collided: continue
            if abs(self.rect.x-i.rect.x) > abs(self.rect.y-i.rect.y):
                self.addx = -self.addx
            else:
                self.addy = -self.addy
            if i.coloridx != self.coloridx:
                if self.num <= 0:
                    self.kill()
                    break
                damage = random.randint(self.num//2, self.num)
                i.num -= damage
                self.num -= damage

    def draw(self, surface):
        pygame.draw.rect(surface, colormap[self.coloridx], self.rect)
        pygame.draw.rect(surface, (255,255,255), self.rect, 1)
        draw_text(ez_num(self.num), self.rect.centerx, self.rect.centery, 20, surface=surface)

class Mkrand(Actor):
    def __init__(self, coloridx:int=1):
        super().__init__('empty.png')
        self.rect.width = self.rect.height = 1
        self.coloridx = coloridx
        self.num = 1
        self.rect.centerx = self.coloridx*50+25
        self.rect.centery = 50
    
    def update(self):
        super().update()
        global towers, holepos, gamesize, tickcnt

        if self.rect.colliderect(pygame.Rect(0, gamesize/3*2-25, 300, 25)):
            self.rect.centery = gamesize/3*2+50
            self.rect.centerx = holepos*50+25
        if self.rect.colliderect(pygame.Rect(0, gamesize/3*2+100, 300, 25)):
            holeidx = (self.rect.centerx-25) // 50 
            if holeidx == 0:
                self.num *= 1.5 + (13.5*into15)
                self.num = int(self.num)
            if holeidx == 1:
                self.num *= 2
            if holeidx == 2:
                self.num *= 3
            if self.num > 100:
                if holeidx == 3:
                    towers[self.coloridx-1].health += self.num
                    self.num = 1
                    if towers[self.coloridx-1].health > 10000000:
                        self.num = towers[self.coloridx-1].health-10000000
                        towers[self.coloridx-1].health = 10000000
                if holeidx == 4:
                    towers[self.coloridx-1].bullet += self.num
                    self.num = 1
                    if towers[self.coloridx-1].bullet > 10000000:
                        self.num = towers[self.coloridx-1].bullet-10000000
                        towers[self.coloridx-1].bullet = 10000000
                if holeidx == 5:
                    Square(self.coloridx, self.num)
                    self.num = 1
            else:
                self.num *= random.randint(2,10)

            self.rect.centery = random.randint(0, 100)
            self.rect.centerx = self.coloridx*50+25
        self.rect.y += random.randint(10, 15)

        if tickcnt > 3000:
            self.num *= random.uniform(1,1.1)
            self.num = int(self.num)

        if towers[self.coloridx-1].health <= 0:
            self.kill()
    
    def draw(self, surface):
        pygame.draw.circle(surface, colormap[self.coloridx], (self.rect.centerx+gamesize, self.rect.centery), 10)
        draw_text(ez_num(self.num), self.rect.centerx+gamesize, self.rect.centery-20, 20, (255, 255, 255), surface=surface)


def make_bullet(coloridx:int=1):
    global free_bullet, busy_bullet
    bullet = free_bullet.sprites()[0]
    bullet.coloridx = coloridx
    bullet.rect.center = towers[coloridx-1].rect.center
    bullet.addx, bullet.addy = dir2pos(towers[coloridx-1].rotate, 1)
    bullet.addx += random.uniform(-0.1, 0.1)
    bullet.addy += random.uniform(-0.1, 0.1)
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

    for j in range(5):
        for i in range(1,5):
            Mkrand(i)
    
    free_bullet = pygame.sprite.Group()
    for i in range(1000):
        free_bullet.add(Bullet())
    busy_bullet = pygame.sprite.Group()

    for i in range(6):
        pygame.draw.aaline(randsurface, (255, 255, 255), (i*50, gamesize/3*2), (i*50, gamesize/3*2+100))
    draw_text('*1.5', 25, gamesize/3*2+25, 20, (255, 255, 255), surface=randsurface)
    draw_text('*2', 75, gamesize/3*2+25, 20, (255, 255, 255), surface=randsurface)
    draw_text('*3', 125, gamesize/3*2+25, 20, (255, 255, 255), surface=randsurface)
    draw_text('加血', 175, gamesize/3*2+25, 20, (255, 255, 255), surface=randsurface)
    draw_text('子弹', 225, gamesize/3*2+25, 20, (255, 255, 255), surface=randsurface)
    draw_text('方块', 275, gamesize/3*2+25, 20, (255, 255, 255), surface=randsurface)
    pygame.draw.rect(randsurface, (0, 0, 255), pygame.Rect(0, gamesize/3*2-25, 300, 25))
    pygame.draw.rect(randsurface, (0, 255, 0), pygame.Rect(0, gamesize/3*2+100, 300, 25))

def update():
    global gamechanges, addbullet, tickcnt, busy_bullet, holepos, into15, filled
    sprite_groups[Tower].update()
    busy_bullet.update()
    sprite_groups[Mkrand].update()
    try:
        sprite_groups[Square].update()
    except KeyError: pass
    # for _ in range(1000):
    #     gamechanges.put((random.randint(0, gamesize-1), random.randint(0, gamesize-1), 1, 1, random.randint(1, 4)))
    tickcnt += 1
    # if tickcnt % 6 == 0:
    #     if random.random() < 0.1:
    #         random.choice(towers).bullet += addbullet
    #         addbullet = 1
    #     addbullet *= 2
    
    if tickcnt % 1 == 0:
        holepos += 1
        if holepos > 5:
            holepos = 0

    if tickcnt == 1*60*20:
        pygame.draw.rect(randsurface, (0,0,0), pygame.Rect(26, 362, 5, 10))
        into15 = True

    if np.sum(blocks != blocks[10, 10]) / np.size(blocks) < 0.05 and blocks[10, 10] != 0 and filled == -1:
        filled = tickcnt
        # logger
        print(blocks, blocks[10, 10], np.sum(blocks != blocks[10, 10]) / np.size(blocks), np.size(blocks), filled, running)
    if tickcnt - filled > 15*20 and filled != -1:
        close()

# @timer
def draw():
    global blocks, colormap, gamechanges, gamesurface, towers, starttime, real_fps, recorder, filled, lastloglen
    while not gamechanges.empty():
        x, y, width, height, color = gamechanges.get()
        blocks[x:x+width-1, y:y+height-1] = color
        pygame.draw.rect(gamesurface, colormap[color], pygame.Rect(x, y, width, height))
    screen.blit(gamesurface, (0, 0))
    screen.blit(randsurface, (gamesize, 0))
    sprite_groups[Tower].draw(screen)
    for i in busy_bullet.sprites():
        i.draw(screen)

    for i in sprite_groups[Mkrand].sprites():
        i.draw(screen)
    
    try:
        for i in sprite_groups[Square].sprites():
            i.draw(screen)
    except KeyError: pass

    for tower in towers:
        # pygame.draw.rect(screen, (255, 255, 255), tower.rect, 5)
        draw_text(f'子弹：{ez_num(tower.bullet)}', tower.rect.centerx, tower.rect.centery+30, 18, (0,0,0))
        draw_text(f'防御：{ez_num(tower.health)}', tower.rect.centerx, tower.rect.centery-30, 18, (0,0,0))

    pygame.draw.circle(screen, (255, 255, 255), (gamesize+holepos*50+25, gamesize/3*2+50), 10)

    real_fps = 1/(time.time()-starttime)
    pygame.display.set_caption(f'fps: {1/(time.time()-starttime):.1f}{" - 乱斗模式已开启"*into15}{f" - 已霸屏{tickcnt-filled}帧"*(filled!=-1)}')

    recorder.add_frame(screen, others={'server_fps': real_fps, 'into15': into15, 'filled': filled, 'tickcnt': tickcnt})

    # logger
    log_content = f'{len(busy_bullet.sprites())},{real_fps},{len(sprite_groups.get(Square, []))},{filled},{tickcnt}'
    print(' '*lastloglen + '\r' + log_content, end='\r')
    lastloglen = len(log_content)
    starttime = time.time()

def getevent(event:pygame.event.Event):
    if event.type == pygame.MOUSEBUTTONDOWN:
        print(event.pos)
    
init()
starttime = time.time()
import live
recorder = live.Live()
go(draw=draw, update=update, screensize=SCREENSIZE, getevent=getevent)
recorder.close()