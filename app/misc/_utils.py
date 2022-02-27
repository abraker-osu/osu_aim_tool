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
    def r_squared(y_data, y_model):
        y_data_mean = np.mean(y_data)
        ss_res = np.sum((y_data - y_model)**2)
        ss_tot = np.sum((y_data - y_data_mean)**2)

        return 1 - (ss_res/ss_tot)


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
        x_avg = np.mean(x)
        y_avg = np.mean(y)

        ss_xx = np.sum((x - x_avg)**2)
        ss_xy = np.sum((x - x_avg)*(y - y_avg))
        
        b = ss_xy/ss_xx          # slope
        c = y_avg - (b * x_avg)  # y-intercept
        
        return b, c


    def exp_regresion(x, y):
        '''
        Thanks: https://math.stackexchange.com/a/2318659
        Fits y = a + be^(cx)
        '''
        if y.shape[0] < 4:
            return None, None, None

        if y.shape[0] != x.shape[0]:
            raise ValueError('x and y must have the same length')

        s = np.zeros(x.shape[0])
        for k in range(1, x.shape[0]):
            s[k] = s[k-1] + (x[k] - x[k-1])*(y[k] + y[k-1])/2

        mat_c0 = np.linalg.inv(np.asarray([
            [ np.sum((x - x[0])**2),  np.sum((x - x[0])*s) ],
            [ np.sum((x - x[0])*s),   np.sum(s**2)         ]
        ]))

        mat_c1 = np.asarray([
            [ np.sum((y - y[0])*(x - x[0])) ],
            [ np.sum((y - y[0])*s) ]
        ]),

        mat_dot = np.dot(mat_c0, mat_c1)
        c = mat_dot[1][0][0]

        mat_ab0 = np.linalg.inv(np.asarray([
            [ x.shape[0],          np.sum(np.exp(c*x))   ],
            [ np.sum(np.exp(c*x)), np.sum(np.exp(2*c*x)) ]
        ]))

        mat_ab1 = np.asarray([
            [ np.sum(y) ],
            [ np.sum(y*np.exp(c*x)) ]
        ])

        mat_dot = np.dot(mat_ab0, mat_ab1)
        a = mat_dot[0][0]
        b = mat_dot[1][0]

        return a, b, c


    @staticmethod
    def softplus_regression(x, y):
        a, b, c = MathUtils.exp_regresion(x, y)
        exp_model = lambda a, b, c, x: a + b*np.exp(c*x)

        exp_180 = exp_model(a, b, c, 180)
        exp_90  = exp_model(a, b, c, 90)
        exp_0   = exp_model(a, b, c, 0)

        a_ln  = np.exp(exp_0  - exp_180) - 1
        b0_ln = np.exp(exp_90 - exp_180) - 1
        b1_ln = np.exp(exp_0  - exp_90)  - 1
        b_ln  = (1/90)*np.log(b0_ln/b1_ln)

        return a_ln, b_ln, exp_180


