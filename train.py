import preprocessing
from model_skeleton import ####


import tensorflow as tf
import numpy as np
import os
import time
import datetime

"""Launch file for training tasks

"""
## PARAMETERS ##

# Data loading parameters
tf.flags.DEFINE_float("dev_sample_percentage", .0001, "Percentage of the training data used for validation")
tf.flags.DEFINE_string("data_file_path", "/data/sentences.train", "Path to the training data")
tf.flags.DEFINE_string("experiment", exp, "experiment type")

# Model parameters
tf.flags.DEFINE_integer("n_hidden", n_hidden, "Size of hidden state")


# Training parameters
tf.flags.DEFINE_integer("batch_size", 64, "Batch Size (default: 64)")
tf.flags.DEFINE_integer("num_epochs", 20, "Number of training epochs (default: 200)")
tf.flags.DEFINE_integer("evaluate_every", 100, "Evaluate model on dev set after this many steps (default: 100)")
tf.flags.DEFINE_integer("checkpoint_every", 100, "Save model after this many steps (default: 100)")
tf.flags.DEFINE_integer("num_checkpoints", 2, "Number of checkpoints to store (default: 5)")

# Tensorflow Parameters
tf.flags.DEFINE_boolean("allow_soft_placement", True, "Allow device soft device placement")
tf.flags.DEFINE_boolean("log_device_placement", False, "Log placement of ops on devices")

# for running on EULER
tf.flags.DEFINE_integer("inter_op_parallelism_threads", 16,
 	"TF nodes that perform blocking operations are enqueued on a pool of inter_op_parallelism_threads available in each process (default 0).")
tf.flags.DEFINE_integer("intra_op_parallelism_threads", 16,
 	"The execution of an individual op (for some op types) can be parallelized on a pool of intra_op_parallelism_threads (default: 0).")

FLAGS = tf.flags.FLAGS

print("\nParameters:")
for attr, value in sorted(FLAGS.__flags.items()):
	print("{}={}".format(attr.upper(), value.value))
print("")

## DATA PREPARATION ##

# Load data
print("Loading and preprocessing training and dev datasets \n")

print("Data loaded")

# Randomly shuffle data
np.random.seed(10)
shuffled_indices = np.random.permutation(len(x))
x_shuffled = x[shuffled_indices]

# Split train/dev sets for validation
dev_sample_index = -1 * int(FLAGS.dev_sample_percentage * float(len(x_shuffled[:,0])))
x_train, x_dev = x_shuffled[:dev_sample_index], x_shuffled[dev_sample_index:]

# Generate training batches
batches = preprocessing.batch_iter(x_train, FLAGS.batch_size, FLAGS.num_epochs) #have to check if the function still works with only one input x


## MODEL AND TRAINING PROCEDURE DEFINITION ##

graph = tf.Graph()
with graph.as_default():
	session_conf = tf.ConfigProto(
		allow_soft_placement=FLAGS.allow_soft_placement,
		log_device_placement=FLAGS.log_device_placement,
		inter_op_parallelism_threads=FLAGS.inter_op_parallelism_threads,
		intra_op_parallelism_threads=FLAGS.intra_op_parallelism_threads
		)
	sess = tf.Session(config=session_conf)
	with sess.as_default():

		# Initialize model
		"""to change
		lstm = LSTM(
			vocab_size=FLAGS.vocab_size, 
			embedding_size=FLAGS.embedding_dim, 
			n_hidden = FLAGS.n_hidden,
			extra_layer = FLAGS.extra_layer
			)"""

		# Define an optimizer with clipping the gradients
		global_step = tf.Variable(0, name="global_step", trainable= False)
		optimizer = tf.train.AdamOptimizer()
		gradient_var_pairs = optimizer.compute_gradients(lstm.loss)
		vars = [x[1] for x in gradient_var_pairs]
		gradients = [x[0] for x in gradient_var_pairs]
		clipped, _ = tf.clip_by_global_norm(gradients, 5)
		train_op = optimizer.apply_gradients(zip(clipped, vars), global_step = global_step)
		
		# Output directory for models and summaries
		timestamp = str(int(time.time()))
		out_dir = os.path.abspath(os.path.join(os.path.curdir, "runs", timestamp))
		print("Writing to {}\n".format(out_dir))

		# Loss summaries
		loss_summary = #tf.summary.scalar("loss", lstm.loss)

		# Train summaries
		train_summary_op = tf.summary.merge([loss_summary])
		train_summary_dir = os.path.join(out_dir, "summaries", "train")
		train_summary_writer = tf.summary.FileWriter(train_summary_dir, sess.graph)

		# Dev summaries
		dev_summary_op = tf.summary.merge([loss_summary])
		dev_summary_dir = os.path.join(out_dir, "summaries", "dev")
		dev_summary_writer = tf.summary.FileWriter(dev_summary_dir, sess.graph)

		# Checkpoint directory (Tensorflow assumes this directory already exists so we need to create it)
		checkpoint_dir = os.path.abspath(os.path.join(out_dir, "checkpoints"))
		checkpoint_prefix = os.path.join(checkpoint_dir, "model")
		if not os.path.exists(checkpoint_dir):
			os.makedirs(checkpoint_dir)
		saver = tf.train.Saver(tf.global_variables(), max_to_keep=FLAGS.num_checkpoints)

		# Initialize all variables
		sess.run(tf.global_variables_initializer())
		sess.graph.finalize()

		# Define training and dev steps (batch)
		def train_step(x_batch):
			"""
			A single training step
			"""
			feed_dict = {
				#lstm.input: x_batch
            	}
			_, step, summaries, loss = sess.run(
				[train_op, global_step, train_summary_op, lstm.loss],
				feed_dict)
			time_str = datetime.datetime.now().isoformat()
			print("{}: step {}, loss {:g}".format(time_str, step, loss))
			train_summary_writer.add_summary(summaries, step)

		def dev_step(x_batch, writer=None):
			"""
			Evaluates model on a dev set
			"""
			feed_dict = {
				#lstm.input: x_batch
				}
			step, summaries, loss = sess.run(
				[global_step, dev_summary_op, lstm.loss],
				feed_dict)
			time_str = datetime.datetime.now().isoformat()
			print("{}: step {}, loss {:g}".format(time_str, step, loss))
			if writer:
				writer.add_summary(summaries, step)

		## TRAINING LOOP ##
		for batch in batches:
			train_step(batch)
			current_step = tf.train.global_step(sess, global_step)
			if current_step % FLAGS.evaluate_every == 0:
				print("\nEvaluation:")
				dev_step(x_dev, writer=dev_summary_writer)
				print("")
			if current_step % FLAGS.checkpoint_every == 0:
				path = saver.save(sess, checkpoint_prefix, global_step=current_step)
				print("Saved model checkpoint to {}\n".format(path))