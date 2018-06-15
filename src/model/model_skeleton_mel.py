import tensorflow as tf
import numpy as np

"""Networks construction file.
"""

# class discriminator_regressor(object):


class Discriminator(object):

	# parameters:
	# ksize= The size of the window for each dimension of the input tensor.
	# strides = The stride of the sliding window for each dimension of the input tensor.

	def __init__(self, reuse=False, discr_type="regressor"):
		"""Model initializer regressor discriminator.
		parameters:
		reuse: True if we want to use Model2, False to use Model1
		discr_type: regressor / discriminator (in order to use model2)
		"""
		print("Initializing model")

		self.input_img = tf.placeholder(tf.uint8, [None, None, None], name='input_img')  # dim batch * shape
		# reshape in [batch, height, width, channels] where channels= 1 for tf.nn.conv2d
		self.input_img = tf.reshape(self.input_img, [tf.shape(self.input_img)[0], tf.shape(self.input_img)[1], tf.shape(self.input_img)[2], 1])

		if discr_type == "regressor":
			self.scores = tf.placeholder(tf.float32, [None], name='scores')
		else:
			self.labels = tf.placeholder(tf.int8, [None], name='labels')

		batch_size = tf.shape(self.input_img)[0]

		with tf.device('/gpu:0'):
			# layer 1
			with tf.name_scope("CNN"):
				# TODO TO COMPLETE maybe write a separate function that construct the CNN (see random notes)

				# parameters to investigate:
				filter_height = 5
				filter_width = 5
				out_channels1 = 8
				out_channels2 = 16
				n_hidden_fconnected = 32
				flatten_format = 7

				# that should solve the problem of Model2
				if (reuse):
					tf.get_variable_scope().reuse_variables()

				# First Conv and Pool Layers
				W_conv1 = tf.get_variable('d_wconv1', [filter_height, filter_width, 1, out_channels1], initializer=tf.truncated_normal_initializer(stddev=0.02))
				b_conv1 = tf.get_variable('d_bconv1', [out_channels1], initializer=tf.constant_initializer(0))
				h_conv1 = tf.nn.relu(self.conv2d(self.input_img, W_conv1) + b_conv1)
				h_pool1 = self.avg_pool_2x2(h_conv1)

				# Second Conv and Pool Layers
				W_conv2 = tf.get_variable('d_wconv2', [filter_height, filter_width, out_channels1, out_channels2], initializer=tf.truncated_normal_initializer(stddev=0.02))
				b_conv2 = tf.get_variable('d_bconv2', [out_channels2], initializer=tf.constant_initializer(0))
				h_conv2 = tf.nn.relu(self.conv2d(h_pool1, W_conv2) + b_conv2)
				h_pool2 = self.avg_pool_2x2(h_conv2)


			# fully connected
			with tf.name_scope("fully connected"):

				# not sure if it's necessary (this is not shared between labeled and scored (to change?))
				# h_fc1 = tf.layers.dense(h_fc1, units= n_hidden_fconnected, activation=None)

				# First Fully Connected Layer
				W_fc1 = tf.get_variable('d_wfc1', [flatten_format*flatten_format*out_channels2, n_hidden_fconnected],
										initializer=tf.truncated_normal_initializer(stddev=0.02))
				b_fc1 = tf.get_variable('d_bfc1', [n_hidden_fconnected], initializer=tf.constant_initializer(0)) # or use tf.truncated_normal_initializer(stddev=0.01) ?
				h_pool2_flat = tf.reshape(h_pool2, [-1, flatten_format * flatten_format * out_channels2]) # Not sure about flatten_format
				h_fc1 = tf.nn.relu(tf.matmul(h_pool2_flat, W_fc1) + b_fc1)

				# Not sure we need that....?
				# Second Fully Connected Layer
				W_fc2 = tf.get_variable('d_wfc2', [n_hidden_fconnected, 1],
										initializer=tf.truncated_normal_initializer(stddev=0.02))
				b_fc2 = tf.get_variable('d_bfc2', [1],
										initializer=tf.constant_initializer(0)) # or use tf.truncated_normal_initializer(stddev=0.01) ?
				h_fc2 = tf.matmul(h_fc1, W_fc2) + b_fc2
				# y_ = tf.nn.softmax(h_fc2)

			# final output
			with tf.name_scope("output"):

				if discr_type == "regressor":
					predictions_score = tf.layers.dense(h_fc2, units=1, activation=None, name="score_pred")
				else:
					logits = tf.layers.dense(h_fc2, units=2, activation=None, name="logits")
					predictions_labels = tf.argmax(logits)

			# Compute loss
			with tf.name_scope("loss"):

				if discr_type == "regressor":
					loss_reg = tf.losses.mean_squared_error(labels=self.scores, predictions = predictions_score, name='loss_reg')
				else:
					loss_label = tf.softmax_cross_entropy_with_logits(logits=self.logits, labels=self.labels, name='loss_label')

	# Not used yet
	def save(self, path):
		"""
		Saves the trained model
		:param path: path to the trained model
		"""
		self.model.save(path)
		print("Model saved to {}".format(path))

	def conv2d(self, x, W):
		input_x = tf.cast(x, tf.float32)
		return tf.nn.conv2d(input=input_x, filter=W, strides=[1, 1, 1, 1], padding='SAME')

	def avg_pool_2x2(self, x):
		return tf.nn.avg_pool(x, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')



class Discriminator_label(object):

	def __init__(self, n_hidden):
		"""Model initializer label discriminator.
		"""
		self.input_img = tf.placeholder(dtype, shape, name='input img') #dim batch * shape
		self.labels = tf.placeholder(dtype, shape, name='labels')
		batch_size = tf.shape(self.input)[0]
		with tf.device('/gpu:0'):
			# layer 1
			with tf.name_scope("CNN"):
					# TODO TO COMPLETE maybe write a separate function that construct the CNN (see random notes)
					a = 0
			# fully connected
			with tf.name_scope("fully connected"):
				logits = tf.dense
			# final output
			with tf.name_scope("output"):
				predictions_labels = tf.argmax(logits)
			# Compute loss
			with tf.name_scope("loss"):
				# prediction at time step t should be input word number t+1
				loss_label = tf.softmax_cross_entropy_with_logits(logits=self.logits, labels=self.labels, name='loss_label')


# TODO can also write a model with train first label then regressor reusing the same CNN


if __name__ == "__main__":
	Discriminator()