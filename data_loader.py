from __future__ import print_function
import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
from ops import *
import numpy as np


def pre_emph(x, coeff=0.95):
    x0 = tf.reshape(x[0], [1,])
    diff = x[1:] - coeff * x[:-1]
    concat = tf.concat([x0, diff],0)
    return concat

def de_emph(y, coeff=0.95):
    if coeff <= 0:
        return y
    x = np.zeros(y.shape[0], dtype=np.float32)
    x[0] = y[0]
    for n in range(1, y.shape[0], 1):
        x[n] = coeff * x[n - 1] + y[n]
    return x

def read_and_decode(serialized_example, canvas_size, preemph=0.):  # Changed: use serialized_example as input parameter
    features = tf.parse_single_example(
        serialized_example,
        features={  # Changed: Removed tf prefix from FixedLenFeature and string
            'wav_raw': tf.io.FixedLenFeature([], tf.string),
            'noisy_raw': tf.io.FixedLenFeature([], tf.string),
        })
    wave = tf.decode_raw(features['wav_raw'], tf.int32)
    wave.set_shape([canvas_size])
    wave = (2./65535.) * tf.cast((wave - 32767), tf.float32) + 1.
    noisy = tf.decode_raw(features['noisy_raw'], tf.int32)
    noisy.set_shape([canvas_size])
    noisy = (2./65535.) * tf.cast((noisy - 32767), tf.float32) + 1.

    if preemph > 0:
        wave = tf.cast(pre_emph(wave, preemph), tf.float32)
        noisy = tf.cast(pre_emph(noisy, preemph), tf.float32)

    return wave, noisy
