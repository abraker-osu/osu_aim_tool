import numpy as np


import math 


class OsuUtils():

    def generate_pattern(bpm: 'float', dx: 'float', angle: 'float', rot: 'float', num: 'float') -> np.array:
        """
        Create a pattern of osu circles.

        parameters:
            bpm: Rate of pattern
            dx: Distance between each note
            angle: angle of the middle jump
            rot: Orientation of the entire pattern
            num: The pattern is played this many times, reversing direction on each repeat
        
        returns:
            np.array of [[x, y, t] for points in pattern]
        """
        ms_t = 60/bpm
        rad  = math.pi/180

        p1x = (dx/2)*math.cos(rad*rot)
        p1y = (dx/2)*math.sin(rad*rot)

        p2x = -(dx/2)*math.cos(rad*rot)
        p2y = -(dx/2)*math.sin(rad*rot)

        p3x = dx*math.cos(rad*rot + rad*angle) + p2x
        p3y = dx*math.sin(rad*rot + rad*angle) + p2y

        px_cx = 1/3*(p1x + p2x + p3x)
        px_cy = 1/3*(p1y + p2y + p3y)

        p1x = int(p1x + 256 - px_cx)
        p1y = int(p1y + 192 - px_cy)
        
        p2x = int(p2x + 256 - px_cx)
        p2y = int(p2y + 192 - px_cy)

        p3x = int(p3x + 256 - px_cx)
        p3y = int(p3y + 192 - px_cy)

        data_x = np.tile([p1x, p2x, p3x, p2x], 1 + int(num/4))
        data_y = np.tile([-p1y, -p2y, -p3y, -p2y], 1 + int(num/4))
        data_t = np.arange(0, data_x.shape[0])*ms_t

        return np.column_stack((data_x, data_y, data_t))


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

        points   = np.array(points) + [[ 320,240 ]] - np.mean(points, axis=0)
        points   = np.pad(points, ((0, (n_repeats - 1)*(n_points - 1)), (0,0)), mode='reflect')
        delta_ts = np.pad(delta_ts, (1,(n_repeats - 1)*(n_points - 1)), mode='symmetric')
        delta_ts[0] = 0

        return np.column_stack((points, np.cumsum(delta_ts)))


    @staticmethod
    def ar_to_ms(ar: 'float') -> float:
        if ar <= 5: return 1800 - 120*ar
        else:       return 1950 - 150*ar

    
    @staticmethod
    def cs_to_px(cs: 'float') -> float:
        return (109 - 9*cs)


    @staticmethod
    def approach_circle_to_radius(cs_px: 'float', ar_ms: 'float', dt: 'float') -> float:
        return cs_px*(1 + 3*dt/ar_ms)