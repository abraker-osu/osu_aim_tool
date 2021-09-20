import numpy as np
import textwrap
import json
import time
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

    SAVE_FILE_X = 'data/back_and_forth_data_x.npy'
    SAVE_FILE_Y = 'data/back_and_forth_data_y.npy'

    COL_STDEV = 0
    COL_BPM   = 1
    COL_PX    = 2
    COL_ANGLE = 3
    COL_NUM   = 4
    NUM_COLS  = 5

    from .misc._dock_patch import updateStylePatched
    from .misc.value_edit import ValueEdit
    from .misc.monitor import Monitor

    # Left column
    from ._stdev_graph_bpm import StddevGraphBpm
    from ._stdev_graph_dx import StddevGraphDx
    #from ._stdev_graph_theta import StddevGraphTheta
    from ._aim_graph import AimGraph

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        os.makedirs('data', exist_ok=True)

        try: 
            self.data_file_x = open(App.SAVE_FILE_X, 'rb+')
            #self.data_file_y = open(App.SAVE_FILE_Y, 'rb+')

            self.data_x = np.load(self.data_file_x, allow_pickle=False)
            #self.data_y = np.load(self.data_file_y, allow_pickle=False)
        except FileNotFoundError:
            print('Data file not found. Creating...')

            self.data_x = np.asarray([])
            #self.data_y = np.asarray([])
            np.save(App.SAVE_FILE_X, np.empty((0, App.NUM_COLS)), allow_pickle=False)
            
            self.data_file_x = open(App.SAVE_FILE_X, 'rb+')
            #self.data_file_Y = open(App.SAVE_FILE_Y, 'rb+')

            self.data_x = np.load(self.data_file_x, allow_pickle=False)
            #self.data_y = np.load(self.data_file_y, allow_pickle=False)

        self.__init_gui()
        self.__build_layout()

        if self.__load_settings():    
            try:
                self.monitor = App.Monitor(self.osu_path)
                self.monitor.create_replay_monitor('back_and_forth_monitor', self.__record_results)
            except Exception as e:
                self.status_txt.setText(str(e) + ' Is osu! path correct?')

        App.StddevGraphBpm.plot_data(self, self.data_x)
        App.StddevGraphDx.plot_data(self, self.data_x)

        self.show()


    def __init_gui(self):
        self.graphs = {}
        self.engaged = False

        self.main_widget = QtGui.QWidget()
        self.main_layout = QtGui.QVBoxLayout(self.main_widget)

        self.perf_chkbx = QtGui.QCheckBox('Show performance')
        self.aim_chkbx  = QtGui.QCheckBox('Show hits')

        self.edit_layout = QtGui.QHBoxLayout()
        self.angle_edit  = App.ValueEdit(0, 360, 360, 'Deg')
        self.bpm_edit    = App.ValueEdit(1, 1200, 1200, 'BPM')
        self.bpm_edit    = App.ValueEdit(1, 1200, 1199, 'BPM')
        self.dx_edit     = App.ValueEdit(0, 512, 512, 'Spacing')
        self.num_edit    = App.ValueEdit(0, 1000, 1000, '# Notes')
        self.cs_edit     = App.ValueEdit(0, 10, 100, 'CS', is_float=True)
        self.ar_edit     = App.ValueEdit(0, 10, 100, 'AR', is_float=True)

        self.action_btn = QtGui.QPushButton('Start')
        self.status_txt = QtGui.QLabel('Set settings and click start!')

        self.area = DockArea()
        self.aim_graph = App.AimGraph()
        

    def __build_layout(self):
        self.edit_layout.addWidget(self.bpm_edit)
        self.edit_layout.addWidget(self.dx_edit)
        self.edit_layout.addWidget(self.angle_edit)
        self.edit_layout.addWidget(self.num_edit)
        self.edit_layout.addWidget(self.cs_edit)
        self.edit_layout.addWidget(self.ar_edit)

        self.main_layout.addWidget(self.perf_chkbx)
        self.main_layout.addWidget(self.aim_chkbx)
        self.main_layout.addLayout(self.edit_layout)
        self.main_layout.addWidget(self.action_btn)
        self.main_layout.addWidget(self.status_txt)

        self.setCentralWidget(self.main_widget)

        # Left column
        App.StddevGraphBpm.__init__(self, pos='top', dock_name='Variance vs BPM')
        App.StddevGraphDx.__init__(self, pos='below', relative_to='StddevGraphBpm', dock_name='Variance vs Spacing')
        #App.StddevGraphAngle.__init__(self, pos='top')

        self.perf_chkbx.stateChanged.connect(self.__perf_chkbx_event)
        self.aim_chkbx.stateChanged.connect(self.__aim_chkbx_event)

        self.bpm_edit.value_changed.connect(self.__bpm_edit_event)
        self.dx_edit.value_changed.connect(self.__dx_edit)
        self.angle_edit.value_changed.connect(self.__angle_edit)
        self.num_edit.value_changed.connect(self.__num_edit)
        self.cs_edit.value_changed.connect(self.__cs_edit)
        self.ar_edit.value_changed.connect(self.__ar_edit)

        self.action_btn.pressed.connect(self.__action_event)

        self.area.setWindowFlags(QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowMinimizeButtonHint)
        self.perf_chkbx.setChecked(True)


    def __load_settings(self):
        # Load osu_dir setting
        try:
            with open('config.json') as f:
                cfg = json.load(f)
        except FileNotFoundError:
            cfg = { 'osu_dir' : '' }
            with open('config.json', 'w') as f:
                json.dump(cfg, f, indent=4)

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

        try: self.num_edit.set_value(cfg['num'])
        except KeyError: self.num_edit.set_value(60)
        
        try: self.cs_edit.set_value(cfg['cs'])
        except KeyError: self.cs_edit.set_value(4)

        try: self.ar_edit.set_value(cfg['ar'])
        except KeyError: self.ar_edit.set_value(8)

        self.bpm   = self.bpm_edit.get_value()
        self.dx    = self.dx_edit.get_value()
        self.angle = self.angle_edit.get_value()
        self.num   = self.num_edit.get_value()
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


    def __bpm_edit_event(self, value):
        with open('config.json') as f:
            cfg = json.load(f)
        
        cfg['bpm'] = value
        self.bpm = self.bpm_edit.get_value()

        with open('config.json', 'w') as f:
            json.dump(cfg, f, indent=4)
        

    def __dx_edit(self, value):
        with open('config.json') as f:
            cfg = json.load(f)
        
        cfg['dx'] = value
        self.dx = self.dx_edit.get_value()

        with open('config.json', 'w') as f:
            json.dump(cfg, f, indent=4)


    def __cs_edit(self, value):
        with open('config.json') as f:
            cfg = json.load(f)
        
        cfg['cs'] = value
        self.cs = self.cs_edit.get_value()
        self.aim_graph.set_cs(value)

        with open('config.json', 'w') as f:
            json.dump(cfg, f, indent=4)


    def __angle_edit(self, value):
        with open('config.json') as f:
            cfg = json.load(f)
        
        cfg['angle'] = value
        self.angle = self.angle_edit.get_value()

        with open('config.json', 'w') as f:
            json.dump(cfg, f, indent=4)


    def __num_edit(self, value):
        with open('config.json') as f:
            cfg = json.load(f)
        
        cfg['num'] = value
        self.num = self.num_edit.get_value()

        with open('config.json', 'w') as f:
            json.dump(cfg, f, indent=4)




    def __ar_edit(self, value):
        with open('config.json') as f:
            cfg = json.load(f)
        
        cfg['ar'] = value
        self.ar = self.ar_edit.get_value()
        self.aim_graph.set_ar(value)

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
        self.num_edit.value_enter()
        self.cs_edit.value_enter()
        self.ar_edit.value_enter()

        # Check if all settings are proper
        is_error = \
            self.bpm_edit.is_error() or   \
            self.dx_edit.is_error() or    \
            self.angle_edit.is_error() or \
            self.num_edit.is_error() or   \
            self.cs_edit.is_error() or    \
            self.ar_edit.is_error()

        if is_error:
            return

        # Generates and saves the beatmap. Then monitor for new replay in the /data/r folder
        map_path = f'{self.osu_path}/Songs/aim_tool'

        self.status_txt.setText('Generating map...')
        self.__generate_map(map_path, self.bpm, self.dx, self.num, self.cs)
        self.__monitor_replay()

        # This needs to be after `monitor_replay`. `monitor replay` will wait until a replay is detected
        # So if we are in replay waiting state, it means the button was pressed while waiting for replay, so we abort
        if not self.engaged:
            return

        # Otherwise, replay was successfully detected and we can update the state to reflect that
        self.engaged = False

        # Data from map and replay -> score
        aim_x_offsets, aim_y_offsets = self.__get_data(map_path)
        if type(aim_x_offsets) == type(None) or type(aim_y_offsets) == type(None):
            self.status_txt.setText(self.status_txt.text() + '\nSet settings and click start!')
            self.action_btn.setText('Start')
            return

        # Update deviation data and plots
        self.__write_data(aim_x_offsets, aim_y_offsets, self.bpm, self.dx, self.num, self.cs. self.ar)
        
        App.StddevGraphBpm.plot_data(self, self.data_x)
        App.StddevGraphDx.plot_data(self, self.data_x)
        self.aim_graph.plot_data(aim_x_offsets, aim_y_offsets)
        
        self.status_txt.setText('Set settings and click start!')
        self.action_btn.setText('Start')


    def __generate_map(self, map_path, bpm, px, num_notes, cs, ar):
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
            Version:back_and_forth_{bpm}_{px}
            Source:
            Tags:
            BeatmapID:0
            BeatmapSetID:882805

            [Difficulty]
            HPDrainRate:8
            CircleSize:{cs}
            OverallDifficulty:0
            ApproachRate:{ar}
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

        px_c = 256
        ms_t = 60*1000/bpm

        # Generate notes
        for i in range(0, num_notes, 2):
            beatmap_data += textwrap.dedent(
                f"""
                {int(px_c - px/2)},192,{int((i + 0)*ms_t)},5,0,0:0:0:0:
                {int(px_c + px/2)},192,{int((i + 1)*ms_t)},1,0,0:0:0:0:\
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
            return None, None

        # Process score data
        score_data = StdScoreData.get_score_data(replay_data, map_data)

        hit_types_miss = score_data['type'] == StdScoreData.TYPE_MISS
        num_total = score_data['type'].values.shape[0]
        num_misses = score_data['type'].values[hit_types_miss].shape[0]

        # Too many misses tends to falsely lower the deviation. Disallow plays with >10% misses
        print(f'num total hits: {num_total}   num: misses {num_misses} ({100 * num_misses/num_total:.2f}%)')
        if num_misses/num_total > 0.1:
            self.status_txt.setText('Invalid play. Too many misses.')
            return None, None

        aim_x_offsets = score_data['replay_x'] - score_data['map_x']
        aim_y_offsets = score_data['replay_y'] - score_data['map_y']

        # Correct for incoming direction
        x_map_vecs = score_data['map_x'].values[1:] - score_data['map_x'].values[:-1]
        y_map_vecs = score_data['map_y'].values[1:] - score_data['map_y'].values[:-1]

        map_thetas = np.arctan2(y_map_vecs, x_map_vecs)
        hit_thetas = np.arctan2(aim_y_offsets, aim_x_offsets)
        mags   = (aim_x_offsets**2 + aim_y_offsets**2)**0.5

        aim_x_offsets = mags*np.cos(map_thetas - hit_thetas[1:])
        aim_y_offsets = mags*np.sin(map_thetas - hit_thetas[1:])

        return aim_x_offsets, aim_y_offsets


    def __write_data(self, aim_offsets_x, aim_offsets_y, bpm, px, angle, num_notes):
        stddev_x = np.std(aim_offsets_x)

        # Close data file for writing
        self.data_file_x.close()
        #self.data_file_y.close()

        # Find record based on bpm and spacing
        data_filter = (self.data_x[:, App.COL_BPM] == bpm) & (self.data_x[:, App.COL_PX] == px)

        if np.any(data_filter):
            # A record exists, update it
            print(f'bpm: {bpm}   dx: {px}   aim stddev (x-axis): {stddev_x} (best: {self.data_x[data_filter, App.COL_STDEV]})')
            #print(f'aim stddev (y-axis): {stddev_y}')

            self.data_x[data_filter, App.COL_STDEV] = min(stddev_x, np.min(self.data_x[data_filter, App.COL_STDEV]))
        else:
            # Create a new record
            print(f'bpm: {bpm}   dx: {px}   aim stddev (x-axis): {stddev_x}')
            #print(f'aim stddev (y-axis): {stddev_y}')
            self.data_x = np.insert(self.data_x, 0, np.asarray([ stddev_x, bpm , px, angle, num_notes ]), axis=0)
        
        # Save data to file
        np.save(App.SAVE_FILE_X, self.data_x, allow_pickle=False)

        # Now reopen it so it can be used
        self.data_file_x = open(App.SAVE_FILE_X, 'rb+')
        self.data_x = np.load(self.data_file_x, allow_pickle=False)


    def closeEvent(self, event):
        # Gracefully stop monitoring
        if self.engaged:
            self.monitor.pause()

        # Hide any widgets to allow the app to close
        self.area.hide()
        self.aim_graph.hide()

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