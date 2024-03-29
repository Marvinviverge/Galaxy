from kivy.config import Config
Config.set('graphics', 'width','900')
Config.set('graphics', 'height','400')

import random
import platform
from kivy.core.window import Window
from kivy.app import App
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import NumericProperty, Clock, ObjectProperty, StringProperty
from kivy.graphics.vertex_instructions import Line, Quad, Triangle
from kivy.graphics.context_instructions import Color
from kivy.lang import Builder
from kivy.core.audio import SoundLoader

Builder.load_file("menu.kv")

class ColoredTriangle(Triangle):
    pass

class TileColor(Quad):
    pass

class MainWidget(RelativeLayout):
    from transforms import transform, transform_2D, transform_perspective
    from user_actions import on_keyboard_down, on_keyboard_up, keyboard_closed, on_touch_down, on_touch_up
    menu_widget = ObjectProperty()
    perspective_point_x = NumericProperty(0)
    perspective_point_y = NumericProperty(0)

    #Génération lignes verticales initiales
    V_NB_LINES = 16
    V_LINES_SPACING = .2
    vertical_lines = []
    #Génération lignes horizontales initiales
    H_NB_LINES = 16
    H_LINES_SPACING = .15
    horizontal_lines = []

    SPEED = .8
    NEWSPEED = SPEED
    current_offset_y = 0 #faire avancer le terrain

    current_y_loop = 0 #faire avancer la tile
    
    SPEED_X = 3
    current_speed_x = 0
    current_offset_x = 0
    #Tiles initiales
    NB_TILES = 20
    tiles = []
    tiles_coordinates = []

    #Génération initiale du vaisseau
    SHIP_WIDTH = .1
    SHIP_HEIGHT = .035
    SHIP_BASE_Y = .04
    ship = None
    ship_coordinate = [(0,0), (0,0), (0,0)]

    state_game_over = False
    state_game_has_started = False
    end_game = False

    menu_title = StringProperty("G   A   L   A   X   Y")
    menu_button_title = StringProperty("START")
    txt_score = StringProperty()
    current_level_txt = StringProperty()

    sound_begin = None
    sound_galaxy = None
    sound_gameover_impact = None
    sound_gameover_voice = None
    sound_music1 = None
    sound_restart = None

    current_level = 1
    next_level_tiles_goal = NB_TILES
    next_level = False

    isJumping = False
    
    def __init__(self, **kwargs):
        super(MainWidget, self).__init__(**kwargs)
        self.init_vertical_lines()
        self.init_horizontal_lines()
        self.init_tiles()
        self.init_ship()
        self.init_audio()
        self.reset_game()
        
        if self.is_desktop():
            self._keyboard = Window.request_keyboard(self.keyboard_closed, self)
            self._keyboard.bind(on_key_down=self.on_keyboard_down)
            self._keyboard.bind(on_key_up=self.on_keyboard_up)
        Clock.schedule_interval(self.update, 1/60)

        self.sound_galaxy.play()

    def go_next_level(self):
        self.current_level += 1
        self.next_level = True
        self.next_level_tiles_goal = int(self.next_level_tiles_goal * 1.5)
        self.NEWSPEED = self.NEWSPEED * 1.15
        

    def init_audio(self):
        self.sound_begin = SoundLoader.load('audio/begin.wav')
        self.sound_galaxy = SoundLoader.load('audio/galaxy.wav')
        self.sound_gameover_impact = SoundLoader.load('audio/gameover_impact.wav')
        self.sound_gameover_voice = SoundLoader.load('audio/gameover_voice.wav')
        self.sound_music1 = SoundLoader.load('audio/music1.wav')
        self.sound_restart = SoundLoader.load('audio/restart.wav')

        self.sound_music1.volume = 1
        self.sound_begin.volume = 0.25
        self.sound_galaxy.volume = 0.25
        self.sound_gameover_impact.volume = 0.6
        self.sound_gameover_voice.volume = 0.25
        self.sound_restart.volume = 0.25

    def reset_game(self):
        self.current_offset_y = 0
        self.current_y_loop = 0
        self.current_speed_x = 0
        self.current_offset_x = 0
        self.txt_score = "Score: " + str(self.current_y_loop)
        self.current_level_txt = "Niveau: " + str(self.current_level)
        self.tiles_coordinates = [] 
        self.pre_fil_tiles_coordinates()
        self.generate_tiles_coordinates()
        self.state_game_over = False
        self.next_level = False

    def is_desktop(self):
        if platform.system() in ('Linux', 'Windows', 'Darwin'):
            return True
        return False
    
    def restore_color(self, dt):
        self.ship_color.rgb = (0, 0, 0)
        self.isJumping = False

    def init_ship(self):
        with self.canvas:
            self.ship_color = Color(0, 0, 0)
            self.ship = ColoredTriangle()

    def update_ship(self):
        center_x = self.width/2
        base_y = self.SHIP_BASE_Y * self.height
        half_width = self.SHIP_WIDTH / 2 * self.width/2
        ship_height = self.SHIP_HEIGHT * self.height

        self.ship_coordinate[0] = (center_x - half_width, base_y)
        self.ship_coordinate[1] = (center_x, base_y + ship_height)
        self.ship_coordinate[2] = (center_x + half_width, base_y)

        x1, y1 = self.transform(*self.ship_coordinate[0]) # * pour expand les coordonnées x et y car transform demande deux arguments
        x2, y2 = self.transform(*self.ship_coordinate[1])
        x3, y3 = self.transform(*self.ship_coordinate[2])

        self.ship.points = [x1,y1,x2,y2,x3,y3]

    def check_ship_collisions(self):
        for i in range (0, len(self.tiles_coordinates)):
            ti_x, ti_y = self.tiles_coordinates[i]
            if ti_y > self.current_y_loop + 1:
                return False
            if self.check_ship_collision_with_tile(ti_x, ti_y):
                return True
        return False

    def check_ship_collision_with_tile(self, ti_x, ti_y):
        xmin, ymin = self.get_tile_coordinates(ti_x, ti_y)
        xmax, ymax = self.get_tile_coordinates(ti_x + 1, ti_y + 1)
        for i in range (0, 3):
            px, py = self.ship_coordinate[i]

            if xmin <= px <= xmax and ymin <= py <= ymax:
                return True
        return False


    def init_tiles(self):
        with self.canvas:
            self.tile_color = Color(1,1,1)
            for i in range (0, self.NB_TILES):
                self.tiles.append(TileColor())

    def pre_fil_tiles_coordinates(self):
        for i in range (0,4):
            self.tiles_coordinates.append((0,i))
    def generate_tiles_coordinates(self):
        last_x = 0
        last_y = 0

        for i in range (len(self.tiles_coordinates)-1, -1, -1):
            if self.tiles_coordinates[i][1] < self.current_y_loop:
                del self.tiles_coordinates[i]

        if len(self.tiles_coordinates) > 0:
            last_coordinate = self.tiles_coordinates[-1]
            last_x = last_coordinate[0] 
            last_y = last_coordinate[1] + 1

        for i in range (len(self.tiles_coordinates), self.NB_TILES):
            
            r = random.randint(0,2)
            start_index = -int(self.V_NB_LINES/2)+1
            end_index = start_index + self.V_NB_LINES -2

            if last_x <= start_index:
                r = 1
            if last_x >= end_index:
                r = 2
            
            self.tiles_coordinates.append((last_x,last_y))

            if r == 1: #on va à droite
                last_x += 1
                self.tiles_coordinates.append((last_x,last_y))
                last_y += 1
                self.tiles_coordinates.append((last_x,last_y))
            elif r == 2: #on va à gauche
                last_x -= 1
                self.tiles_coordinates.append((last_x,last_y))
                last_y += 1
                self.tiles_coordinates.append((last_x,last_y))
            last_y += 1
    def init_vertical_lines(self):
        with self.canvas:
            Color(1,1,1)
            for i in range (0, self.V_NB_LINES):
                self.vertical_lines.append(Line())

    def init_horizontal_lines(self):
        with self.canvas:
            Color(1,1,1)
            for i in range (0, self.H_NB_LINES):
                self.horizontal_lines.append(Line())
    
    def get_line_x_from_index (self, index):
        central_line_x = self.perspective_point_x
        spacing = self.V_LINES_SPACING * self.width
        offset = index - 0.5
        line_x = central_line_x + offset*spacing + self.current_offset_x
        return line_x
    
    def get_line_y_from_index(self,index):
        spacing_y = self.H_LINES_SPACING * self.height
        line_y = index *spacing_y - self.current_offset_y
        return line_y
    
    def get_tile_coordinates(self, ti_x, ti_y):
        ti_y = ti_y - self.current_y_loop
        x = self.get_line_x_from_index(ti_x)
        y = self.get_line_y_from_index(ti_y)
        return x, y

    def update_tiles(self):

        for i in range (0, self.NB_TILES):
            with self.canvas:
                if random.randint(1, 5) == 1:
                    self.tile_color = Color(0.5, 0.5, 0.5)

            tile = self.tiles[i]
            tile_coordinate = self.tiles_coordinates[i]
            xmin, ymin = self.get_tile_coordinates(tile_coordinate[0], tile_coordinate[1])
            xmax, ymax = self.get_tile_coordinates(tile_coordinate[0] + 1, tile_coordinate[1] + 1)
            
            x1, y1 = self.transform(xmin, ymin)
            x2, y2 = self.transform(xmin, ymax)
            x3, y3 = self.transform(xmax, ymax)
            x4, y4 = self.transform(xmax, ymin)

            tile.points = [x1, y1, x2, y2, x3, y3, x4, y4]

    def update_vertical_lines(self):
        start_index = -int(self.V_NB_LINES/2)+1

        for i in range (start_index, start_index + self.V_NB_LINES):
                line_x = self.get_line_x_from_index(i)
                x1, y1 = self.transform(line_x, 0)
                x2, y2 = self.transform(line_x, self.height)
                self.vertical_lines[i].points = [x1,y1,x2,y2]

    def update_horizontal_lines(self):
        start_index = -int(self.V_NB_LINES/2)+1
        end_index = start_index + self.V_NB_LINES -1

        xmin = self.get_line_x_from_index(start_index)
        xmax = self.get_line_x_from_index(end_index)

        for i in range (0, self.H_NB_LINES):
                line_y = self.get_line_y_from_index(i)
                x1, y1 = self.transform(xmin, line_y)
                x2, y2 = self.transform(xmax, line_y)
                self.horizontal_lines[i].points = [x1,y1,x2,y2]

    def update(self, dt):
        time_factor = dt*60

        self.update_vertical_lines()
        self.update_horizontal_lines()
        self.update_tiles()
        self.update_ship()

        if not self.state_game_over and self.state_game_has_started:
            speed_y = self.SPEED * self.height / 100
            self.current_offset_y += speed_y * time_factor

        spacing_y = self.H_LINES_SPACING * self.height

        while self.current_offset_y >= spacing_y:
            self.current_offset_y -= self.current_offset_y
            self.current_y_loop += 1
            self.txt_score = "Score: " + str(self.current_y_loop)
            self.current_level_txt = "Niveau: " + str(self.current_level)
            self.generate_tiles_coordinates()
        
        speed_x = self.current_speed_x * self.width / 100
        self.current_offset_x += speed_x * time_factor

        if self.current_y_loop == self.next_level_tiles_goal:
            self.state_game_over = True
            self.menu_title = "L  E  V  E  L    U  P"
            self.menu_button_title = "CONTINUE"
            self.menu_widget.opacity = 1
            self.sound_music1.stop()
            self.sound_gameover_impact.play()
            self.go_next_level()

        if not self.check_ship_collisions() and not self.state_game_over and not self.isJumping:
            self.state_game_over = True
            self.end_game = True
            self.menu_title = "G  A  M  E    O  V  E  R"
            self.menu_button_title = "RESTART"
            self.menu_widget.opacity = 1
            self.sound_music1.stop()
            self.sound_gameover_impact.play()
            Clock.schedule_once(self.play_voice_game_over, 2)

    def play_voice_game_over(self, dt):
        if self.state_game_over:
            self.sound_gameover_voice.play()
    
    def on_menu_button_pressed(self):
        if self.state_game_over and self.end_game:
            self.sound_restart.play()
            self.current_level = 1
            self.NEWSPEED = self.SPEED
            self.next_level_tiles_goal = self.NB_TILES
            self.end_game = False
        else:
            self.sound_begin.play()
        self.sound_music1.play()
        self.reset_game()
        self.state_game_has_started = True
        self.menu_widget.opacity = 0


class GalaxyApp(App):
    pass


GalaxyApp().run()