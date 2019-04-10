"""
Network.py, an experimental clone of KDE's KNetwalk.
Copyright (C) 2010-12  Edmund Horner
"""
import random


class AI(object):
    def __init__(self, map):
        self.map = map
        self.solve_stack = []
        self.experimental = False

        self.map_stack = []

    def set_live(self, tile):
        if tile.live_end:
            return False
        tile.live_end = True
        self.solve_stack.append((tile.y, tile.x))
        return False

    def set_dead(self, tile):
        if tile.dead_end:
            return False
        tile.dead_end = True
        self.solve_stack.append((tile.y, tile.x))
        return False

    def set_solved(self, tile):
        if tile.possibles == tile.ports and tile.necessaries == tile.ports:
            return False
        tile.possibles = tile.ports
        tile.necessaries = tile.ports
        self.solve_stack.append((tile.y, tile.x))
        return True

    def set_not_possible(self, tile, k):
        if not tile.possibles[k]:
            return False
        tile.possibles[k] = False
        self.solve_stack.append((tile.y, tile.x))
        return False

    def set_necessary(self, tile, k):
        if tile.necessaries[k]:
            return False
        tile.necessaries[k] = True
        self.solve_stack.append((tile.y, tile.x))
        return False

    def check_consistency(self, tile):
        ns = self.map.get_neighbours(tile)
        for k in range(4):
            if not ns[k] and tile.necessaries[k]:
                return False
            if not ns[k]:
                continue
            if tile.necessaries[k] and not ns[k].possibles[(k + 2) % 4]:
                return False
            if not tile.possibles[k] and ns[k].necessaries[(k + 2) % 4]:
                return False
            if tile.necessaries[k] and not tile.possibles[k]:
                return False
        return True

    def solve_one(self):
        if len(self.solve_stack) == 0:
            for i in range(self.map.height):
                for j in range(self.map.width):
                    self.solve_stack.append((i, j))
            random.Random().shuffle(self.solve_stack)

        while len(self.solve_stack) > 0:
            i, j = self.solve_stack.pop()
            tile = self.map.tiles[i][j]
            ns = self.map.get_neighbours(tile)

            if not self.check_consistency(tile):
                self.rollback_guess()
                self.solve_stack = []
                return True

            if tile.source is not None:
                if self.set_live(tile): return True

            if sum(tile.ports) == 1:
                if self.set_dead(tile): return True

            # If most connected neighbours are dead ends, so's this.
            if not tile.dead_end:
                not_deads = 0
                for k in range(4):
                    if not tile.possibles[k]:
                        continue
                    if ns[k] and (not ns[k].dead_end or not ns[k].locked):
                        not_deads += 1
                if not_deads <= 1:
                    if self.set_dead(tile): return True

            # If at least one connected neighbours is a live end, so's this.
            if not tile.live_end:
                lives = 0
                for k in range(4):
                    if not tile.necessaries[k]:
                        continue
                    if ns[k] and ns[k].live_end:
                        lives += 1
                if lives >= 1:
                    if self.set_live(tile): return True

            if tile.locked or not any(tile.ports):
                if self.set_solved(tile): return True
                continue
            if sum(tile.possibles) == sum(tile.ports):
                tile.ports = tile.possibles
                if not tile.locked:
                    tile.locked = True
                    self.solve_stack.append((tile.y, tile.x))
                    for n in ns:
                        if n: self.solve_stack.append((n.y, n.x))
                    continue
            if sum(tile.necessaries) == sum(tile.ports):
                tile.ports = tile.necessaries
                if not tile.locked:
                    tile.locked = True
                    self.solve_stack.append((tile.y, tile.x))
                    for n in ns:
                        if n: self.solve_stack.append((n.y, n.x))
                    continue

            # If all but one of my possible neighbours is dead, then the one remaining
            # one is necessary.
            num_deads = 0
            not_dead = None
            for k in range(4):
                if not tile.possibles[k]:
                    continue
                if ns[k] and ns[k].dead_end:
                    num_deads += 1
                elif not tile.necessaries[k]:
                    not_dead = k
            if not_dead is not None and num_deads == sum(tile.possibles) - 1:
                if self.experimental:
                    tile.necessaries[not_dead] = True
                    tile.mark = True
                    return True

            ns = self.map.get_neighbours(tile)
            for k in range(4):
                # Copy necessary and possible information from neighbours
                if ns[k] and not ns[k].possibles[(k + 2) % 4]:
                    if self.set_not_possible(tile, k): return True
                if ns[k] and ns[k].necessaries[(k + 2) % 4]:
                    if self.set_necessary(tile, k): return True
                if tile.ports in [[True,False,True,False], [False,True,False,True]]:
                    # If it's a horizontal or vertical pipe, the opposite of necessary is necessary
                    if ns[k] and ns[k].necessaries[(k + 2) % 4]:
                        if self.set_necessary(tile, (k + 2) % 4): return True
                    # And the opposite of impossible is impossible
                    if ns[k] and not ns[k].possibles[(k + 2) % 4]:
                        if self.set_not_possible(tile, (k + 2) % 4): return True
                elif sum(tile.ports) == 2:
                    # If it's a corner, the opposite of a necessary is impossible
                    if ns[k] and ns[k].necessaries[(k + 2) % 4]:
                        if self.set_not_possible(tile, (k + 2) % 4): return True
                    # And the opposite if impossible is necessary
                    if ns[k] and not ns[k].possibles[(k + 2) % 4]:
                        if self.set_necessary(tile, (k + 2) % 4): return True
                elif sum(tile.ports) == 1:
                    # If it's an endpoint and the neighbour is an endpoint, that connection is impossible
                    if ns[k] and sum(ns[k].ports) == 1:
                        if self.set_not_possible(tile, k): return True

                # If I'm live, and the neighbour not necessary and also live, then
                # it's impossible.
                if tile.live_end and ns[k] and ns[k].live_end and not tile.necessaries[k]:
                    if self.set_not_possible(tile, k): return True

                # Check if nearest three edges are necessary, if so this is impossible
                if self.experimental:
                    neccs = True
                    n = tile
                    for i in range(3):
                        n = self.map.get_neighbours(n)[(k+i) % 4]
                        if not n.necessaries[(k+i+1) % 4]:
                            neccs = False
                            break
                    if neccs:
                        if self.set_not_possible(tile, k): return True

        if len(self.solve_stack) > 0:
            return True
        if self.experimental:
            return self.make_guess()
        return True

    def make_guess(self):
        tile = None
        for i in range(self.map.height):
            for j in range(self.map.width):
                if not self.map.tiles[i][j].locked:
                    tile = self.map.tiles[i][j]
                    break

        if tile is None:
            return False

        tile.rotate(1)
        tile.ai_rotations += 1
        if tile.ai_rotations > 4:
            self.rollback_guess()
            return True

        self.map_stack.append(self.map.tiles)
        self.map.tiles = self.map.clone_tiles()
        t2 = self.map.tiles[tile.y][tile.x]
        t2.locked = True
        t2.possibles = t2.ports
        t2.necessaries = t2.ports

        self.solve_stack.append((tile.y, tile.x))

        return True

    def rollback_guess(self):
        self.map.tiles = self.map_stack.pop()
