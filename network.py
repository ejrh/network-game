"""
Network.py, an experimental clone of KDE's KNetwalk.
Copyright (C) 2010-11  Edmund Horner
"""
import sys
import pygame

from ai import AI
from map import Map


class Window(object):

    def __init__(self, map, width, height, display):
        self.map = map
        self.width = width
        self.height = height
        self.display = display
        self.font = pygame.font.SysFont(None, 25)
        self.scroll_x = 0
        self.scroll_y = 0
        self.frame = 0


    def scroll(self, dx, dy):
        self.scroll_x += dx
        self.scroll_y += dy
        if not self.map.torus:
            max_x = self.map.width - self.width
            max_y = self.map.height - self.height
            if self.scroll_x < 0:
                self.scroll_x = 0
            if self.scroll_y < 0:
                self.scroll_y = 0
            if self.scroll_x > max_x:
                self.scroll_x = max_x
            if self.scroll_y > max_y:
                self.scroll_y = max_y
        else:
            self.scroll_x = self.scroll_x % self.map.width
            self.scroll_y = self.scroll_y % self.map.height


    def draw(self):
        self.draw_map()
        #pygame.image.save(self.display, 'network%04d.png' % self.frame)
        self.frame += 1

    def get_wire_colour(self, tile):
        a = []
        for i in range(3):
            c = tile.heat[i]
            n = self.frame % 20
            if n > 10:
                f = 1-((n-10)/10.0)
            else:
                f = n/10.0
            if tile.heat[i] >= tile.prev_heat[i]:
                f = 1
            a.append(int(c * f * 255))
        return tuple(a)

    def draw_tile(self, tile, row, col):
        if tile is None or not any(tile.ports):
            pygame.draw.rect(self.display, (50, 50, 100), pygame.Rect(col*50+1, row*50+1, 48, 48))
            return
        if tile.locked:
            pygame.draw.rect(self.display, (50, 100, 150), pygame.Rect(col*50+1, row*50+1, 48, 48))
        else:
            pygame.draw.rect(self.display, (150, 100, 50), pygame.Rect(col*50+1, row*50+1, 48, 48))
        wire_col = self.get_wire_colour(tile)
        if tile.ports[0]:
            pygame.draw.rect(self.display, wire_col, pygame.Rect(col*50+21, row*50+1, 8, 24))
        if tile.ports[1]:
            pygame.draw.rect(self.display, wire_col, pygame.Rect(col*50+1, row*50+21, 24, 8))
        if tile.ports[2]:
            pygame.draw.rect(self.display, wire_col, pygame.Rect(col*50+21, row*50+25, 8, 24))
        if tile.ports[3]:
            pygame.draw.rect(self.display, wire_col, pygame.Rect(col*50+25, row*50+21, 24, 8))
        if tile.source is not None:
            pygame.draw.circle(self.display, (200, 150, 50), (col*50+25, row*50+25), 12)
        if any(tile.ports):
            pygame.draw.circle(self.display, wire_col, (col*50+25, row*50+25), 4)
        if sum(tile.ports) == 1 and tile.source is None:
            pygame.draw.rect(self.display, (100, 200, 100), pygame.Rect(col*50+11, row*50+11, 28, 28))
            if sum(tile.heat) > 0.0 and sum(tile.heat) >= sum(tile.prev_heat):
                pygame.draw.rect(self.display, (250, 250, 0), pygame.Rect(col*50+21, row*50+21, 8, 8))
        #text = self.font.render("%0.2f" % tile.heat, False, (255,255,255))
        #self.display.blit(text, (col*50, row*50))
        extra_str = ""
        if tile.mark:
            extra_str = extra_str + 'M'
        if tile.dead_end:
            extra_str = extra_str + 'D'
        if tile.live_end:
            extra_str = extra_str + 'L'
        text = self.font.render(extra_str, False, (255,255,255))
        self.display.blit(text, (col*50, row*50 + 50 - text.get_height()))

    def draw_mini_tile(self, tile, row, col, offset_x, offset_y):
        if tile is None or not any(tile.ports):
            return
        bg_col = (100, 100, 100)
        if (col - self.scroll_x) % self.map.width < self.width and (row - self.scroll_y) % self.map.height < self.height:
            bg_col = (150, 150, 150)
        if tile.mark:
            bg_col = (255, 255, 255)
        pygame.draw.rect(self.display, bg_col, pygame.Rect(col*6+offset_x, row*6+offset_y, 6, 6))
        wire_col = self.get_wire_colour(tile)
        if tile.ports[0]:
            pygame.draw.rect(self.display, wire_col, pygame.Rect(col*6+offset_x+2, row*6+offset_y, 2,4))
        if tile.ports[1]:
            pygame.draw.rect(self.display, wire_col, pygame.Rect(col*6+offset_x, row*6+offset_y+2, 4,2))
        if tile.ports[2]:
            pygame.draw.rect(self.display, wire_col, pygame.Rect(col*6+offset_x+2, row*6+offset_y+2, 2,4))
        if tile.ports[3]:
            pygame.draw.rect(self.display, wire_col, pygame.Rect(col*6+offset_x+2, row*6+offset_y+2, 4,2))
        if sum(tile.ports) == 1 and tile.source is None:
            pygame.draw.rect(self.display, (100, 200, 100), pygame.Rect(col*6+offset_x+2, row*6+offset_y+2, 2,2))
            if sum(tile.heat) > 0.0 and sum(tile.heat) >= sum(tile.prev_heat):
                pygame.draw.rect(self.display, (250, 250, 0), pygame.Rect(col*6+offset_x+2, row*6+offset_y+2, 2,2))

    def draw_map(self):
        for i in range(self.height):
            for j in range(self.width):
                t = self.map.tiles[(self.scroll_y + i) % self.map.height][(self.scroll_x + j) % self.map.width]
                self.draw_tile(t, i, j)

        info_str = '%d locks, %d lights' % (self.map.locks, self.map.lights)
        if self.map.lights == self.map.sinks:
            info_str = info_str + ', Won!'
        text = self.font.render(info_str, False, (255,255,255))
        self.display.blit(text, (0,0))

        offset_x = self.display.get_size()[0] - 6 * self.map.width - 10
        offset_y = 6
        for i in range(self.map.height):
            for j in range(self.map.width):
                self.draw_mini_tile(self.map.tiles[i][j], i, j, offset_x, offset_y)

    def locate_click(self, x, y):
        x = x / 50
        y = y / 50
        return (x + self.scroll_x) % self.map.width, (y + self.scroll_y) % self.map.height


def main(args=None):
    if args is None:
        args = sys.argv

    WINDOW_WIDTH=9
    WINDOW_HEIGHT=9

    pygame.init()
    display = pygame.display.set_mode((WINDOW_WIDTH * 50, WINDOW_HEIGHT * 50))
    pygame.time.set_timer(pygame.USEREVENT+1, 250)

    map = Map(21,21, True, 3)
    window = Window(map, WINDOW_WIDTH, WINDOW_HEIGHT, display)

    map.generate()
    window.draw()
    pygame.display.flip()

    auto_solve = False

    ai = AI(map)

    click_pos = None

    while True:
        ev = pygame.event.wait()
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                break
            elif ev.key == pygame.K_r:
                map.clear()
                map.generate()
                window.draw()
                pygame.display.flip()
                ai = AI(map)
            elif ev.key == pygame.K_f:
                map.solve()
                window.draw()
                pygame.display.flip()
            elif ev.key == pygame.K_a:
                auto_solve = not auto_solve
            elif ev.key == pygame.K_x:
                ai.experimental = not ai.experimental
            elif ev.key == pygame.K_s:
                ai.solve_one()
                window.draw()
                pygame.display.flip()
            elif ev.key == pygame.K_UP:
                window.scroll(0,-1)
                window.draw()
                pygame.display.flip()
            elif ev.key == pygame.K_DOWN:
                window.scroll(0,1)
                window.draw()
                pygame.display.flip()
            elif ev.key == pygame.K_LEFT:
                window.scroll(-1,0)
                window.draw()
                pygame.display.flip()
            elif ev.key == pygame.K_RIGHT:
                window.scroll(1,0)
                window.draw()
                pygame.display.flip()
        if ev.type == pygame.MOUSEBUTTONDOWN:
            click_pos = ev.pos
            last_temp_scroll_x, last_temp_scroll_y = 0, 0
        elif ev.type == pygame.MOUSEBUTTONUP:
            click_pos2 = ev.pos
            if click_pos is None:
                click_pos = click_pos2
            rel_x = click_pos[0] - click_pos2[0]
            rel_y = click_pos[1] - click_pos2[1]
            if abs(rel_x) < 5 and abs(rel_y) < 5:
                x, y = ev.pos
                x, y = window.locate_click(x, y)
                if x >= 0 and y >= 0 and x < map.width and y < map.height:
                    if ev.button == 1 and not map.tiles[y][x].locked:
                        map.tiles[y][x].rotate(3)
                    elif ev.button == 3 and not map.tiles[y][x].locked:
                        map.tiles[y][x].rotate(1)
                    elif ev.button == 2:
                        map.tiles[y][x].locked = not map.tiles[y][x].locked
                        if not map.tiles[y][x].locked:
                            map.tiles[y][x].possibles = [True]*4
                            map.tiles[y][x].necessaries = [False]*4
                    window.draw()
                    pygame.display.flip()
            else:
                tile_rel_x = int(round(rel_x/50.0))
                tile_rel_y = int(round(rel_y/50.0))
                if tile_rel_x != last_temp_scroll_x or tile_rel_y != last_temp_scroll_y:
                    window.scroll(tile_rel_x - last_temp_scroll_x, tile_rel_y - last_temp_scroll_y)
                    window.draw()
                    pygame.display.flip()
            click_pos = None
        elif ev.type == pygame.USEREVENT+1:
            if click_pos is not None:
                click_pos2 = pygame.mouse.get_pos()
                rel_x = click_pos[0] - click_pos2[0]
                rel_y = click_pos[1] - click_pos2[1]
                tile_rel_x = int(round(rel_x/50.0))
                tile_rel_y = int(round(rel_y/50.0))
                if tile_rel_x != last_temp_scroll_x or tile_rel_y != last_temp_scroll_y:
                    window.scroll(tile_rel_x - last_temp_scroll_x, tile_rel_y - last_temp_scroll_y)
                    window.draw()
                    pygame.display.flip()
                    last_temp_scroll_x, last_temp_scroll_y = tile_rel_x, tile_rel_y

            if auto_solve:
                auto_solve = ai.solve_one()
            if map.update():
                window.draw()
                pygame.display.flip()
        elif ev.type == pygame.QUIT:
            break

    pygame.quit()


try:
    import psyco
    psyco.full()
    #print 'Optimised'
except ImportError:
    #print 'Not optimised'
    pass


if __name__ == '__main__':
    main()
