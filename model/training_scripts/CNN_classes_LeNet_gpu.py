# -*- coding: utf-8 -*-
"""
Created on Sun Mar 10 10:55:34 2019

@author: Cheng Lin

Used pytorch tutorial: https://stanford.edu/~shervine/blog/pytorch-how-to-generate-data-parallel
"""

import cv2 as cv
import numpy as np
import torch
from torch.utils.data import Dataset
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image

device = torch.device('cuda')

#function to read in image and normalize it
def get_normalized_image(image_path):
    img = cv.imread(image_path, 0)
    #img = Image.open(file_name).convert('LA')
    #img = np.swapaxes(img, 0,2)
    #img_norm = (img-np.mean(img))/np.std(img)
    
    tensor_img = torch.from_numpy(img_norm).unsqueeze(0)
    
    return tensor_img

class ASLLettersDataset(Dataset):
    def __init__(self, img_paths, labels, img_transform):
        
        self.img_paths = img_paths
        self.labels = labels

        self.colour_jitter = transforms.ColorJitter(brightness=0.3, contrast=0.7, saturation=0.3, hue=0.1)
        self.random_rotate = transforms.RandomRotation(20)
        self.random_crop = transforms.RandomCrop(170)
        self.grayscale = transforms.Grayscale(num_output_channels=1)
        
        self.img_transform = img_transform
        
        
    def __len__(self):
        return len(self.img_paths)
    
    def __getitem__(self, idx):
        path = self.img_paths[idx]
        
        #load data and get label
        X = Image.open(path)
        
        if self.img_transform:
            X = self.colour_jitter(X)
            X = self.random_rotate(X)
            X = self.random_crop(X)
    
            
            X_mask = Image.new("RGB", (200,200))        
            X_mask.paste(X, (15,15))
            X = X_mask
        
        X = self.grayscale(X)
        #convert PIL image to grayscale and then convert to tensor
        X_tensor = transforms.functional.to_tensor(X)
        
        y = self.labels[path]
        
        return X_tensor, y
    
class CNN(nn.Module):
    def __init__(self):
        super().__init__()
        
        self.conv1 = nn.Conv2d(1, 6, kernel_size=5, stride=1, padding=0)
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2, padding=0)
        
        self.conv3 = nn.Conv2d(6, 16, kernel_size=5, stride=1, padding=0)
        self.pool4 = nn.MaxPool2d(kernel_size=2, stride=2, padding=0)
        self.conv5 = nn.Conv2d(16, 120, kernel_size=5, stride=1, padding=0)
        
        self.fc6 = nn.Linear(120*43*43, 84)
        self.fc7 = nn.Linear(84, 26)
        
    def forward(self, x):
        #cast to float
        x = x.float()
        
        #convolutional layer + pooling
        #print('conv 1')
        x = F.relu(self.conv1(x))
        #print(x.shape)
        #print('pool')
        x = self.pool2(x)
        #print(x.shape)
        
        #print('conv 3')
        x=F.relu(self.conv3(x))
        #print(x.shape)
        x = self.pool4(x)
        #print('pool')
        #print(x.shape)
        
        #print('conv 5')
        x=F.relu(self.conv5(x))
        #print(x.shape)
        #x = self.pool(x)
        #print('pool')
        #print(x.shape)
        
        #reshape data for fully connected layer
        #print('view')
        x = x.view(-1, 120*43*43)
        #print(x.shape)
        
        #fully connected layers
        #print('linear')
        x = F.relu(self.fc6(x))
        #print(x.shape)
        x = F.softmax(self.fc7(x), dim=1)
        #print(x.shape)
        
        return x.squeeze()
        