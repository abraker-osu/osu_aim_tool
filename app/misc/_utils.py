import math
import numpy as np


class Utils():

    @staticmethod
    def get_traceback(e, msg):
        traceback_str = f'{msg}: {type(e).__name__} due to "{e}"\n'

        tb_curr = e.__traceback__
        while tb_curr != None:
            traceback_str += f'    File "{tb_curr.tb_frame.f_code.co_filename}", line {tb_curr.tb_lineno} in {tb_curr.tb_frame.f_code.co_name}\n'
            tb_curr = tb_curr.tb_next

        return traceback_str



class MathUtils():

    @staticmethod
    def normal_distr(x, avg, std):
        return 1/(std*((2*math.pi)**0.5))*math.exp(-0.5*((x - avg)/std)**2)


    @staticmethod
    def get_freq_hist(data):
        freq = np.zeros(data.shape[0])
        unique = np.unique(data)

        for val in unique:
            val_filter = (data == val)
            freq[val_filter] = np.arange(freq[val_filter].shape[0])

        return freq


    @staticmethod
    def calc_err(x_data, y_data, r, t_min, y=0):
        curve_fit = MathUtils.softplus_func(x_data, r, t_min, y)
        return np.sum(np.abs(y_data - curve_fit))


    @staticmethod
    def softplus_func(t, r, t_min, y=0):
        lin = r*(t - t_min)
        lin[lin < 100] = np.log(np.exp(lin[lin < 100]) + np.exp(y))
        return lin

    
    @staticmethod
    def linear_regresion(x, y):
        # Model processing. Needs at least 2 points.
        if y.shape[0] < 2:
            return None, None

        # Split data in half on x-axis and figure out if the data is increasing or decreasing
        left_half = x < np.median(x)
        right_half = x >= np.median(x)

        # If one of halves is empty, return None
        if not (any(left_half) and any(right_half)):
            return None, None

        y_left_avg = np.mean(y[x < np.median(x)])
        y_right_avg = np.mean(y[x >= np.median(x)])

        # Model linear curve
        # Visual example of how this works: https://i.imgur.com/k7H8bLe.png
        # 1) Take points on y-axis and x-axis, and split them into half - resulting in two groups
        avg_x = np.mean(x)
        avg_y = np.mean(y)

        if y_left_avg < y_right_avg:
            # Positive slope
            g1 = (x < avg_x) & (y < avg_y)    # Group 1 select
            g2 = (x >= avg_x) & (y >= avg_y)  # Group 2 select
        else:
            # Negative slope
            g1 = (x < avg_x) & (y >= avg_y)   # Group 1 select
            g2 = (x >= avg_x) & (y < avg_y)   # Group 2 select
        
        # Check if follows model by having positive linear slope
        if(not any(g1) or not any(g2)):
            return None, None

        # 2) Take the center of gravity for each of the two groups
        #    Those become points p1 and p2 to fit a line through
        p1x = np.mean(x[g1])
        p1y = np.mean(y[g1])

        p2x = np.mean(x[g2])
        p2y = np.mean(y[g2])

        # 3) Calculate slope and y-intercept
        m = (p1y - p2y)/(p1x - p2x)
        b = p1y - m*p1x

        return m, b
