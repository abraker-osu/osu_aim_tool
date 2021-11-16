import numpy as np


import math 


class OsuUtils():

    # Thanks joz#9960
    def generate_pattern2(initial_angle: 'float', distance: 'float|list[float]', time: 'float|list[float]', angle: 'float|list[float]', n_points: 'int', n_repeats: 'int' = 1) -> np.array:
        """
        Create a pattern of osu circles.

        parameters:
            initial_angle: direction of the first jump
            dist(s): a distance or list of distances between each note (wraps to start if size is less than n_points)
            time: a time offset or list of offsets between each note (wraps to start if size is less than n_points)
            angles: an angle or list of angles between each jump (wraps to start if size is than [n_points-1])
            n_points: number of distinct points in the pattern
            n_repeats: the pattern is played this many times, reversing direction on each repeat
        
        returns:
            np.array of [[x, y, t] for points in pattern]
        """
        dists  = np.array(distance, dtype='f').flatten()
        times  = np.array(time, dtype='f').flatten()
        angles = np.array(angle, dtype='f').flatten()
        rots   = np.array([ [[ np.cos(angle), -np.sin(angle) ], [ np.sin(angle), np.cos(angle) ]] for angle in angles ])

        curr_pos = np.array([ 0.0, 0.0 ])
        curr_dir = np.array([ np.cos(initial_angle), np.sin(initial_angle) ])

        points   = [ curr_pos ]
        delta_ts = []

        for i in range(n_points - 1):
            curr_pos = curr_pos + curr_dir * dists[i % len(dists)]
            delta_t  = times[i % len(times)]
            curr_dir = rots[i % len(angles)] @ curr_dir

            points.append(curr_pos)
            delta_ts.append(delta_t)

        center = (np.max(points, axis=0) + np.min(points, axis=0))/2
        points   = np.array(points) - center + [[ 256, 192 ]] 
        points   = np.pad(points, ((0, (n_repeats - 1)*n_points), (0, 0)), mode='reflect')
        delta_ts = np.pad(delta_ts, (1, (n_repeats - 1)*n_points), mode='symmetric')
        delta_ts[0] = 0

        data = np.column_stack((points, np.cumsum(delta_ts)))

        # osu! clips note positions into boundaries of the playfield
        is_clip = np.any((data[:, 0] < 0) | (data[:, 0] > 512)) or np.any((data[:, 1] < 0) | (data[:, 1] > 384))

        data[:, 0] = np.round(np.minimum(512, np.maximum(0, data[:, 0])))
        data[:, 1] = np.round(np.minimum(384, np.maximum(0, data[:, 1])))

        return data, is_clip


    @staticmethod
    def ar_to_ms(ar: 'float') -> float:
        if ar <= 5: return 1800 - 120*ar
        else:       return 1950 - 150*ar


    @staticmethod
    def ms_to_ar(ms: 'float') -> float:
        if ms >= 1200: return (1800 - ms)/120
        else:          return (1950 - ms)/150

    
    @staticmethod
    def cs_to_px(cs: 'float') -> float:
        return (109 - 9*cs)


    @staticmethod
    def approach_circle_to_radius(cs_px: 'float', ar_ms: 'float', dt: 'float') -> float:
        return cs_px*(1 + 3*dt/ar_ms)