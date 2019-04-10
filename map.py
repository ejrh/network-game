"""
Network.py, an experimental clone of KDE's KNetwalk.
Copyright (C) 2010-12  Edmund Horner
"""
import random


HEAT_DECAY = (-0.015, -0.015, -0.015)

MAX_DISTANCE = 30


def heat_flow(h1, h2):
    a = max(0, h1[0] - h2[0]) / 2.0
    b = max(0, h1[1] - h2[1]) / 2.0
    c = max(0, h1[2] - h2[2]) / 2.0
    return a,b,c


def heat_add(h1, h2):
    a = h1[0] + h2[0]
    b = h1[1] + h2[1]
    c = h1[2] + h2[2]
    return a,b,c


def heat_collar(h):
    a = max(0.0, min(h[0], 1.0))
    b = max(0.0, min(h[1], 1.0))
    c = max(0.0, min(h[2], 1.0))
    return a,b,c


class Tile(object):
    def __init__(self, x, y, ports=[False]*4, source=None):
        self.x = x
        self.y = y
        self.ports = ports[:]
        self.source = source
        self.true_ports = ports[:]
        self.locked = False
        if source == 0:
            self.heat = (1.0, 0.0, 0.0)
        elif source == 1:
            self.heat = (0.0, 1.0, 0.0)
        elif source == 2:
            self.heat = (0.0, 0.0, 1.0)
        else:
            self.heat = (0.0, 0.0, 0.0)
        self.prev_heat = (0.0, 0.0, 0.0)
        self.possibles = [True]*4
        self.necessaries = [False]*4
        self.dead_end = False
        self.live_end = False
        self.mark = False
        self.ai_rotations = 0
        self.distance = 0

    def rotate(self, steps=1):
        self.ports = self.ports[steps:] + self.ports[:steps]
        if self.source is None:
            self.heat = (0.0, 0.0, 0.0)

    def clone(self):
        t = Tile(self.x, self.y)

        for n in dir(self):
            if n[0] != '_':
                v = getattr(self, n)
                if type(v) == list:
                    v = v[:]
                elif callable(v):
                    continue
                setattr(t, n, v)

        return t


class Map(object):

    DEFAULT_WIDTH=9
    DEFAULT_HEIGHT=9

    def __init__(self, width, height, torus=False, num_seeds=1):
        self.width = self.DEFAULT_WIDTH
        self.height = self.DEFAULT_HEIGHT
        self.torus = False
        self.num_seeds = num_seeds
        self.clear(width, height, torus, num_seeds)

    def clear(self, width=None, height=None, torus=None, num_seeds=None):
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height
        if torus is not None:
            self.torus = torus
        if num_seeds is not None:
            self.num_seeds = num_seeds
        self.tiles = [None]*self.height
        for i in range(self.height):
            self.tiles[i] = [None]*self.width
        self.sinks = 0
        self.lights = 0
        self.locks = 0

    def clone_tiles(self):
        new_tiles = [None]*self.height
        for i in range(self.height):
            new_tiles[i] = [None]*self.width

        for i in range(self.height):
            for j in range(self.width):
                new_tiles[i][j] = self.tiles[i][j].clone()

        return new_tiles

    def generate(self):
        seeds = []
        for k in range(self.num_seeds):
            i = random.randint(0, self.height - 1)
            j = random.randint(0, self.height - 1)
            t = Tile(j, i, source=k%3)
            self.tiles[i][j] = t
            seeds.append([t])

        next_seed = 0
        while any(seeds):
            seed_list = seeds[next_seed]
            if len(seed_list) == 0:
                next_seed = (next_seed+1) % self.num_seeds
                continue
            r = random.randint(0,len(seed_list)-1)
            s = seed_list[r]
            ns = self.get_neighbours(s)
            if all([n is not None for n in ns]):
                seeds[next_seed] = seed_list[:r] + seed_list[r+1:]
                continue
            r = random.randint(0,3)
            if ns[r] is not None:
                continue
            x,y = self.get_coords(s.x, s.y, r)
            t = Tile(x, y)
            t.distance = s.distance + 1
            self.tiles[y][x] = t
            if sum(s.ports) < 3:
                s.ports[r] = True
                t.ports[(r+2)%4] = True
                if t.distance < MAX_DISTANCE:
                    seed_list.append(t)
                next_seed = (next_seed+1) % self.num_seeds

        # Fill in any remaining empty tiles
        for i,row in enumerate(self.tiles):
            for j,tile in enumerate(row):
                if tile is None:
                    row[j] = Tile(j,i)

        for row in self.tiles:
            for t in row:
                t.true_ports = t.ports[:]
                t.rotate(random.randint(0,3))
                if sum(t.ports) == 1 and t.source is None:
                    self.sinks += 1
                if sum(t.ports) == 0:
                    self.locked = True

    def get_neighbours(self, s):
        ns = [False]*4

        if self.torus:
            for i in range(4):
                x,y = self.get_coords(s.x, s.y, i)
                ns[i] = self.tiles[y][x]
            return ns

        if s.y > 0:
            ns[0] = self.tiles[s.y-1][s.x]
        if s.x > 0:
            ns[1] = self.tiles[s.y][s.x-1]
        if s.y < self.height-1:
            ns[2] = self.tiles[s.y+1][s.x]
        if s.x < self.width-1:
            ns[3] = self.tiles[s.y][s.x+1]
        return ns

    def get_coords(self, x, y, num):
        if num == 0:
            x,y = x, y-1
        elif num == 1:
            x,y = x-1, y
        elif num == 2:
            x,y = x, y+1
        else:
            x,y = x+1, y

        x = x % self.width
        y = y % self.height
        return x, y

    def update(self):
        adj = []
        for i in range(self.height):
            adj.append([HEAT_DECAY]*self.width)

        for i in range(self.height):
            for j in range(self.width):
                if self.tiles[i][j] in [None,False]:
                    continue
                if self.tiles[i][j].source is None:
                    ns = self.get_neighbours(self.tiles[i][j])
                    for k in range(4):
                        if ns[k] not in [False,None] and self.tiles[i][j].ports[k] and ns[k].ports[(k + 2) % 4]:
                            d = heat_flow(ns[k].heat, self.tiles[i][j].heat)
                            adj[i][j] = heat_add(adj[i][j], d)

        changed = False
        self.lights = 0
        self.locks = 0
        for i in range(self.height):
            for j in range(self.width):
                tile = self.tiles[i][j]
                if tile in [None,False]:
                    continue
                if tile.source is None:
                    tile.prev_heat = tile.heat
                    tile.heat = heat_collar(heat_add(tile.heat, adj[i][j]))
                    changed |= (tile.heat != tile.prev_heat)

                if sum(tile.ports) == 1 and tile.source is None:
                    if tile.heat != (0.0, 0.0, 0.0) and sum(tile.heat) >= sum(tile.prev_heat):
                        self.lights += 1

                if tile.locked:
                    self.locks += 1

        return changed

    def solve(self):
        for row in self.tiles:
            for t in row:
                t.ports = t.true_ports

    def scroll(self, dx, dy):
        dx = (dx + self.width) % self.width
        dy = (dy + self.height) % self.height
        if dy != 0:
            self.tiles = self.tiles[dy:] + self.tiles[:dy]
        if dx != 0:
            for i in range(self.height):
                self.tiles[i] = self.tiles[i][dx:] + self.tiles[i][:dx]

        for row in self.tiles:
            for tile in row:
                tile.x = (tile.x - dx) % self.width
                tile.y = (tile.y - dy) % self.height
