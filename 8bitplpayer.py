import pygame
import json
import numpy as np
import bisect
from pygame.locals import *

class ChiptunePlayer:
    def __init__(self, max_channels=4):
        # 初始化立体声混音器
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self.channels = {
            'pulse1': pygame.mixer.Channel(0),
            'pulse2': pygame.mixer.Channel(1),
            'triangle': pygame.mixer.Channel(2),
            'noise': pygame.mixer.Channel(3)
        }
        self.sound_cache = {}
        self.loop = True  # 新增循环控制属性
        self.playing = False
        self.current_time = 0.0
        self.last_update = 0.0

    def _generate_wave(self, wave_type, freq, duration, **params):
        """生成波形数据（最终修正版）"""
        sample_rate = 44100
        length = int(sample_rate * duration)
        t = np.linspace(0, duration, length, dtype=np.float64)

        # 生成基础波形（保持原有代码）
        if wave_type == 'square':
            duty = params.get('duty_cycle', 0.5)
            wave = np.where(np.sin(2 * np.pi * freq * t) > 2*duty-1, 1.0, -1.0)
        elif wave_type == 'triangle':
            phase = (freq * t) % 1
            wave = 2 * np.abs(2 * phase - 1) - 1
        elif wave_type == 'noise':
            wave = np.random.uniform(-1, 1, len(t))
        else:
            wave = np.zeros(len(t))

        # 转换为立体声格式
        arr = (wave * 32767).clip(-32768, 32767).astype(np.int16)
        stereo_arr = np.repeat(arr.reshape(-1, 1), 2, axis=1)  # 单声道转立体声
        
        return pygame.sndarray.make_sound(stereo_arr)

    def load(self, json_path):
        with open(json_path) as f:
            data = json.load(f)
        
        self.metadata = data['metadata']
        self.instruments = data['instruments']
        self.score = sorted(data['score'], key=lambda x: x['time'])
        self.event_times = [ev['time'] for ev in self.score]
        
        # 预生成所有需要的音频
        self._precache_sounds()

    def _precache_sounds(self):
        """预生成所有音符的音频样本"""
        for ev in self.score:
            instr = self.instruments[ev['channel']]
            key = (ev['channel'], ev['note'], ev['duration'])
            if key not in self.sound_cache:
                freq = self._note_to_freq(ev['note'])
                wave_type = instr['waveform']
                params = {k:v for k,v in instr.items() if k != 'waveform'}
                self.sound_cache[key] = self._generate_wave(
                    wave_type, freq, ev['duration'], **params)

    def _note_to_freq(self, note):
        """转换音符到频率（A4=440Hz标准）"""
        if isinstance(note, (int, float)):
            return 440.0 * 2 ** ((note - 69) / 12)
        midi_map = {'C':0, 'C#':1, 'D':2, 'D#':3, 'E':4, 'F':5, 
                   'F#':6, 'G':7, 'G#':8, 'A':9, 'A#':10, 'B':11}
        octave = int(note[-1])
        tone = midi_map[note[:-1].upper()]
        return 440.0 * 2 ** ((octave-4) + (tone-9)/12)

    def play(self):
        self.playing = True
        self.current_time = 0.0
        self.last_update = pygame.time.get_ticks() / 1000.0

    def stop(self):
        self.playing = False
        for ch in self.channels.values():
            ch.stop()

    def update(self):
        if not self.playing:
            return
        
        # 基于实际流逝时间计算
        now = pygame.time.get_ticks() / 1000.0
        delta = now - self.last_update
        self.last_update = now
        self.current_time += delta

        # 处理循环逻辑
        if self.loop and self.current_time > self.metadata['duration']:
            self.current_time %= self.metadata['duration']

        # 计算触发时间窗口
        window_start = self.current_time - delta
        window_end = self.current_time

        # 使用二分查找快速定位需要触发的事件
        events = []
        if window_start < window_end:
            left = bisect.bisect_left(self.event_times, window_start)
            right = bisect.bisect_left(self.event_times, window_end)
            events = self.score[left:right]
        else:  # 处理跨循环的情况
            left = bisect.bisect_left(self.event_times, window_start)
            events = self.score[left:]
            right = bisect.bisect_left(self.event_times, window_end)
            events += self.score[:right]

        # 播放触发的事件
        for ev in events:
            channel = self.channels[ev['channel']]
            sound = self.sound_cache[(ev['channel'], ev['note'], ev['duration'])]
            
            # 停止当前通道声音并播放新音符
            channel.stop()
            channel.play(sound, maxtime=int(ev['duration']*1000))

# 使用示例
if __name__ == "__main__":
    player = ChiptunePlayer()
    player.load("8bit_song copy.json")
    player.play()
    
    pygame.init()
    screen = pygame.display.set_mode((400, 300))
    clock = pygame.time.Clock()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
        
        player.update()  # 每帧调用更新
        pygame.display.flip()
        clock.tick(60)  # 帧率不稳定测试时可去掉限制
    
    pygame.quit()