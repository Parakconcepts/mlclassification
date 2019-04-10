import os

import keras
import numpy as np
import tensorflow as tf

from keras.models import load_model

from keras.preprocessing import image
from keras.preprocessing.image import ImageDataGenerator

from keras.layers import Conv2D
from keras.layers import MaxPooling2D
from keras.layers import Flatten
from keras.layers import Dense

from keras.models import Sequential
from keras.callbacks import ModelCheckpoint

from .constants import model_dir
from .constants import default_test_folder_path
from .constants import default_train_folder_path

train_datagen = ImageDataGenerator(
    rescale=1./255,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True
)

test_datagen = ImageDataGenerator(rescale=1./255)


def train_model(new_model,train_folder_path,test_folder_path):
    # Check that both train and test folders are present (Catch both orders)
    if os.path.isdir(train_folder_path):

        # test_folder_path must also be a directory
        if os.path.isdir(test_folder_path):
            train(new_model, train_folder=train_folder_path, test_folder=test_folder_path)

        print('\n The provided test folder is not a directory')
        return # You must return  
    #Means train_folder_path is not a directory
    print('\n The provided train folder is not a directory')
    return


def _generator(folder_path =None, is_train_set=True):
    """
    Accepts a training folder path and generate training set from it.

    if a folder is not supplied, defaults to using ./datasets/training_set

    No need to make default dataset folder constant because it's only used here
    """
    if is_train_set:
        if folder_path is None:
            folder_path = default_train_folder_path
        return train_datagen.flow_from_directory(folder_path,target_size=(64, 64),
                                                 batch_size=32,
                                                 class_mode='binary')
    if folder_path is None:
        folder_path = default_test_folder_path
    return test_datagen.flow_from_directory(folder_path,target_size=(64, 64),
                                                 batch_size=32,
                                                 class_mode='binary')


def train(model_name, epochs=100, all_count=10000, train_folder=None, test_folder=None):
    
    #Generate training data set 
    training_set = _generator(train_folder, is_train_set=True)
    #Generate test data set
    test_set = _generator(test_folder, is_train_set=False)

    epoch_steps= all_count/ 32
    model_path = os.path.join(model_dir, model_name)

    print("Training")
    classifier = Sequential()

    # Step 1 - Convolution
    classifier.add(
        Conv2D(32, (3, 3), input_shape=(64, 64, 3), activation='relu'))
    # Step 2 - Pooling
    classifier.add(MaxPooling2D(pool_size=(2, 2)))

    # Adding a second convolutional layer
    classifier.add(Conv2D(32, (3, 3), activation='relu'))
    classifier.add(MaxPooling2D(pool_size=(2, 2)))
    # Step 3 - Flattening
    classifier.add(Flatten())

    # Step 4 - Full connection
    classifier.add(Dense(units=128, activation='relu'))
    classifier.add(Dense(units=1, activation='sigmoid'))
        # checkpoint

    checkpoint = ModelCheckpoint(model_path, monitor='val_acc', verbose=1, save_best_only=True, mode='max')
    callbacks_list = [checkpoint]
    if os.path.isfile(model_path):
        print ("Resumed model's weights from {}".format(model_path))
        # load weights
        classifier.load_weights(model_path)
    # Compiling the CNN
    classifier.compile(
        optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])


    classifier.fit_generator(
                             training_set,
                             steps_per_epoch=epoch_steps,
                             epochs=epochs,
                             verbose=1,
                             validation_data=test_set,
                             validation_steps=2000,
                             callbacks=callbacks_list)
    #Model confidence
    x, y = zip(*(test_set[i] for i in range(len(test_set))))  
    x_test, y_test = np.vstack(x), np.vstack(y)    
    loss, acc = classifier.evaluate(x_test, y_test.ravel(), batch_size=64)
    print("Confidence: " ,round(acc*100),'%')
    #print("Loss: ", loss)
    # training_set.class_indices
    train.label = training_set.class_indices
    train.model = classifier

    
    #save Model with Unique ID
def saveModel():
    labels = train.label.keys()
    labels = str(list(labels))+"_model.h5"
    save = train.model.save(labels)
    return save


def prepImage(testImage):

    test_image = image.load_img(testImage, target_size=(64, 64))
    test_image = image.img_to_array(test_image)
    test_image = np.expand_dims(test_image, axis=0)

    return test_image

def setupTF():

    config = tf.ConfigProto(device_count={'GPU': 1})
    sess = tf.Session(config=config)
    keras.backend.set_session(sess)

    return


