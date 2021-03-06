import tensorflow as tf


class Generator(tf.keras.Model):
    def __init__(self):
        super(Generator, self).__init__()


        self.encoders = [
            Encoder_Block(64, 4, batchnorm=False, input_shape=(256,256,1)),
            Encoder_Block(128,4),
            Encoder_Block(256,4),
            Encoder_Block(512,4),
            Encoder_Block(512,4),
            Encoder_Block(512,4),
            Encoder_Block(512,4),
            Encoder_Block(512,4), #1x512
        ]

        self.decoders = [
            Decoder_Block(512,4, dropout=True),
            Decoder_Block(512,4, dropout=True),
            Decoder_Block(512,4, dropout=True),
            Decoder_Block(512,4),
            Decoder_Block(256,4),
            Decoder_Block(128,4),
            Decoder_Block(64,4),
            tf.keras.layers.Conv2DTranspose(2, 4, 
                strides=2, 
                padding='same', 
                activation='tanh', 
                kernel_initializer=tf.random_normal_initializer(0., 0.02)
                ) 
        ]
        # the initializer and learning rate parameters are from https://www.tensorflow.org/tutorials/generative/pix2pix

        self.optimizer = tf.keras.optimizers.Adam(2e-4, beta_1=0.5)

    @tf.function
    def call(self, input):
        encoder_outs = []
        for i,layer in enumerate(self.encoders):
            if i == 0:
                encoder_outs.append(layer(input[...,:1]))
            else:
                encoder_outs.append(layer(encoder_outs[-1]))
        
        decoder_out = None
        for i,layer in enumerate(self.decoders):
            if i == 0:
                decoder_out = layer(encoder_outs[-1])
            else:
                corresponding_encoded = encoder_outs[len(self.decoders) - i - 1]
                concat = tf.keras.layers.Concatenate()([decoder_out, corresponding_encoded])
                decoder_out = layer(concat)
        
        
        return decoder_out

    def loss_function(self, fake, d_fake, real, l=100):
        d_loss_fn = tf.keras.losses.BinaryCrossentropy(from_logits=True)
        d_loss = tf.reduce_mean(d_loss_fn(tf.ones_like(d_fake), d_fake))
        mae_loss_fn = tf.keras.losses.MeanAbsoluteError()
        mae_loss = tf.reduce_mean(mae_loss_fn(fake, real))
        return d_loss + mae_loss * l, mae_loss, d_loss

class Encoder_Block(tf.keras.layers.Layer):
    def __init__(self, num_filters, kernel_size=3, strides=2, batchnorm=True, input_shape=None, padding='same'):
        super(Encoder_Block, self).__init__()
        if input_shape is not None: 
            self.conv_layer = tf.keras.layers.Conv2D(
                num_filters, 
                kernel_size, 
                strides=strides, 
                padding=padding, 
                input_shape=input_shape,
                kernel_initializer=tf.random_normal_initializer(0., 0.02)
            )
        else:
            self.conv_layer = tf.keras.layers.Conv2D(
                num_filters, 
                kernel_size, 
                strides=strides, 
                padding=padding,
                kernel_initializer=tf.random_normal_initializer(0., 0.02)
            )
        self.batch_norm = batchnorm
        if batchnorm:
            self.batch_norm = tf.keras.layers.BatchNormalization()
        self.leaky = tf.keras.layers.LeakyReLU()
    
    @tf.function
    def call(self, inputs):
        conv_out = self.conv_layer(inputs)
        if self.batch_norm:
            batch_norm_out = self.batch_norm(conv_out)
        else:
            batch_norm_out = conv_out
        leaky_out = self.leaky(batch_norm_out)

        return leaky_out


class Decoder_Block(tf.keras.layers.Layer):
    def __init__(self, num_filters, kernel_size=3, strides=2, dropout=False):
        super(Decoder_Block, self).__init__()  
        self.dropout = dropout
        
        self.conv_t_layer = tf.keras.layers.Conv2DTranspose(
            num_filters, 
            kernel_size, 
            strides=strides, 
            padding='same',
            kernel_initializer=tf.random_normal_initializer(0., 0.02)
        )

        self.batch_norm = tf.keras.layers.BatchNormalization()
        self.relu = tf.keras.layers.ReLU()

    @tf.function
    def call(self, inputs):
        conv_out = self.conv_t_layer(inputs)
        batch_norm_out = self.batch_norm(conv_out)
        if self.dropout: batch_norm_out = tf.keras.layers.Dropout(0.5)(batch_norm_out)
        relu_out = self.relu(batch_norm_out)

        return relu_out



