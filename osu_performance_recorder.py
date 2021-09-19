import os
import sys
import time
import tinydb

from PyQt5 import QtCore
import numpy as np

from osu_analysis import ManiaActionData, ManiaScoreData
from osu_analysis import BeatmapIO, ReplayIO, Gamemode
from osu_db_reader.osu_db_reader import OsuDbReader
from monitor import Monitor



class Data():    
    MAP_ID    = 0
    TIMESTAMP = 1 
    TIMINGS   = 2
    OFFSETS   = 3
    HIT_TYPE  = 4
    KEYS      = 5
    HASH      = 6
    MODS      = 7
    NUM_COLS  = 8


class Recorder(QtCore.QObject):

    __new_replay_event = QtCore.pyqtSignal(tuple)

    SAVE_FILE = 'data/osu_performance_recording_v2.npy'

    def __init__(self, osu_path, callback):
        QtCore.QObject.__init__(self)

        self.__new_replay_event.connect(callback)
        os.makedirs('data', exist_ok=True)

        # For resolving replays to maps
        self.db = tinydb.TinyDB('data/maps.json')
        self.maps_table = self.db.table('maps')
        self.meta_table = self.db.table('meta')

        self.osu_path = osu_path
        self.__check_maps_db()

        try: 
            self.data_file = open(Recorder.SAVE_FILE, 'rb+')
            self.data = np.load(self.data_file, allow_pickle=False)
        except FileNotFoundError:
            print('Data file not found. Creating...')

            self.data = np.asarray([])
            np.save(Recorder.SAVE_FILE, np.empty((0, Data.NUM_COLS)), allow_pickle=False)
            
            self.data_file = open(Recorder.SAVE_FILE, 'rb+')
            self.data = np.load(self.data_file, allow_pickle=False)

        if len(self.data) != 0:
            self.__new_replay_event.emit((self.maps_table, self.data, None))

        self.monitor = Monitor(osu_path)
        self.monitor.create_replay_monitor('Replay Grapher', self.__handle_new_replay)


    def __del__(self):
        self.data_file.close()


    def __save_data(self, data):
        # TODO:
        # [ 
        #   hit_offset, release_offset       # hit timing
        #   keys, timestamp, map_id          # metadata
        #   ic0, ic1, ic2, ... ic18,         # note offset from current hit to prev note of each column
        #   ip0, ip1, ip2, ... ip18,         # note offset from prev hit to prev prev note of each column
        #   h0, h1, h2, ... h18,             # hold state for each column at release timing
        #   
        # ]
        self.data_file.close()

        self.data = np.insert(self.data, 0, data, axis=0)
        np.save(Recorder.SAVE_FILE, self.data, allow_pickle=False)

        # Now reopen it so it can be used
        self.data_file = open(Recorder.SAVE_FILE, 'rb+')
        self.data = np.load(self.data_file, allow_pickle=False)


    def __handle_new_replay(self, replay_path):
        time.sleep(1)
    
        #print('New replay detected!')

        try: replay, beatmap, hash = self.__get_files(replay_path)
        except TypeError: return

        map_data = ManiaActionData.get_action_data(beatmap)
        replay_data = ManiaActionData.get_action_data(replay)
        mods = self.__process_mods(map_data, replay_data, replay)

        score_data = ManiaScoreData.get_score_data(map_data, replay_data)

        # Get data
        data = self.__get_data(hash, mods, beatmap.difficulty.cs, map_data, score_data, beatmap.metadata.beatmap_id)
        self.__save_data(data)

        self.__new_replay_event.emit((self.maps_table, self.data, beatmap.metadata.name + ' ' + replay.get_name()))


    def __process_mods(self, map_data, replay_data, replay):
        mods = 0

        if replay.mods.has_mod('DT') or replay.mods.has_mod('NC'):
            mods |= (1 << 0)

        if replay.mods.has_mod('HT'):
            mods |= (1 << 1)

        if replay.mods.has_mod('MR'):
            num_keys = ManiaActionData.num_keys(map_data)
            map_data[:, ManiaActionData.IDX_COL] = (num_keys - 1) - map_data[:, ManiaActionData.IDX_COL]

        return mods


    def __check_maps_db(self):
        if len(self.maps_table) == 0:
            data = OsuDbReader.get_beatmap_md5_paths(f'{self.osu_path}/osu!.db')
            self.maps_table.insert_multiple(data)
            
            num_beatmaps_read = OsuDbReader.get_num_beatmaps(f'{self.osu_path}/osu!.db')
            self.meta_table.upsert({ 'num_maps' : num_beatmaps_read }, tinydb.where('num_maps').exists())

            last_modified_read = os.stat(f'{self.osu_path}/osu!.db').st_mtime
            self.meta_table.upsert({ 'last_modified' : last_modified_read }, tinydb.where('last_modified').exists())

            print('Map table did not exist - created it')
            return

        num_beatmaps_read = OsuDbReader.get_num_beatmaps(f'{self.osu_path}/osu!.db')
        num_beatmaps_save = self.meta_table.get(tinydb.where('num_maps').exists())
        if num_beatmaps_save != None:
            num_beatmaps_save = num_beatmaps_save['num_maps']

        last_modified_read = os.stat(f'{self.osu_path}/osu!.db').st_mtime
        last_modified_save = self.meta_table.get(tinydb.where('last_modified').exists())
        if last_modified_save != None:
            last_modified_save = last_modified_save['last_modified']

        num_maps_changed = num_beatmaps_read != num_beatmaps_save
        osu_db_modified = last_modified_read != last_modified_save

        if num_maps_changed or osu_db_modified:
            if osu_db_modified:
                user_input = input('osu!.db was modified. If you modified a map for testing, it will not be found until you rebuild db. Rebuild db? (y/n)')
                if not 'y' in user_input.lower(): return

            data = OsuDbReader.get_beatmap_md5_paths(f'{self.osu_path}/osu!.db')
            self.db.drop_table('maps')
            self.maps_table = self.db.table('maps')
            self.maps_table.insert_multiple(data)

            self.meta_table.upsert({ 'num_maps' : num_beatmaps_read }, tinydb.where('num_maps').exists())
            self.meta_table.upsert({ 'last_modified' : last_modified_read }, tinydb.where('last_modified').exists())

        print(num_beatmaps_read, num_beatmaps_save)
        print(last_modified_read, last_modified_save)


    def __get_files(self, replay_path):
        try: replay = ReplayIO.open_replay(replay_path)
        except Exception as e:
            print(f'Error opening replay: {e}')
            return

        if replay.game_mode != Gamemode.MANIA:
            print('Only mania gamemode supported for now')            
            return

        print('Determining beatmap...')

        maps = self.maps_table.search(tinydb.where('md5') == replay.beatmap_hash)
        if len(maps) == 0:
            print('Associated beatmap not found. Do you have it?')
            return

        path = f'{self.osu_path}/Songs'
        beatmap = BeatmapIO.open_beatmap(f'{self.osu_path}/Songs/{maps[0]["path"]}')

        return replay, beatmap, maps[0]["md5"]


    #@jit(nopython=True, parellel=True)
    def __get_data(self, md5, mods, num_keys, map_data, score_data, beatmap_id):
        '''
            [ offset, timing, n1, n2, n3, ...  ],
            [ offset, timing, n1, n2, n3, ... ],
            ...
        '''
        note_intervals = [ [] for i in range(int(num_keys)) ]
        data = []
        current_time = time.time()
        hash_mask = 0xFFFFFFFFFFFF0000

        for ref_col in range(int(num_keys)):
            # Get scoring data for the current column
            score_ref_col = score_data.loc[ref_col]

            # Get replay hitoffsets and timings for those offsets
            offsets = (score_ref_col['replay_t'] - score_ref_col['map_t']).values
            htypes  = score_ref_col['type'].values

            if mods & (1 << 0):    # DT
                timings = score_ref_col['replay_t'].values / 1.5
                offsets = offsets*2/3
            elif mods & (1 << 1):  # HT
                timings = score_ref_col['replay_t'].values * 1.5
                offsets = offsets*3/2
            else:                  # NM
                timings = score_ref_col['replay_t'].values

            # Additional metadata
            col_dat    = np.full_like(offsets, ref_col)
            id_dat     = np.full_like(offsets, beatmap_id)
            timestamp  = np.full_like(offsets, current_time)
            hash       = np.full_like(offsets, int(md5, 16) & hash_mask)
            mod_data   = np.full_like(offsets, mods)

            '''
            for col in range(int(num_keys)):
                # Get note times where needed to press for other column
                score_oth_col = score_data.loc[col]
                oth_col_times = score_oth_col['map_t']

                # Then get interval between the hit note and previous
                if ref_col == col:
                    # If it's the same column, take note interval difference
                    intervals = np.zeros(ref_col_times.shape)
                    intervals[1:] = np.diff(ref_col_times)
                    intervals[0] = np.inf
                else:
                    # Otherwise get note interval difference to nearest precending note
                    intervals = self.__diff_nearest(ref_col_times.values, oth_col_times.values)

                # Save note interval data reference to column
                note_intervals[col] = intervals
            '''
            
            # Append data entries for column
            data.append(np.c_[ id_dat, timestamp, timings, offsets, htypes, col_dat, hash, mod_data ])

        # Concate data accross all columns
        return np.concatenate(data)


    def __diff_nearest(self, n1, n0):
        # For each n1 takes the closest preceeding value in n0 and diffs them
        # If there is no preceeding value, then result is np.inf
        res = np.digitize(n1, n0)

        filt = res != 0
        res = res[filt] - 1

        ret = np.zeros(n1.shape)
        ret[filt] = n1[filt] - n0[res]
        ret[~filt] = np.inf

        return ret