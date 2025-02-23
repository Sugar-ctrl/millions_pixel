'''
自制的Pygame Zero
完美支持IDE自动补全
导入后附带pygame的内容（直接使用`pygame.xxx`即可）
建议使用from import *导入
'''
import math
from typing import Callable, Tuple, List, Dict
import pygame
import os

WIDTH, HEIGHT = 500, 500
FPS = 60
TITLE = 'my pygame zero'

all_sprites: pygame.sprite.Group = pygame.sprite.Group()
sprite_groups: Dict[type, pygame.sprite.Group] = {}

pygame.init()
pygame.mixer.init()
screen: pygame.Surface = pygame.display.set_mode((WIDTH, HEIGHT))

def draw_text(
    text: str, 
    x: int, 
    y: int, 
    size: int = 18, 
    color: Tuple[int, int, int] = (0, 0, 0), 
    fontname: str = ''
) -> None:
    '''
    绘制文字
    参数：
    text: 文字内容
    x: 横坐标
    y: 纵坐标
    size: 字体大小
    color: 字体颜色
    fontname: 字体名称
    '''
    try:
        font = pygame.font.Font(fontname, size)
    except:
        font = pygame.font.Font(f'{os.path.abspath(__file__)}/../MSYH.TTC')
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.centerx = x
    text_rect.centery = y
    screen.blit(text_surface, text_rect)

class Actor(pygame.sprite.Sprite):
    '''
    角色类
    参数：
    picture: 贴图名称
    colourkey: 贴图透明色
    scale: 贴图缩放后的长宽
    
    注：如果使用scale指定长宽，则不能使用旋转
    '''
    def __init__(
        self, 
        picture: str, 
        colourkey: Tuple[int, int, int] = None, 
        scale: Tuple[int, int] = None
    ) -> None:
        pygame.sprite.Sprite.__init__(self)

        if colourkey:
            self.__genimage__ = pygame.image.load('images/' + picture).convert()
            self.image = pygame.image.load('images/' + picture).convert()
            try: 
                self.image = pygame.transform.scale(self.image, scale)
            except: pass
        else:
            self.__genimage__ = pygame.image.load('images/' + picture).convert_alpha()
            self.image = pygame.image.load('images/' + picture).convert_alpha()
            try: 
                self.image = pygame.transform.scale(self.image, scale)
            except: pass
        self.colorkey = colourkey
        self.scale = scale
        all_sprites.add(self)
        if sprite_groups.get(type(self)):
            sprite_groups[type(self)].add(self)
        else:
            sprite_groups[type(self)] = pygame.sprite.Group()
            sprite_groups[type(self)].add(self)
        self.rect = self.image.get_rect()
        self.image.set_colorkey(colourkey)
        self.radius = 23
        self.group = '__none__'
        self.rotate = 0 # 正数是逆时针
        self.__ro__ = self.rotate

    def update(self) -> None:
        '''
        角色每一帧执行的内容
        '''
        if self.__ro__ != self.rotate:
            self.__ro__ = self.rotate
            self.__ro__ %= 360; self.rotate %= 360
            self.ce = self.rect.center

            if self.colorkey:
                self.image = pygame.transform.rotate(self.__genimage__, self.__ro__)
                try: 
                    self.image = pygame.transform.scale(self.image, self.scale)
                except: pass
                self.image.set_colorkey(self.colorkey)
            else:
                self.image = pygame.transform.rotate(self.__genimage__, self.__ro__).convert_alpha()
                try: 
                    self.image = pygame.transform.scale(self.image, self.scale)
                except: pass

            self.rect = self.image.get_rect()
            self.rect.center = self.ce
    
def calc_dir(
    angle: float, 
    length: float
) -> Tuple[float, float]:
    '''
    通过角度和距离计算x和y分别增加多少
    参数：
    angle: 角度
    length: 距离
    返回：
    (x, y)
    '''
    return (length * math.cos(math.radians(angle)), -length * math.sin(math.radians(angle)))
            
def go(
    update: Callable[[], None] = lambda: None,
    draw: Callable[[], None] = lambda: all_sprites.draw(screen),
    getevent: Callable[[pygame.event.Event], None] = lambda event: None,
    background: str = '',
    screensize: Tuple[int, int] = (WIDTH, HEIGHT),
    title: str = TITLE,
    bgcolor: Tuple[int, int, int] = (0, 0, 0),
    fps: int = FPS
) -> None:
    '''
    运行游戏
    需放在一切的最后，进行最终的配置
    参数：
    update: 每一帧执行的内容
    draw: 每一帧绘制的内容
    getevent: 获取事件的回调
    background: 背景图片路径
    screensize: 游戏窗口的长宽

    '''
    
    screen = pygame.display.set_mode(screensize)
    pygame.display.set_caption(title)
    clock = pygame.time.Clock()
    try:
        bgimg = pygame.image.load('images/' + background).convert()
        background_img = pygame.transform.scale(bgimg, (screensize[0], screensize[1]))
    except:
        pass
    running = True
    while running:
        clock.tick(fps)
        for event in pygame.event.get():
            getevent(event)
            if event.type == pygame.QUIT:
                running = False
        # 更新
        all_sprites.update()
        update()

        # 显示
        screen.fill(bgcolor)
        try:
            screen.blit(background_img, (0, 0))
        except: pass
        draw()
        pygame.display.update()
    pygame.quit()

if __name__ == '__main__':
    a = lambda *org: print('这不是直接运行用的！')
    go(a, a, a)
