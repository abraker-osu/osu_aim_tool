import numpy as np
import textwrap
import random
import json
import time
import math
import shutil
import os
import re

import pyqtgraph
from pyqtgraph.Qt import QtCore
from pyqtgraph.Qt import QtGui
from pyqtgraph.dockarea import DockArea

from osu_analysis import StdMapData
from osu_analysis import StdReplayData
from osu_analysis import StdScoreData
from osu_analysis import BeatmapIO
from osu_analysis import ReplayIO
from osu_analysis import ReplayIO
from osu_analysis import Mod

from app.config import AppConfig



class App(QtGui.QMainWindow):

    SAVE_FILE = lambda x: f'data/stdev_data_{int(x)}.npy'

    MAX_NUM_DATA_POINTS = 5  # Maximum number of data point records to average

    COL_STDEV_X = 0  # Deviation along x-axis
    COL_STDEV_Y = 1  # Deviation along y-axis
    COL_STDEV_T = 2  # Deviation along hit time
    COL_BPM     = 3  # BPM of the pattern (60/s)
    COL_PX      = 4  # Distance between notes in the pattern (osu!px)
    COL_ANGLE   = 5  # Angle between notes in the pattern (deg)
    COL_ROT     = 6  # Rotation of pattern (deg)
    COL_NUM     = 7  # Number of notes in the pattern before pattern reverses
    NUM_COLS    = 8

    DEV_X  = 0
    DEV_Y  = 1
    DEV_XY = 2
    DEV_T  = 3

    from .misc._dock_patch import updateStylePatched
    from .misc.value_edit import ValueEdit
    from .misc.monitor import Monitor
    from .misc._osu_utils import OsuUtils

    # Left column
    from .graphs._stdev_graph_bpm import StddevGraphBpm
    from .graphs._stdev_graph_dx import StddevGraphDx
    from .graphs._stdev_graph_num_notes import StddevGraphNumNotes
    from .graphs._stdev_graph_angle import StddevGraphAngle
    from .graphs._stdev_graph_vel import StddevGraphVel
    from .graphs._stdev_graph_skill import StddevGraphSkill
    from .views._aim_graph import AimGraph
    from .views._pattern_visual import PatternVisual
    from .views._data_list import DataList

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        os.makedirs('data', exist_ok=True)

        self.user_id = AppConfig.cfg['id']

        self.__init_gui()
        self.__build_layout()

        self.load_data_file(self.user_id)
        self.data_list.load_data_list()
        self.data_list.select_data_id(self.user_id)

        if os.path.isdir(AppConfig.cfg['osu_dir']):
            default_cfg = {
                'bpm'     : 60,
                'dx'      : 100,
                'angle'   : 0,
                'rot'     : 0,
                'notes'   : 0,
                'repeats' : 60,
                'cs'      : 4,
                'ar'      : 8,
            }

            for key in self.cfg_widgets:
                try: self.cfg_widgets[key].set_value(AppConfig.cfg[key])
                except KeyError:
                    self.cfg_widgets[key].set_value(default_cfg[key])

            try:
                self.monitor = App.Monitor(AppConfig.cfg['osu_dir'])
                self.monitor.create_replay_monitor('back_and_forth_monitor', self.__record_results)
            except Exception as e:
                self.status_txt.setText(str(e) + ' Is osu! path correct?')
        else:
            self.info_text = \
                'Invalid osu! path! Find config.json in app folder and edit it.\n' + \
                'Then restart the app.\n' + \
                'Make sure to use double backslashes for osu! path\n'
            self.stats_text = ''
            self.status_txt.setText(self.info_text + self.stats_text)

            self.action_btn.setEnabled(False)
            self.view_hits_action.setEnabled(False)
            self.view_map_action.setEnabled(False)

        self.replot_graphs()
        self.show()


    def __init_gui(self):
        self.graphs = {}
        self.engaged = False
        self.dev_select = App.DEV_X

        self.model_compensation = False
        self.avg_data_points    = True
        self.auto_increase      = False

        self.selected_data_id = None
        self.data_list_ids = []

        self.info_text = ''
        self.stats_text = ''

        self.menu_bar  = QtGui.QMenuBar()
        self.view_menu = QtGui.QMenu("&View", self)

        self.view_perf_action = QtGui.QAction("&Show performance", self.view_menu, triggered=lambda: self.area.show())
        self.view_hits_action = QtGui.QAction("&Show hits",        self.view_menu, triggered=lambda: self.aim_graph.show())
        self.view_map_action  = QtGui.QAction("&Show map",         self.view_menu, triggered=lambda: (
                self.pattern_visual.show(), 
                self.__update_generated_map()
            )
        )
        self.view_data_sel_action = QtGui.QAction("&Show data select", self.view_menu, triggered=lambda: self.data_list.show())

        self.main_widget = QtGui.QWidget()
        self.main_layout = QtGui.QVBoxLayout(self.main_widget)
        
        self.selct_layout = QtGui.QHBoxLayout()

        self.win_selct_layout = QtGui.QVBoxLayout()
        self.auto_chkbx = QtGui.QCheckBox('Auto increment settings')
        self.avg_chkbx = QtGui.QCheckBox('Average data points')
        self.model_chkbx = QtGui.QCheckBox('Model compensation')

        self.dev_selct_layout = QtGui.QVBoxLayout()
        self.xdev_radio_btn = QtGui.QRadioButton('x-dev')
        self.ydev_radio_btn = QtGui.QRadioButton('y-dev')
        self.xydev_radio_btn = QtGui.QRadioButton('xy-dev')
        self.tdev_radio_btn = QtGui.QRadioButton('t-dev')

        self.edit_layout  = QtGui.QHBoxLayout()
        self.cfg_widgets = {
            'bpm'     : App.ValueEdit(1, 1200, 'bpm',     'BPM'),
            'dx'      : App.ValueEdit(0, 512,  'dx',      'Spacing'),
            'angle'   : App.ValueEdit(0, 180,  'angle',   'Note deg'),
            'rot'     : App.ValueEdit(0, 360,  'rot',     'Rot deg'),
            'notes'   : App.ValueEdit(3, 2000, 'notes',   '# Notes'),
            'repeats' : App.ValueEdit(1, 1000, 'repeats', '# Repeats'),
            'cs'      : App.ValueEdit(0, 10,   'cs',      'CS', is_float=True),
            'ar'      : App.ValueEdit(0, 11,   'ar',      'AR', is_float=True),
        }

        self.action_btn = QtGui.QPushButton('Start')
        self.status_txt = QtGui.QLabel('Set settings and click start!')

        self.area = DockArea()
        self.aim_graph = App.AimGraph()
        self.pattern_visual = App.PatternVisual()
        self.data_list = App.DataList(self)
        

    def __build_layout(self):
        self.setWindowTitle('osu! Aim Tool Settings')
        self.area.setWindowTitle('osu! Aim Tool Performance Graphs')

        # Set up menu bar
        self.setMenuBar(self.menu_bar)
        self.menu_bar.addMenu(self.view_menu)
        self.view_menu.addAction(self.view_perf_action)
        self.view_menu.addAction(self.view_hits_action)
        self.view_menu.addAction(self.view_map_action)
        self.view_menu.addAction(self.view_data_sel_action)

        # Connect deviation select radio buttons events
        self.xdev_radio_btn.setChecked(True)
        self.xdev_radio_btn.toggled.connect(self.__dev_select_event)
        self.ydev_radio_btn.toggled.connect(self.__dev_select_event)
        self.xydev_radio_btn.toggled.connect(self.__dev_select_event)
        self.tdev_radio_btn.toggled.connect(self.__dev_select_event)

        # Add setting text edit fields
        self.edit_layout.addWidget(self.cfg_widgets['bpm'])
        self.edit_layout.addWidget(self.cfg_widgets['dx'])
        self.edit_layout.addWidget(self.cfg_widgets['angle'])
        self.edit_layout.addWidget(self.cfg_widgets['rot'])
        self.edit_layout.addWidget(self.cfg_widgets['repeats'])
        self.edit_layout.addWidget(self.cfg_widgets['notes'])
        self.edit_layout.addWidget(self.cfg_widgets['cs'])
        self.edit_layout.addWidget(self.cfg_widgets['ar'])

        # Add settings checkboxes
        self.avg_chkbx.setChecked(True)
        self.win_selct_layout.addWidget(self.avg_chkbx)
        self.win_selct_layout.addWidget(self.model_chkbx)
        self.win_selct_layout.addWidget(self.auto_chkbx)

        # Add deviation select radio buttons
        self.dev_selct_layout.addWidget(self.xdev_radio_btn)
        self.dev_selct_layout.addWidget(self.ydev_radio_btn)
        self.dev_selct_layout.addWidget(self.xydev_radio_btn)
        self.dev_selct_layout.addWidget(self.tdev_radio_btn)

        # Build layout
        self.selct_layout.addLayout(self.win_selct_layout)
        self.selct_layout.addLayout(self.dev_selct_layout)

        self.main_layout.addLayout(self.selct_layout)
        self.main_layout.addLayout(self.edit_layout)
        self.main_layout.addWidget(self.action_btn)
        self.main_layout.addWidget(self.status_txt)

        self.setCentralWidget(self.main_widget)

        # Create graphs
        App.StddevGraphBpm.__init__(self, pos='top', dock_name='Deviation vs BPM')
        App.StddevGraphDx.__init__(self, pos='below', relative_to='StddevGraphBpm', dock_name='Deviation vs Spacing')
        App.StddevGraphNumNotes.__init__(self, pos='below', relative_to='StddevGraphDx', dock_name='Deviation vs # Notes')
        App.StddevGraphAngle.__init__(self, pos='below', relative_to='StddevGraphNumNotes', dock_name='Deviation vs Angle')
        App.StddevGraphVel.__init__(self, pos='below', relative_to='StddevGraphAngle', dock_name='Deviation vs Velocity')
        App.StddevGraphSkill.__init__(self, pos='below', relative_to='StddevGraphVel', dock_name='Skill vs Angle')

        # Connect checkbox events
        self.avg_chkbx.stateChanged.connect(self.__avg_chkbx_event)
        self.model_chkbx.stateChanged.connect(self.__model_chkbx_event)
        self.auto_chkbx.stateChanged.connect(self.__auto_chkbx_event)

        # Connect settings edit events
        for widget in self.cfg_widgets.values():
            widget.value_changed.connect(lambda data: self.__setting_value_changed_event(*data))

        self.action_btn.pressed.connect(self.__action_event)

        self.area.setWindowFlags(QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowMinimizeButtonHint)
        self.area.show()

        # Switch to the dev vs vel tab
        self.graphs['StddevGraphVel']['dock'].raiseDock()


    def __record_results(self, replay_path):
        time.sleep(2)

        try: self.replay = ReplayIO.open_replay(replay_path)
        except Exception as e:
            print(f'Error opening replay: {e}')
            self.monitor.pause()
            return

        self.monitor.pause()


    def __avg_chkbx_event(self, state):
        self.avg_data_points = (state == QtCore.Qt.Checked)
        self.replot_graphs()


    def __model_chkbx_event(self, state):
        self.model_compensation = (state == QtCore.Qt.Checked)
        self.replot_graphs()


    def __auto_chkbx_event(self, state):
        self.auto_increase = (state == QtCore.Qt.Checked)


    def __setting_value_changed_event(self, key, value):
        AppConfig.update_value(key, value)

        if key in [ 'bpm', 'dx', 'angle', 'repeats', 'rot', 'notes', 'cs', 'ar' ]:
            is_clipped = self.__update_generated_map()
            
            # Check if pattern is clipped and show warning if so
            if key in [ 'dx', 'angle', 'rot', 'repeats', 'notes' ]:
                if is_clipped:
                    self.info_text = \
                        'Set settings and click start!\n' + \
                        'Warning: Pattern is being clipped to playfield border!\n'
                else:
                    self.info_text = 'Set settings and click start!\n'
    
                self.status_txt.setText(self.info_text + self.stats_text)

        if key in [ 'bpm', 'dx' ]:
            App.StddevGraphVel.update_vel(self, **{ key : value })

        if key == 'cs':
            self.aim_graph.set_cs(value)
            dev = App.OsuUtils.cs_to_px(value)

            App.StddevGraphBpm.set_dev(self, dev)
            App.StddevGraphDx.set_dev(self, dev)
            App.StddevGraphNumNotes.set_dev(self, dev)
            App.StddevGraphAngle.set_dev(self, dev)
            App.StddevGraphVel.set_dev(self, dev)


    def __dev_select_event(self):
        if self.sender() == self.xdev_radio_btn:
            self.dev_select = App.DEV_X
        elif self.sender() == self.ydev_radio_btn:
            self.dev_select = App.DEV_Y
        elif self.sender() == self.xydev_radio_btn:
            self.dev_select = App.DEV_XY
        elif self.sender() == self.tdev_radio_btn:
            self.dev_select = App.DEV_T

        self.replot_graphs()


    def __action_event(self):
        while True:
            # If we are waiting for replay, this means we are aborting
            if self.engaged:
                # We are manually aborting, so disable automation
                self.auto_chkbx.setChecked(False)

                # Stop monitoring
                self.monitor.pause()

                # Restore GUI state to non-engaged state
                self.action_btn.setText('Start')
                self.data_list.setEnabled(True)
                self.__set_settings_edit_enabled(True)

                self.engaged = False
                return

            # Submit all unsaved settings to save and apply them
            is_error = False

            for widget in self.cfg_widgets.values():
                # Apply all settings
                widget.value_enter()

                # Check if all settings are proper
                is_error = is_error or widget.is_error()

            if is_error:
                return

            # Check if we have user's data opened. Switch to it if we do not
            if self.selected_data_id != self.user_id:
                self.data_list.select_data_id(self.user_id)
                self.replot_graphs()

            # Generates and saves the beatmap. Then monitor for new replay in the /data/r folder
            map_path = f'{AppConfig.cfg["osu_dir"]}/Songs/aim_tool'

            self.__generate_map(map_path)
            self.__monitor_replay()

            # This needs to be after `monitor_replay`. `monitor replay` will wait until a replay is detected
            # So if we are in replay waiting state, it means the button was pressed while waiting for replay, so we abort
            if not self.engaged:
                self.info_text = 'Set settings and click start!\n'
                self.status_txt.setText(self.info_text + self.stats_text)
                return

            self.info_text = ''
            self.stats_text = ''
            self.status_txt.setText(self.info_text + self.stats_text)

            # Otherwise, replay was successfully detected and we can update the state to reflect that
            self.engaged = False
            self.data_list.setEnabled(True)
            self.__set_settings_edit_enabled(True)

            # Data from map and replay -> score
            replay_data, aim_x_offsets, aim_y_offsets, tap_offsets = self.__get_data(map_path)
            if type(aim_x_offsets) == type(None) or type(aim_y_offsets) == type(None) or type(tap_offsets) == type(None):
                if not self.auto_increase:
                    self.info_text += 'Set settings and click start!\n'
                    self.stats_text = ''
                    self.status_txt.setText(self.info_text + self.stats_text)

                    self.action_btn.setText('Start')
                    return
                else:
                    continue

            # Update deviation data and plots
            self.__write_data(aim_x_offsets, aim_y_offsets, tap_offsets)

            self.replot_graphs()
            self.aim_graph.plot_data(aim_x_offsets, aim_y_offsets)
            self.pattern_visual.set_replay(replay_data)
            
            # If we are in not auto mode, we are done
            if not self.auto_increase:
                self.info_text += 'Set settings and click start!\n'
                self.status_txt.setText(self.info_text + self.stats_text)

                self.action_btn.setText('Start')
                return

            # Otherwise, we are in auto mode, so we need to increase the respective settings
            for widget in self.cfg_widgets.values():
                widget.value_increase()


    def __generate_map(self, map_path):
        # Handle DT/NC vs nomod setting
        rate_multiplier = 1.0 if (AppConfig.cfg["ar"] <= 10) else 1.5
        
        ar = min(AppConfig.cfg["ar"], 10)
        ar = ar if (AppConfig.cfg["ar"] <= 10) else App.OsuUtils.ms_to_ar(App.OsuUtils.ar_to_ms(AppConfig.cfg["ar"])*rate_multiplier)

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
            Version:aim__bpm-{AppConfig.cfg["bpm"]}_dx-{AppConfig.cfg["dx"]}_rot-{AppConfig.cfg["rot"]}_deg-{AppConfig.cfg["angle"]}
            Source:
            Tags:
            BeatmapID:0
            BeatmapSetID:882805

            [Difficulty]
            HPDrainRate:8
            CircleSize:{AppConfig.cfg["cs"]}
            OverallDifficulty:10
            ApproachRate:{AppConfig.cfg["ar"]}
            SliderMultiplier:1.4
            SliderTickRate:1

            [Events]\
            """
        )

        # Generate notes
        pattern, _ = App.OsuUtils.generate_pattern2(AppConfig.cfg["rot"]*math.pi/180, AppConfig.cfg["dx"], 60/AppConfig.cfg["bpm"]*rate_multiplier, AppConfig.cfg["angle"]*math.pi/180, AppConfig.cfg["notes"], AppConfig.cfg["repeats"])
        audio_offset = -48  # ms

        for note in pattern:
            beatmap_data += textwrap.dedent(
                f"""
                Sample,{int(note[2]*1000 + audio_offset*rate_multiplier)},3,"pluck.wav",100\
                """
            )

        beatmap_data += textwrap.dedent(
            f"""

            [TimingPoints]
            0,1000,4,1,1,100,1,0

            [HitObjects]\
            """
        )

        for note in pattern:
            beatmap_data += textwrap.dedent(
                f"""
                {int(note[0])},{int(note[1])},{int(note[2]*1000 + audio_offset*rate_multiplier)},1,0,0:0:0:0:\
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

        if not os.path.isfile(f'{map_path}/pluck.wav'):
            shutil.copy2('pluck.wav', f'{map_path}/pluck.wav')

        if not os.path.isfile(f'{map_path}/normal-hitnormal.wav'):
            shutil.copy2('blank.wav', f'{map_path}/normal-hitnormal.wav')


    def __monitor_replay(self):
        self.info_text = 'Open osu! and play the map! Waiting for play...\n'
        self.status_txt.setText(self.info_text + self.stats_text)

        self.action_btn.setText('ABORT')

        # Resumes *.osr file monitoring and updates state
        self.monitor.resume()
        self.engaged = True
        self.data_list.setEnabled(False)
        self.__set_settings_edit_enabled(False)

        # Wait until a replay is detected or user presses the ABORT button
        while not self.monitor.paused:
            QtGui.QApplication.instance().processEvents()
            time.sleep(0.05)


    def __get_data(self, map_path):
        beatmap = BeatmapIO.open_beatmap(f'{map_path}/map.osu')

        print('replay mods:', self.replay.mods.value)

        # Check if mods are valid
        if AppConfig.cfg["ar"] > 10:
            has_dt = (self.replay.mods.value & Mod.DoubleTime) > 0
            has_nc = (self.replay.mods.value & Mod.Nightcore) > 0

            if not (has_dt or has_nc):
                self.info_text = 'AR >10 requires DT or NC mod enabled!\n'
                self.status_txt.setText(self.info_text + self.stats_text)
                return None, None, None, None

            has_other_mods = (self.replay.mods.value & ~(Mod.DoubleTime | Mod.Nightcore)) > 0
            if has_other_mods:
                self.info_text = 'AR >10 requires ONLY DT or NC mod enabled!\n'
                self.status_txt.setText(self.info_text + self.stats_text)
                
                return None, None, None, None
        else:
            if self.replay.mods.value != 0:
                self.info_text = 'AR <10 requires nomod!\n'
                self.status_txt.setText(self.info_text + self.stats_text)
                return None, None, None, None

        # Read beatmap
        try: map_data = StdMapData.get_map_data(beatmap)
        except TypeError as e:
            self.info_text = 'Error reading beatmap!\n'
            self.status_txt.setText(self.info_text + self.stats_text)
            print(e)
            return None, None, None, None

        # Read replay
        try: replay_data = StdReplayData.get_replay_data(self.replay)
        except Exception as e:
            self.info_text = 'Error reading replay!\n'
            self.status_txt.setText(self.info_text + self.stats_text)
            print(e)
            return None, None, None, None

        # Process score data
        settings = StdScoreData.Settings()
        settings.ar_ms = App.OsuUtils.ar_to_ms(AppConfig.cfg["ar"])
        settings.hitobject_radius = App.OsuUtils.cs_to_px(AppConfig.cfg["cs"])
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
            self.info_text = ''
            self.stats_text = '\nInvalid play. Too many misses.'
            self.status_txt.setText(self.info_text + self.stats_text)
            return None, None, None, None

        aim_x_offsets = score_data['replay_x'].values - score_data['map_x'].values
        aim_y_offsets = score_data['replay_y'].values - score_data['map_y'].values
        tap_offsets   = score_data['replay_t'].values - score_data['map_t'].values

        # Correct for incoming direction
        x_map_vecs = score_data['map_x'].values[1:] - score_data['map_x'].values[:-1]
        y_map_vecs = score_data['map_y'].values[1:] - score_data['map_y'].values[:-1]

        map_thetas = np.arctan2(y_map_vecs, x_map_vecs)
        hit_thetas = np.arctan2(aim_y_offsets, aim_x_offsets)
        mags = (aim_x_offsets**2 + aim_y_offsets**2)**0.5

        aim_x_offsets = mags[1:]*np.cos(map_thetas - hit_thetas[1:])
        aim_y_offsets = mags[1:]*np.sin(map_thetas - hit_thetas[1:])

        spacings = (x_map_vecs**2 + y_map_vecs**2)**0.5

        # angle = [ x0, x1, x2 ]
        dx0 = score_data['map_x'].values[1:-1] - score_data['map_x'].values[:-2]   # x1 - x0
        dx1 = score_data['map_x'].values[2:] - score_data['map_x'].values[1:-1]    # x2 - x1

        dy0 = score_data['map_y'].values[1:-1] - score_data['map_y'].values[:-2]   # y1 - y0
        dy1 = score_data['map_y'].values[2:] - score_data['map_y'].values[1:-1]    # y2 - y1
        
        theta_d0 = np.arctan2(dy0, dx0)*(180/math.pi)
        theta_d1 = np.arctan2(dy1, dx1)*(180/math.pi)

        angles = np.abs(theta_d1 - theta_d0)
        angles[angles > 180] = 360 - angles[angles > 180]
        angles = np.round(angles)

        # First and last notes do not partain to any angle
        # and select by angle (because there are unwanted angles where pattern reverses)
        # Angles are selected with a bit of error margin since lower spacing introduces pixel-angle uncertainty
        # Allow `dx = 0` through because all angles would be 0
        # Allow `notes = 2` through because all angles would be 180
        angle_select = (np.abs(angles - AppConfig.cfg["angle"]) < 3) | (AppConfig.cfg["dx"] == 0) | (AppConfig.cfg["notes"] == 2)

        # Make sure only points that are within the set spacing are recorded
        spacing_select = (np.abs(spacings[1:] - AppConfig.cfg["dx"]) < 3)

        aim_x_offsets = aim_x_offsets[:-1][angle_select & spacing_select]
        aim_y_offsets = aim_y_offsets[:-1][angle_select & spacing_select]
        tap_offsets   = tap_offsets[1:-1][angle_select & spacing_select]

        # Prevent recording if there is blank data
        if 0 in [ aim_x_offsets.shape[0], aim_y_offsets.shape[0], tap_offsets.shape[0] ]:            
            aim_x_offsets = score_data["replay_y"].values - score_data["map_y"].values
            aim_y_offsets = score_data["replay_x"].values - score_data["map_x"].values

            self.stats_text = '\nData calculation error!'
            self.status_txt.setText(self.info_text + self.stats_text)
            
            print('Non of the angles match')
            print('Debug info:')
            print()
            print(f'    aim_x_offsets = {aim_x_offsets}')
            print()
            print(f'    aim_y_offsets = {aim_y_offsets}')
            print()
            print(f'    x_map_vecs = {x_map_vecs}')
            print()
            print(f'    y_map_vecs = {y_map_vecs}')
            print()
            print(f'    angles = {angles}')
            print()
            print(f'    set dx = {self.dx}')
            print(f'    set notes = {self.notes}')
            print(f'    set ang = {self.angle}')
            return None, None, None, None

        # Filter out nans that happen due to misc reasons (usually due to empty slices or div by zero)
        nan_filter = ~np.isnan(aim_x_offsets) & ~np.isnan(aim_y_offsets)

        aim_x_offsets = aim_x_offsets[nan_filter]
        aim_y_offsets = aim_y_offsets[nan_filter]
        tap_offsets   = tap_offsets[nan_filter]

        # Prevent recording if there is blank data
        if 0 in [ aim_x_offsets.shape[0], aim_y_offsets.shape[0], tap_offsets.shape[0] ]:
            hit_theta_x = score_data["replay_y"].values - score_data["map_y"].values
            hit_theta_y = score_data["replay_x"].values - score_data["map_x"].values

            self.stats_text = '\nData calculation error!'
            self.status_txt.setText(self.info_text + self.stats_text)

            print('Data calculation error!')
            print('Debug info:')
            print()
            print(f'    tap_offsets = {tap_offsets}')
            print()
            print(f'    aim_y_offsets = {hit_theta_y}')
            print()
            print(f'    aim_x_offsets = {hit_theta_x}')
            print()
            print(f'    hit_thetas = {np.arctan2(hit_theta_x, hit_theta_y)}')
            print()
            print(f'    map_thetas = {np.arctan2(y_map_vecs, x_map_vecs)}')
            return None, None, None, None

        return replay_data, aim_x_offsets, aim_y_offsets, tap_offsets


    def __write_data(self, aim_offsets_x, aim_offsets_y, tap_offsets):
        stddev_x = np.std(aim_offsets_x)
        stddev_y = np.std(aim_offsets_y)
        stddev_t = np.std(tap_offsets)

        stddev_xy = (stddev_x**2 + stddev_y**2)**0.5

        # Close data file for writing
        self.data_file.close()

        # Find record based on bpm and spacing
        data_select = \
            (self.data[:, App.COL_BPM] == AppConfig.cfg["bpm"]) & \
            (self.data[:, App.COL_PX] == AppConfig.cfg["dx"]) & \
            (self.data[:, App.COL_ROT] == AppConfig.cfg["rot"]) & \
            (self.data[:, App.COL_ANGLE] == AppConfig.cfg["angle"]) & \
            (self.data[:, App.COL_NUM] == AppConfig.cfg["notes"])

        num_records = data_select.sum()

        # Print play/record info
        if num_records != 0:
            # Get current records
            stddev_x_curr = self.data[data_select, App.COL_STDEV_X]
            stddev_y_curr = self.data[data_select, App.COL_STDEV_Y]
            stddev_t_curr = self.data[data_select, App.COL_STDEV_T]

            # Calculate stdev-xy for each data point and figure out which one is largest
            stddev_xy_curr = (stddev_x_curr**2 + stddev_y_curr**2)**0.5
            min_stddev_xy_curr_idx = np.argmax(stddev_xy_curr)

            # Print current record along with worst one
            self.stats_text = \
                f'\nTotal number of records: {num_records + 1}\n' \
                f'ar: {AppConfig.cfg["ar"]}   bpm: {AppConfig.cfg["bpm"]}   dx: {AppConfig.cfg["dx"]}   angle: {AppConfig.cfg["angle"]}   rot: {AppConfig.cfg["rot"]}   notes: {AppConfig.cfg["notes"]}\n' \
                f'aim stddev-xy: {stddev_xy:.2f} (worst: {stddev_xy_curr[min_stddev_xy_curr_idx]:.2f})   aim stddev (x, y, t): ({stddev_x:.2f}, {stddev_y:.2f}, {stddev_t:.2f})  worst: ({stddev_x_curr[min_stddev_xy_curr_idx]:.2f}, {stddev_y_curr[min_stddev_xy_curr_idx]:.2f}, {stddev_t_curr[min_stddev_xy_curr_idx]:.2f})\n'
        else:
            # Nothing recorded yet, print just current record
            self.stats_text = \
                f'\nTotal number of records: {num_records + 1}\n' \
                f'ar: {AppConfig.cfg["ar"]}   bpm: {AppConfig.cfg["bpm"]}   dx: {AppConfig.cfg["dx"]}   angle: {AppConfig.cfg["angle"]}   rot: {AppConfig.cfg["rot"]}   notes: {AppConfig.cfg["notes"]}\n' \
                f'aim stddev-xy: {stddev_xy:.2f}  aim stddev (x, y, t): ({stddev_x:.2f}, {stddev_y:.2f}, {stddev_t:.2f})\n'

        self.status_txt.setText(self.info_text + self.stats_text)
        print(self.stats_text)
    
        # Update data and save to file
        self.data = np.insert(self.data, 0, np.asarray([ stddev_x, stddev_y, stddev_t, AppConfig.cfg['bpm'], AppConfig.cfg['dx'], AppConfig.cfg['angle'], AppConfig.cfg['rot'], AppConfig.cfg['notes'] ]), axis=0)
        np.save(App.SAVE_FILE(self.user_id), self.data, allow_pickle=False)

        # Now reopen it so it can be used
        self.data_file = open(App.SAVE_FILE(self.user_id), 'rb+')
        self.data = np.load(self.data_file, allow_pickle=False)


    def load_data_file(self, user_id):
        try: 
            self.data_file = open(App.SAVE_FILE(user_id), 'rb+')
            self.data = np.load(self.data_file, allow_pickle=False)
        except FileNotFoundError:
            print('Data file not found. Creating...')

            self.data = np.asarray([])
            np.save(App.SAVE_FILE(user_id), np.empty((0, App.NUM_COLS)), allow_pickle=False)
            
            self.data_file = open(App.SAVE_FILE(user_id), 'rb+')
            self.data = np.load(self.data_file, allow_pickle=False)


    def replot_graphs(self):
        App.StddevGraphBpm.plot_data(self, self.data)
        App.StddevGraphDx.plot_data(self, self.data)
        App.StddevGraphNumNotes.plot_data(self, self.data)
        App.StddevGraphAngle.plot_data(self, self.data)
        App.StddevGraphVel.plot_data(self, self.data)
        App.StddevGraphSkill.plot_data(self, self.data)


    def __update_generated_map(self):
        bpm   = AppConfig.cfg['bpm']
        dx    = AppConfig.cfg['dx']
        angle = AppConfig.cfg['angle']
        rot   = AppConfig.cfg['rot']
        num   = AppConfig.cfg['repeats']
        notes = AppConfig.cfg['notes']

        pattern, is_clip = App.OsuUtils.generate_pattern2(rot*math.pi/180, dx, 60/bpm, angle*math.pi/180, notes, num)

        data_x = pattern[:, 0]
        data_y = -pattern[:, 1]
        data_t = pattern[:, 2]

        self.pattern_visual.set_map(data_x, data_y, data_t, AppConfig.cfg['cs'], AppConfig.cfg['ar'])

        return is_clip
        

    def __set_settings_edit_enabled(self, enabled):
        for widget in self.cfg_widgets.values():
            widget.setEnabled(enabled)


    def closeEvent(self, event):
        # Gracefully stop monitoring
        if self.engaged:
            self.__action_event()

        # Hide any widgets to allow the app to close
        self.area.hide()
        self.aim_graph.hide()
        self.pattern_visual.hide()
        self.data_list.hide()

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