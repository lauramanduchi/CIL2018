import tensorflow as tf


"""
Take a single input - a randomly-sampled vector z from known distribution pz.
First hidden layer h_0 needs reshaping to be small image-shaped array to be sent through the network -> upscaled [1000×1000] image at the end. 
Take the linearly-transformed z-values and reshape to [4x4xnumkernels]. Also -1 to do this for all images in the batch.

Gradual Upscale to the size of image_size:
 - Chose factor of 2 in each layer
 - # of upsamplings to be done = log(image size)/log(2)  2^(num of layers)=1000 in our case
"""

"""
Once it works:
https://github.com/soumith/ganhacks
"""

class Generator(object):

    def __init__(self, z, batch_size, z_dim, reuse=False, g_dim = 64, c_dim = 1):
        """

        :param z: noise
        :param batch_size:
        :param z_dim:
        :param reuse:
        :param g_dim: Number of filters of first layer of generator
        :param c_dim: Colour dimension of output (1 for grayscale )
        """
        print("Initializing generator")
        self.reuse = reuse
        self.g_dim = g_dim
        self.c_dim = c_dim

        # (When building network) - Network inputs
        self.input_noise = tf.placeholder(dtype=tf.float32, shape=[None, 1000, 1000], name='input_noise')
        # Add 1 dimension to input to have [batch, in_height, in_width, in_channels], where in_channels=1
        self.input_noise = tf.expand_dims(self.input_noise, 3)

        # parameters to confirm
        output_size = 1000  # Output size of the image

        # Gradual upscaling parameters
        upscale0 = 2   # int(output_size/16)+1, if output_size = 28
        upscale1 = 25  # int(output_size/8)
        upscale2 = 250  # int(output_size/4)-1
        upscale3 = 500  # int(output_size/2)-2

        # Deconvolution parameters
        W_size = 5

        print("z: {}".format(z.shape))

        # reshaping input
        h0 = tf.reshape(z, [batch_size, upscale0, upscale0, 25])
        # Last integer of reshape must be such that z_dimensions = upscale0*upscale0* integer
        print('shape h0: {}'.format(h0.shape))
        h0 = tf.nn.relu(h0)
        print('shape h0: {}'.format(h0.shape))

        # Dimensions of h0 = batch_size x 2 x 2 x 25

        with tf.device('/gpu:0'):
            with tf.variable_scope("discriminator") as scope:

                # if (reuse):
                #     scope.reuse_variables()

                # First DeConvolution Layer
                # output1_shape as 4-D array of images: (batch, height, width, channels)
                output1_shape = [batch_size, upscale1, upscale1, g_dim*4]
                print('output1_shape: {}'.format(output1_shape))
                print('output1_shape[-1]: {}'.format(output1_shape[-1]))

                print("int(h0.get_shape()[-1]): {}".format(int(h0.get_shape()[-1])))
                W_conv1 = tf.get_variable('g_wconv1', [W_size, W_size, output1_shape[-1], int(h0.get_shape()[-1])],
                                          # [filter_height, filter_width, 1, out_channels1]
                                          initializer=tf.truncated_normal_initializer(stddev=0.1))
                b_conv1 = tf.get_variable('g_bconv1', [output1_shape[-1]], initializer=tf.constant_initializer(.1))
                H_conv1 = tf.nn.conv2d_transpose(h0, W_conv1, output_shape=output1_shape,
                                                 strides=[1, 2, 2, 1], padding='SAME') + b_conv1
                H_conv1 = tf.contrib.layers.batch_norm(inputs = H_conv1, center=True, scale=True, is_training=True, scope="g_bn1")
                H_conv1 = tf.nn.relu(H_conv1)
                #Dimensions of H_conv1 = batch_size x 3 x 3 x 256

                # Second DeConv Layer
                output2_shape = [batch_size, upscale2, upscale2, g_dim*2]
                print("output2_shape: {}".format(output2_shape))
                W_conv2 = tf.get_variable('g_wconv2', [W_size, W_size, output2_shape[-1], int(H_conv1.get_shape()[-1])],
                                          initializer=tf.truncated_normal_initializer(stddev=0.1))
                b_conv2 = tf.get_variable('g_bconv2', [output2_shape[-1]], initializer=tf.constant_initializer(.1))
                H_conv2 = tf.nn.conv2d_transpose(H_conv1, W_conv2, output_shape=output2_shape,
                                                 strides=[1, 2, 2, 1], padding='SAME') + b_conv2
                H_conv2 = tf.contrib.layers.batch_norm(inputs = H_conv2, center=True, scale=True, is_training=True, scope="g_bn2")
                H_conv2 = tf.nn.relu(H_conv2)
                #Dimensions of H_conv2 = batch_size x 6 x 6 x 128

                # Third DeConv Layer
                output3_shape = [batch_size, upscale3, upscale3, g_dim*1]
                print("output3_shape: {}".format(output3_shape))

                W_conv3 = tf.get_variable('g_wconv3', [W_size, W_size, output3_shape[-1], int(H_conv2.get_shape()[-1])],
                                          initializer=tf.truncated_normal_initializer(stddev=0.1))
                b_conv3 = tf.get_variable('g_bconv3', [output3_shape[-1]], initializer=tf.constant_initializer(.1))
                H_conv3 = tf.nn.conv2d_transpose(H_conv2, W_conv3, output_shape=output3_shape,
                                                 strides=[1, 2, 2, 1], padding='SAME') + b_conv3
                H_conv3 = tf.contrib.layers.batch_norm(inputs = H_conv3, center=True, scale=True, is_training=True, scope="g_bn3")
                H_conv3 = tf.nn.relu(H_conv3)
                #Dimensions of H_conv3 = batch_size x 12 x 12 x 64

                # Fourth DeConv Layer
                output4_shape = [batch_size, output_size, output_size, c_dim]
                print("output4_shape: {}".format(output4_shape))

                W_conv4 = tf.get_variable('g_wconv4', [W_size, W_size, output4_shape[-1], int(H_conv3.get_shape()[-1])],
                                          initializer=tf.truncated_normal_initializer(stddev=0.1))
                b_conv4 = tf.get_variable('g_bconv4', [output4_shape[-1]], initializer=tf.constant_initializer(.1))
                H_conv4 = tf.nn.conv2d_transpose(H_conv3, W_conv4, output_shape=output4_shape,
                                                 strides=[1, 2, 2, 1], padding='VALID') + b_conv4
                H_conv4 = tf.nn.tanh(H_conv4)
                #Dimensions of H_conv4 = batch_size x 28 x 28 x 1
                print(H_conv4)


#Just for testing if it works; REMOVE AFTER
if __name__ == "__main__":
    sess = tf.Session()
    z_dimensions = 100
    z_test_placeholder = tf.placeholder(tf.float32, [None, z_dimensions])
    Generator(z=z_test_placeholder, batch_size=1, z_dim=z_dimensions)