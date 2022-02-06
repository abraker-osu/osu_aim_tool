import watchdog.observers
import watchdog.events
import os



class Monitor(watchdog.observers.Observer):

    def __init__(self, osu_path):
        watchdog.observers.Observer.__init__(self)

        if not os.path.exists(osu_path):
            raise Exception(f'"{osu_path}" does not exist!')

        self.paused = False

        self.osu_path = osu_path
        self.monitors = {}
        self.start()


    def __del__(self):
        self.stop()


    def pause(self):
        self.paused = True


    def resume(self):
        self.paused = False


    def create_replay_monitor(self, name, callback):
        replay_path = f'{self.osu_path}/Data/r'
        if not os.path.exists(replay_path):
            raise Exception(f'"{replay_path}" does not exist!')

        export_path = f'{self.osu_path}/Replays'
        if not os.path.exists(export_path):
            raise Exception(f'"{export_path}" does not exist!')

        class EventHandler(watchdog.events.FileSystemEventHandler):
            def on_created(self, event, paused=self.paused): 
                if not paused:
                    if '.osr' in event.src_path:
                        callback(event.src_path)

        self.monitors[f'{name}_r0'] = self.schedule(EventHandler(), replay_path, recursive=False)
        self.monitors[f'{name}_r1'] = self.schedule(EventHandler(), export_path, recursive=False)
        print(f'Created file creation monitor for {self.osu_path}/Data/r and {self.osu_path}/Replays')
        

    def create_map_montor(self, name, callback, beatmap_path):
        # TODO
        pass
