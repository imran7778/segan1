from __future__ import print_function
import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
from tensorflow.keras.layers import BatchNormalization, Dense, Flatten
from tensorflow.keras.initializers import glorot_uniform as xavier_initializer
from ops import *
import numpy as np

def discriminator(self, wave_in, reuse=False):
    """
    wave_in: waveform input
    """
    # take the waveform as input "activation"
    in_dims = wave_in.get_shape().as_list()
    hi = wave_in
    if len(in_dims) == 2:
        hi = tf.expand_dims(wave_in, -1)
    elif len(in_dims) < 2 or len(in_dims) > 3:
        raise ValueError('Discriminator input must be 2-D or 3-D')

    # Get the batch size dynamically
    batch_size = tf.shape(wave_in)[0]

    # set up the disc_block function
    with tf.variable_scope('d_model', reuse=reuse) as scope:
        if reuse:
            scope.reuse_variables()

        def disc_block(block_idx, input_, kwidth, nfmaps, bnorm, activation, pooling=2):
            with tf.variable_scope('d_block_{}'.format(block_idx)):
                if not reuse:
                    print('D block {} input shape: {}'.format(block_idx, input_.get_shape()), end=' *** ')
                bias_init = None
                if self.bias_D_conv:
                    if not reuse:
                        print('biasing D conv', end=' *** ')
                    bias_init = tf.constant_initializer(0.)
                downconv_init = tf.truncated_normal_initializer(stddev=0.02)
                hi_a = downconv(input_, nfmaps, kwidth=kwidth, pool=pooling, init=downconv_init, bias_init=bias_init)
                if not reuse:
                    print('downconved shape: {}'.format(hi_a.get_shape()), end=' *** ')
                if bnorm:
                    if not reuse:
                        print('Applying VBN', end=' *** ')
                    hi_a = self.vbn(hi_a, 'd_vbn_{}'.format(block_idx))
                if activation == 'leakyrelu':
                    if not reuse:
                        print('Applying Lrelu', end=' *** ')
                    hi = leakyrelu(hi_a)
                elif activation == 'relu':
                    if not reuse:
                        print('Applying Relu', end=' *** ')
                    hi = tf.nn.relu(hi_a)
                else:
                    raise ValueError('Unrecognized activation {} in D'.format(activation))
                # Print output shape of each block
                if not reuse:
                    print('D block {} output shape: {}'.format(block_idx, hi.get_shape()))
                return hi

        # Apply input noisy layer to real and fake samples
        hi = gaussian_noise_layer(hi, self.disc_noise_std)
        if not reuse:
            print('*** Discriminator summary ***')
        for block_idx, fmaps in enumerate(self.d_num_fmaps):
            hi = disc_block(block_idx, hi, 31, self.d_num_fmaps[block_idx], True, 'leakyrelu')
            if not reuse:
                print()
        if not reuse:
            print('discriminator deconved shape: ', hi.get_shape())

        # Properly flatten hi with known dimensions
        hi_shape = hi.get_shape().as_list()
        # Ensure the shape is fully defined before passing to Dense layer
        hi_f = tf.reshape(hi, [batch_size, -1])  # Ensures batch_size dimension is dynamic

        # Ensure the shape is known and defined before passing to the Dense layer
        dense_input_shape = hi_f.get_shape().as_list()
        if None in dense_input_shape:
            raise ValueError("Dense layer input shape must be fully defined. Current shape: {}".format(dense_input_shape))

        # Use a Dense layer to produce the final output
        with tf.variable_scope('d_dense'):
            d_logit_out = Dense(1, activation=None)(hi_f)  # Ensure shape is known before Dense layer

        if not reuse:
            print('discriminator output shape: ', d_logit_out.get_shape())
            print('*****************************')
        return d_logit_out
