#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  5 10:44:06 2020

@author: joel
"""
from datagen import datagen
import numpy as np
from tqdm import tqdm
import pandas as pd


import tensorflow.keras as keras
from tensorflow.keras.models import Sequential
#from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv3D,InputLayer,Dense,Activation,MaxPool3D,Flatten,BatchNormalization,GlobalAveragePooling3D
from tensorflow.keras.losses import categorical_crossentropy
from tensorflow.keras.metrics import mean_squared_error,binary_accuracy,categorical_crossentropy,categorical_accuracy
from tensorflow.keras.callbacks import ModelCheckpoint,EarlyStopping,TensorBoard
from tensorflow.keras.utils import to_categorical

class Conv3D_model():
    
    def __init__(self):
        self.model_3d=self.model()
        self.cuts = None
        self.images = None
        print(self.model_3d.summary())
    
    # Model with 10 input frames and 1 prediction. 
    def model(self, n=10):
        input_layer=(64,64,n,3)
        kernel_conv1=(5,5,3)
        kernel_conv2=(3,3,3)
        kernel_conv3=(6,6,1)
        kernal_softmax=(1,1,4)

        model = Sequential()
        model.add(InputLayer(input_layer))
        model.add(Conv3D(kernel_size=kernel_conv1, filters=16, strides=(2, 2, 1), padding='valid', activation='relu'))
        model.add(Conv3D(kernel_size=kernel_conv2, filters=24, strides=(2, 2, 1), padding='valid', activation='relu'))
        model.add(Conv3D(kernel_size=kernel_conv2, filters=32, strides=(2, 2, 1), padding='valid', activation='relu'))
        model.add(Conv3D(kernel_size=kernel_conv3, filters=12, strides=(2, 2, 1), padding='valid', activation='relu'))
        model.add(MaxPool3D((1,1,4)))
        model.add(Flatten())
        model.add(Dense(2,activation='softmax'))

        model.compile(optimizer='adam',loss='categorical_crossentropy',metrics=[categorical_crossentropy,categorical_accuracy])

        return(model)
    
    def FCN(self,n=None):
        """
        fully convolutional neural network (doesn't work as intended when scaling up input dimension')
        """
        input_layer=(64,64,n,3)
        kernel_conv1=(5,5,3)
        kernel_conv2=(3,3,3)
        kernel_conv3=(6,6,1)
        kernal_softmax=(1,1,4)
        
        model = Sequential()
        model.add(InputLayer(input_layer))
        model.add(Conv3D(kernel_size=kernel_conv1, filters=16, strides=(2, 2, 1), padding="valid", activation='relu'))
        model.add(Conv3D(kernel_size=kernel_conv2, filters=24, strides=(2, 2, 1), padding="valid", activation='relu'))
        model.add(Conv3D(kernel_size=kernel_conv2, filters=32, strides=(2, 2, 1), padding='valid', activation='relu'))
        model.add(Conv3D(kernel_size=kernel_conv3, filters=12, strides=(2, 2, 1), padding='valid', activation='relu'))
        model.add(MaxPool3D((1,1,4),strides=(1,1,1)))
        model.add(Conv3D(kernel_size=(1,1,1), filters=2, strides=(1, 1, 1),padding='valid', activation='softmax'))
        model.compile(optimizer='adam',loss='categorical_crossentropy',metrics=[categorical_crossentropy,categorical_accuracy])
        model.summary()
        return(model)
    
    def train(self,  img_data, cut, epoch=100, batch_size=32, out_weight='modelWeights.h5'):
        try:
            print("loading Data")
            image_data=np.load(img_data, allow_pickle=True)
            cut=np.load(cut, allow_pickle=True)
            print('#'*50)
            print("data has been loaded")
        
        except:
            print('create training data first')
        
        image_train,image_test=image_data[:int(.8*len(cut))],image_data[int(.8*len(cut)):]
        cut_train,cut_test=cut[:int(.8*len(cut))],cut[int(.8*len(cut)):]
        cut_train, cut_test = to_categorical(cut_train), to_categorical(cut_test)
        self.model_3d.fit(image_train,cut_train, batch_size =batch_size, epochs=epoch , validation_data=(image_test,cut_test))
        self.model_3d.save(out_weight)
        print('training finished')

    def create_dataset(self,video_file,csv_file,name):
        gen=datagen(no_frames=10,video_file=video_file,csv_file=csv_file)
        image_data,cut=[],[]
        for image_64,prediction in tqdm(gen.data_extrac(),total=gen.len):
            image_data.append(image_64.reshape((64, 64, 10, 3)))
            cut.append(prediction)
            
            if len(cut) == 5000:
                try:
                    image_loaded=list(np.load(name+'im_data.npy', allow_pickle=True))
                    cut_loaded=list(np.load(name+'cut.npy', allow_pickle=True))
                    print("data has been loaded")
                    image_loaded.extend(image_data)
                    cut_loaded.extend(cut)
                    image_loaded=np.array(image_loaded)
                    cut_loaded=np.array(cut_loaded)
                    np.save(name+'im_data.npy',image_loaded)
                    np.save(name+'cut.npy',cut_loaded)
                    print('saving data')
                    image_data,cut=[],[]
                    
                except:
                    print("\n saving data")
                    np.save(name+'im_data.npy',image_data)
                    np.save(name+'cut.npy',cut)
                    image_data,cut=[],[]
                    
        image_loaded=list(np.load(name+'im_data.npy', allow_pickle=True))
        cut_loaded=list(np.load(name+'cut.npy', allow_pickle=True))
        print("data has been loaded")
        image_loaded.extend(image_data)
        cut_loaded.extend(cut)
        image_loaded=np.array(image_loaded)
        cut_loaded=np.array(cut_loaded)
        np.save(name+'im_data.npy',image_loaded)
        np.save(name+'cut.npy',cut_loaded)
        print('saving data final')
        
    def predict_shots(self,video_file,csv_file, weights):
        gen=datagen(no_frames=10,video_file=video_file,csv_file=csv_file)
        predict = []
        for image_64,_ in tqdm(gen.data_extrac(),total=gen.len):
            self.model_3d.load_weights(weights)
            img = image_64.reshape((1,64, 64, 10, 3))
            predict.append(np.argmax((self.model_3d.predict(img))))
        return predict