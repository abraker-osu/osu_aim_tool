import numpy as np
import textwrap
import random
import json
import time
import math
import os

import pyqtgraph
from pyqtgraph.Qt import QtCore
from pyqtgraph.Qt import QtGui
from pyqtgraph.dockarea import DockArea

from osu_analysis import StdMapData
from osu_analysis import StdReplayData
from osu_analysis import StdScoreData
from osu_analysis import BeatmapIO
from osu_analysis import ReplayIO



class App(QtGui.QMainWindow):

    SAVE_FILE = lambda x: f'data/stdev_data_{int(x)}.npy'

    COL_STDEV_X = 0
    COL_STDEV_Y = 1
    COL_STDEV_T = 2
    COL_BPM     = 3
    COL_PX      = 4
    COL_ANGLE   = 5
    COL_ROT     = 6
    COL_NUM     = 7
    NUM_COLS    = 8

    from .misc._dock_patch import updateStylePatched
    from .misc.value_edit import ValueEdit
    from .misc.monitor import Monitor
    from .misc._osu_utils import OsuUtils

    # Left column
    from ._stdev_graph_bpm import StddevGraphBpm
    from ._stdev_graph_dx import StddevGraphDx
    from ._stdev_graph_angle import StddevGraphAngle
    from ._aim_graph import AimGraph
    from ._pattern_visual import PatternVisual

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        os.makedirs('data', exist_ok=True)

        self.__load_user_val()

        try: 
            self.data_file = open(App.SAVE_FILE(self.user_id), 'rb+')
            self.data = np.load(self.data_file, allow_pickle=False)
        except FileNotFoundError:
            print('Data file not found. Creating...')

            self.data = np.asarray([])
            np.save(App.SAVE_FILE(self.user_id), np.empty((0, App.NUM_COLS)), allow_pickle=False)
            
            self.data_file = open(App.SAVE_FILE(self.user_id), 'rb+')
            self.data = np.load(self.data_file, allow_pickle=False)

        self.__init_gui()
        self.__build_layout()

        if self.__load_settings():    
            try:
                self.monitor = App.Monitor(self.osu_path)
                self.monitor.create_replay_monitor('back_and_forth_monitor', self.__record_results)
            except Exception as e:
                self.status_txt.setText(str(e) + ' Is osu! path correct?')

        App.StddevGraphBpm.plot_data(self, self.data)
        App.StddevGraphDx.plot_data(self, self.data)
        #App.StddevGraphAngle.plot_data(self, self.data)

        self.show()


    def __init_gui(self):
        self.graphs = {}
        self.engaged = False

        self.main_widget = QtGui.QWidget()
        self.main_layout = QtGui.QVBoxLayout(self.main_widget)

        self.perf_chkbx = QtGui.QCheckBox('Show performance')
        self.aim_chkbx  = QtGui.QCheckBox('Show hits')
        self.ptrn_chkbx = QtGui.QCheckBox('Show pattern')

        self.edit_layout = QtGui.QHBoxLayout()
        self.bpm_edit    = App.ValueEdit(1, 1200, 'BPM')
        self.dx_edit     = App.ValueEdit(0, 512,  'Spacing')
        self.angle_edit  = App.ValueEdit(0, 360,  'Note deg')
        self.rot_edit    = App.ValueEdit(0, 360,  'Rot deg')
        self.notes_edit  = App.ValueEdit(2, 100,  '# Notes')
        self.num_edit    = App.ValueEdit(1, 1000, '# Repeats')
        self.cs_edit     = App.ValueEdit(0, 10,   'CS', is_float=True)
        self.ar_edit     = App.ValueEdit(0, 10,   'AR', is_float=True)

        self.action_btn = QtGui.QPushButton('Start')
        self.status_txt = QtGui.QLabel('Set settings and click start!')

        self.area = DockArea()
        self.aim_graph = App.AimGraph()
        self.pattern_visual = App.PatternVisual()
        

    def __build_layout(self):
        self.setWindowTitle('osu! Aim Tool Settings')
        self.area.setWindowTitle('osu! Aim Tool Performance Graphs')

        self.edit_layout.addWidget(self.bpm_edit)
        self.edit_layout.addWidget(self.dx_edit)
        self.edit_layout.addWidget(self.angle_edit)
        self.edit_layout.addWidget(self.rot_edit)
        self.edit_layout.addWidget(self.num_edit)
        self.edit_layout.addWidget(self.notes_edit)
        self.edit_layout.addWidget(self.cs_edit)
        self.edit_layout.addWidget(self.ar_edit)

        self.main_layout.addWidget(self.perf_chkbx)
        self.main_layout.addWidget(self.aim_chkbx)
        self.main_layout.addWidget(self.ptrn_chkbx)
        self.main_layout.addLayout(self.edit_layout)
        self.main_layout.addWidget(self.action_btn)
        self.main_layout.addWidget(self.status_txt)

        self.setCentralWidget(self.main_widget)

        # Left column
        App.StddevGraphBpm.__init__(self, pos='top', dock_name='Variance vs BPM')
        App.StddevGraphDx.__init__(self, pos='below', relative_to='StddevGraphBpm', dock_name='Variance vs Spacing')
        #App.StddevGraphAngle.__init__(self, pos='below', relative_to='StddevGraphDx', dock_name='Variance vs Angle')

        self.perf_chkbx.stateChanged.connect(self.__perf_chkbx_event)
        self.aim_chkbx.stateChanged.connect(self.__aim_chkbx_event)
        self.ptrn_chkbx.stateChanged.connect(self.__ptrn_chkbx_event)

        self.bpm_edit.value_changed.connect(self.__bpm_edit_event)
        self.dx_edit.value_changed.connect(self.__dx_edit)
        self.angle_edit.value_changed.connect(self.__angle_edit)
        self.rot_edit.value_changed.connect(self.__rot_edit)
        self.notes_edit.value_changed.connect(self.__notes_edit)
        self.num_edit.value_changed.connect(self.__num_edit)
        self.cs_edit.value_changed.connect(self.__cs_edit)
        self.ar_edit.value_changed.connect(self.__ar_edit)

        self.action_btn.pressed.connect(self.__action_event)

        self.area.setWindowFlags(QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowMinimizeButtonHint)
        self.perf_chkbx.setChecked(True)


    def __check_config_file(self):
        # Load osu_dir setting
        try:
            with open('config.json') as f:
                cfg = json.load(f)
        except FileNotFoundError:
            cfg = { 'osu_dir' : '' }
            with open('config.json', 'w') as f:
                json.dump(cfg, f, indent=4)


    def __load_user_val(self):
        self.__check_config_file()
        with open('config.json') as f:
            cfg = json.load(f)

        if not 'id' in cfg:
            cfg['id'] = random.randint(100, 1000000)
                    
            with open('config.json', 'w') as f:
                json.dump(cfg, f, indent=4)

        self.user_id = cfg['id']


    def __load_settings(self):
        self.__check_config_file()
        with open('config.json') as f:
            cfg = json.load(f)

        try: self.osu_path = cfg['osu_dir']
        except KeyError:
            cfg['osu_dir'] = ''
            with open('config.json', 'w') as f:
                json.dump(cfg, f, indent=4)

        if not os.path.isdir(self.osu_path):
            self.status_txt.setText('Invalid osu! path! Find config.json in app folder and edit it.\nThen restart the app.')
            return False

        # Load saved settings
        try: self.bpm_edit.set_value(cfg['bpm'])
        except KeyError: self.bpm_edit.set_value(60)

        try: self.dx_edit.set_value(cfg['dx'])
        except KeyError: self.dx_edit.set_value(100)

        try: self.angle_edit.set_value(cfg['angle'])
        except KeyError: self.angle_edit.set_value(0)

        try: self.rot_edit.set_value(cfg['rot'])
        except KeyError: self.rot_edit.set_value(0)

        try: self.num_edit.set_value(cfg['num'])
        except KeyError: self.num_edit.set_value(60)

        try: self.notes_edit.set_value(cfg['notes'])
        except KeyError: self.notes_edit.set_value(2)
        
        try: self.cs_edit.set_value(cfg['cs'])
        except KeyError: self.cs_edit.set_value(4)

        try: self.ar_edit.set_value(cfg['ar'])
        except KeyError: self.ar_edit.set_value(8)

        self.bpm   = self.bpm_edit.get_value()
        self.dx    = self.dx_edit.get_value()
        self.angle = self.angle_edit.get_value()
        self.rot   = self.rot_edit.get_value()
        self.num   = self.num_edit.get_value()
        self.notes = self.notes_edit.get_value()
        self.cs    = self.cs_edit.get_value()

        return True


    def __record_results(self, replay_path):
        time.sleep(2)

        try: self.replay = ReplayIO.open_replay(replay_path)
        except Exception as e:
            print(f'Error opening replay: {e}')
            self.monitor.pause()
            return

        self.monitor.pause()


    def __perf_chkbx_event(self, state):
        if state == QtCore.Qt.Checked:
            self.area.show()
        else:
            self.area.hide()

    
    def __aim_chkbx_event(self, state):
        if state == QtCore.Qt.Checked:
            self.aim_graph.show()
        else:
            self.aim_graph.hide()
        pass


    def __ptrn_chkbx_event(self, state):
        if state == QtCore.Qt.Checked:
            self.pattern_visual.show()
            self.pattern_visual.update(self.bpm, self.dx, self.angle, self.rot, self.num, self.notes, self.cs, self.ar)
        else:
            self.pattern_visual.hide()
        pass


    def __bpm_edit_event(self, value):
        with open('config.json') as f:
            cfg = json.load(f)
        
        cfg['bpm'] = value
        self.bpm = self.bpm_edit.get_value()
        self.pattern_visual.update(bpm=self.bpm)

        with open('config.json', 'w') as f:
            json.dump(cfg, f, indent=4)
        

    def __dx_edit(self, value):
        with open('config.json') as f:
            cfg = json.load(f)
        
        cfg['dx'] = value
        self.dx = self.dx_edit.get_value()
        self.pattern_visual.update(dx=self.dx)

        with open('config.json', 'w') as f:
            json.dump(cfg, f, indent=4)


    def __angle_edit(self, value):
        with open('config.json') as f:
            cfg = json.load(f)
        
        cfg['angle'] = value
        self.angle = self.angle_edit.get_value()
        self.pattern_visual.update(angle=self.angle)

        with open('config.json', 'w') as f:
            json.dump(cfg, f, indent=4)


    def __rot_edit(self, value):
        with open('config.json') as f:
            cfg = json.load(f)
        
        cfg['rot'] = value
        self.rot = self.rot_edit.get_value()
        self.pattern_visual.update(rot=self.rot)

        with open('config.json', 'w') as f:
            json.dump(cfg, f, indent=4)


    def __num_edit(self, value):
        with open('config.json') as f:
            cfg = json.load(f)
        
        cfg['num'] = value
        self.num = self.num_edit.get_value()
        self.pattern_visual.update(num=self.num)

        with open('config.json', 'w') as f:
            json.dump(cfg, f, indent=4)


    def __notes_edit(self, value):
        with open('config.json') as f:
            cfg = json.load(f)
        
        cfg['notes'] = value
        self.notes = self.notes_edit.get_value()
        self.pattern_visual.update(notes=self.notes)

        with open('config.json', 'w') as f:
            json.dump(cfg, f, indent=4)


    def __cs_edit(self, value):
        with open('config.json') as f:
            cfg = json.load(f)
        
        cfg['cs'] = value
        self.cs = self.cs_edit.get_value()
        self.aim_graph.set_cs(self.cs)
        self.pattern_visual.update(cs=self.cs)

        with open('config.json', 'w') as f:
            json.dump(cfg, f, indent=4)


    def __ar_edit(self, value):
        with open('config.json') as f:
            cfg = json.load(f)
        
        cfg['ar'] = value
        self.ar = self.ar_edit.get_value()
        self.pattern_visual.update(ar=self.ar)

        with open('config.json', 'w') as f:
            json.dump(cfg, f, indent=4)


    def __action_event(self):
        # If we are waiting for replay, this means we are aborting
        if self.engaged:
            self.monitor.pause()
            self.action_btn.setText('Start')
            self.status_txt.setText('Set settings and click start!')
            self.engaged = False
            return

        # Submit all unsaved settings to save and apply them
        self.bpm_edit.value_enter()
        self.dx_edit.value_enter()
        self.angle_edit.value_enter()
        self.rot_edit.value_enter()
        self.num_edit.value_enter()
        self.notes_edit.value_enter()
        self.cs_edit.value_enter()
        self.ar_edit.value_enter()

        # Check if all settings are proper
        is_error = \
            self.bpm_edit.is_error() or   \
            self.dx_edit.is_error() or    \
            self.angle_edit.is_error() or \
            self.rot_edit.is_error() or   \
            self.num_edit.is_error() or   \
            self.notes_edit.is_error() or   \
            self.cs_edit.is_error() or    \
            self.ar_edit.is_error()

        if is_error:
            return

        # Generates and saves the beatmap. Then monitor for new replay in the /data/r folder
        map_path = f'{self.osu_path}/Songs/aim_tool'

        self.status_txt.setText('Generating map...')
        self.__generate_map(map_path)
        self.__monitor_replay()

        # This needs to be after `monitor_replay`. `monitor replay` will wait until a replay is detected
        # So if we are in replay waiting state, it means the button was pressed while waiting for replay, so we abort
        if not self.engaged:
            return

        # Otherwise, replay was successfully detected and we can update the state to reflect that
        self.engaged = False

        # Data from map and replay -> score
        aim_x_offsets, aim_y_offsets, tap_offsets = self.__get_data(map_path)
        if type(aim_x_offsets) == type(None) or type(aim_y_offsets) == type(None) or type(tap_offsets) == type(None):
            self.status_txt.setText(self.status_txt.text() + '\nSet settings and click start!')
            self.action_btn.setText('Start')
            return

        # Update deviation data and plots
        self.__write_data(aim_x_offsets, aim_y_offsets, tap_offsets)
        
        App.StddevGraphBpm.plot_data(self, self.data)
        App.StddevGraphDx.plot_data(self, self.data)
        #App.StddevGraphAngle.plot_data(self, self.data)
        self.aim_graph.plot_data(aim_x_offsets, aim_y_offsets)
        
        self.status_txt.setText(self.status_txt.text() + 'Set settings and click start!')
        self.action_btn.setText('Start')


    def __generate_map(self, map_path):
        beatmap_data = textwrap.dedent(
            f"""\
            osu file format v14

            [General]
            AudioFilename: blank.mp3
            AudioLeadIn: 0
            PreviewTime: -1
            Countdown: 0
            SampleSet: Normal
            StackLeniency: 0
            Mode: 0
            LetterboxInBreaks: 1
            WidescreenStoryboard: 1

            [Editor]
            DistanceSpacing: 0.9
            BeatDivisor: 1
            GridSize: 32
            TimelineZoom: 0.2000059

            [Metadata]
            Title:unknown
            TitleUnicode:unknown
            Artist:abraker
            ArtistUnicode:abraker
            Creator:abraker
            Version:aim__bpm-{self.bpm}_dx-{self.dx}_rot-{self.rot}_deg-{self.angle}
            Source:
            Tags:
            BeatmapID:0
            BeatmapSetID:882805

            [Difficulty]
            HPDrainRate:8
            CircleSize:{self.cs}
            OverallDifficulty:10
            ApproachRate:{self.ar}
            SliderMultiplier:1.4
            SliderTickRate:1

            [Events]
            //Background and Video events
            //Break Periods
            //Storyboard Layer 0 (Background)
            //Storyboard Layer 1 (Fail)
            //Storyboard Layer 2 (Pass)
            //Storyboard Layer 3 (Foreground)
            //Storyboard Layer 4 (Overlay)
            //Storyboard Sound Samples

            [TimingPoints]
            0,1000,4,1,1,100,1,0


            [HitObjects]\
            """
        )

        # Generate notes
        pattern = App.OsuUtils.generate_pattern2(self.rot*math.pi/180, self.dx, 60/self.bpm, self.angle*math.pi/180, self.notes, self.num)

        for note in pattern:
            beatmap_data += textwrap.dedent(
                f"""
                {int(note[0])},{int(note[1])},{int(note[2]*1000)},1,0,0:0:0:0:\
                """
            )

        # Remove leading whitespace
        beatmap_data = beatmap_data.split('\n')
        for i in range(len(beatmap_data)):
            beatmap_data[i] = beatmap_data[i].strip()
        self.beatmap_data = '\n'.join(beatmap_data)

        # Write to beatmap file
        os.makedirs(map_path, exist_ok=True)
        BeatmapIO.save_beatmap(self.beatmap_data, f'{map_path}/map.osu')


    def __monitor_replay(self):
        self.status_txt.setText('Open osu! and play the map! Waiting for play...')
        self.action_btn.setText('ABORT')

        # Resumes *.osr file monitoring and updates state
        self.monitor.resume()
        self.engaged = True

        # Wait until a replay is detected or user presses the ABORT button
        while not self.monitor.paused:
            QtGui.QApplication.instance().processEvents()
            time.sleep(0.1)


    def __get_data(self, map_path):
        beatmap = BeatmapIO.open_beatmap(f'{map_path}/map.osu')

        # Read beatmap
        try: map_data = StdMapData.get_map_data(beatmap)
        except TypeError as e:
            self.status_txt.setText('Error reading beatmap!')
            print(e)
            return None, None

        # Read replay
        try: replay_data = StdReplayData.get_replay_data(self.replay)
        except Exception as e:
            self.status_txt.setText('Error reading replay!')
            print(e)
            return None, None, None

        # Process score data
        settings = StdScoreData.Settings()
        settings.ar_ms = App.OsuUtils.ar_to_ms(self.ar)
        settings.hitobject_radius = App.OsuUtils.cs_to_px(self.cs)
        settings.pos_hit_range = 100        # ms point of late hit window
        settings.neg_hit_range = 100        # ms point of early hit window
        settings.pos_hit_miss_range = 100   # ms point of late miss window
        settings.neg_hit_miss_range = 100   # ms point of early miss window

        score_data = StdScoreData.get_score_data(replay_data, map_data, settings)

        hit_types_miss = score_data['type'] == StdScoreData.TYPE_MISS
        num_total = score_data['type'].values.shape[0]
        num_misses = score_data['type'].values[hit_types_miss].shape[0]

        # Too many misses tends to falsely lower the deviation. Disallow plays with >10% misses
        print(f'num total hits: {num_total}   num: misses {num_misses} ({100 * num_misses/num_total:.2f}%)')
        if num_misses/num_total > 0.1:
            self.status_txt.setText('Invalid play. Too many misses.')
            return None, None, None

        aim_x_offsets = score_data['replay_x'] - score_data['map_x']
        aim_y_offsets = score_data['replay_y'] - score_data['map_y']
        tap_offsets   = score_data['replay_t'] - score_data['map_t']

        # Correct for incoming direction
        x_map_vecs = score_data['map_x'].values[1:] - score_data['map_x'].values[:-1]
        y_map_vecs = score_data['map_y'].values[1:] - score_data['map_y'].values[:-1]

        map_thetas = np.arctan2(y_map_vecs, x_map_vecs)
        hit_thetas = np.arctan2(aim_y_offsets, aim_x_offsets)
        mags = (aim_x_offsets**2 + aim_y_offsets**2)**0.5

        aim_x_offsets = mags*np.cos(map_thetas - hit_thetas[1:])
        aim_y_offsets = mags*np.sin(map_thetas - hit_thetas[1:])

        return aim_x_offsets, aim_y_offsets, tap_offsets


    def __write_data(self, aim_offsets_x, aim_offsets_y, tap_offsets):
        stddev_x = np.std(aim_offsets_x)
        stddev_y = np.std(aim_offsets_y)
        stddev_t = np.std(tap_offsets)

        # Close data file for writing
        self.data_file.close()

        # Find record based on bpm and spacing
        data_select = \
            (self.data[:, App.COL_BPM] == self.bpm) & \
            (self.data[:, App.COL_PX] == self.dx) & \
            (self.data[:, App.COL_ROT] == self.rot) & \
            (self.data[:, App.COL_ANGLE] == self.angle)

        if np.any(data_select):
            # A record exists, see if it needs to be updated
            stddev_x_curr = self.data[data_select, App.COL_STDEV_X][0]
            stddev_y_curr = self.data[data_select, App.COL_STDEV_Y][0]
            stddev_t_curr = self.data[data_select, App.COL_STDEV_T][0]

            text = \
                f'ar: {self.ar}   bpm: {self.bpm}   dx: {self.dx}   angle: {self.angle}   rot: {self.rot}\n' \
                f'aim stddev^2: {stddev_x*stddev_y:.2f} (best: {stddev_x_curr*stddev_y_curr:.2f})   aim stddev (x, y, t): ({stddev_x:.2f}, {stddev_y:.2f}, {stddev_t:.2f})  best: ({stddev_x_curr:.2f}, {stddev_x_curr:.2f}, {stddev_t_curr:.2f})\n'
            
            self.status_txt.setText(text)
            print(text)

            # Record new best only if stdev^2 is better
            if stddev_x*stddev_y < stddev_x_curr*stddev_y_curr:
                self.data[data_select, App.COL_STDEV_X] = stddev_x
                self.data[data_select, App.COL_STDEV_Y] = stddev_y
                self.data[data_select, App.COL_STDEV_T] = stddev_t
        else:
            # Create a new record
            text = \
                f'ar: {self.ar}   bpm: {self.bpm}   dx: {self.dx}   angle: {self.angle}   rot: {self.rot}\n' \
                f'aim stddev^2: {stddev_x*stddev_y:.2f}   aim stddev (x, y, t): ({stddev_x:.2f}, {stddev_y:.2f}, {stddev_t:.2f}))\n'

            self.status_txt.setText(text)
            print(text)

            self.data = np.insert(self.data, 0, np.asarray([ stddev_x, stddev_y, stddev_t, self.bpm , self.dx, self.angle, self.rot, self.num ]), axis=0)
        
        # Save data to file
        np.save(App.SAVE_FILE(self.user_id), self.data, allow_pickle=False)

        # Now reopen it so it can be used
        self.data_file = open(App.SAVE_FILE(self.user_id), 'rb+')
        self.data = np.load(self.data_file, allow_pickle=False)


    def closeEvent(self, event):
        # Gracefully stop monitoring
        if self.engaged:
            self.monitor.pause()

        # Hide any widgets to allow the app to close
        self.area.hide()
        self.aim_graph.hide()
        self.pattern_visual.hide()

        # Proceed
        event.accept()


    def _create_graph(self, graph_id=None, dock_name=' ', pos='bottom', relative_to=None, widget=None, plot=None):
        if type(widget) == type(None):
            widget = pyqtgraph.PlotWidget()
        
        try: widget.getViewBox().enableAutoRange()
        except AttributeError: pass
        
        dock = pyqtgraph.dockarea.Dock(dock_name, size=(500,400))
        dock.addWidget(widget)
        
        try: relative_dock = self.graphs[relative_to]['dock']
        except KeyError:
            relative_dock = None

        self.area.addDock(dock, pos, relativeTo=relative_dock)

        self.graphs[graph_id] = {
            'widget' : widget,
            'dock'   : dock
        }

        if plot != None:
            widget.addItem(plot)