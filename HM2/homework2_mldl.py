# -*- coding: utf-8 -*-
"""Homework2-MLDL.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1g1nvQ1GYWiJhmNJe2_zLaUl335Ezwcy9

**Install requirements**
"""

if(False):
  #!pip3 install 'torch==1.3.1'
  !pip3 install 'torch==1.4.0'
  !pip3 install 'torchvision==0.5.0'
  !pip3 install 'Pillow-SIMD'
  !pip3 install 'tqdm'

"""**Import libraries**"""

import os
import logging

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Subset, DataLoader, random_split
from torch.backends import cudnn

import torchvision
from torchvision import transforms
from torchvision.models import alexnet

from PIL import Image
from tqdm import tqdm

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from copy import deepcopy
import seaborn as sns
import cv2

"""**Set Arguments**"""

DEVICE = 'cuda' # 'cuda' or 'cpu'

NUM_CLASSES = 101 # 101 + 1: There is an extra Background class that should be removed 

BATCH_SIZE = 256     # Higher batch sizes allows for larger learning rates. An empirical heuristic suggests that, when changing
                     # the batch size, learning rate should change by the same factor to have comparable results

LR = 1e-3            # The initial Learning Rate
MOMENTUM = 0.9       # Hyperparameter for SGD, keep this at 0.9 when using SGD
WEIGHT_DECAY = 5e-5  # Regularization, you can keep this at the default

NUM_EPOCHS = 30      # Total number of training epochs (iterations over dataset)
STEP_SIZE = 20       # How many epochs before decreasing learning rate (if using a step-down policy)
GAMMA = 0.1          # Multiplicative factor for learning rate step-down

LOG_FREQUENCY = 10
VAL_FREQUENCY = 2

"""**Define Data Preprocessing**"""

# Define transforms for training phase
train_transform = transforms.Compose([transforms.Resize(256),      # Resizes short size of the PIL image to 256
                                      transforms.CenterCrop(224),  # Crops a central square patch of the image
                                                                   # 224 because torchvision's AlexNet needs a 224x224 input!
                                                                   # Remember this when applying different transformations, otherwise you get an error
                                      transforms.ToTensor(), # Turn PIL Image to torch.Tensor
                                      transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)) # Normalizes tensor with mean and standard deviation
])
# Define transforms for the evaluation phase
eval_transform = transforms.Compose([transforms.Resize(256),
                                      transforms.CenterCrop(224),
                                      transforms.ToTensor(),
                                      transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))                                    
])

"""**Prepare Dataset**"""

# Clone github repository with data
if not os.path.isdir('./Caltech101'):
  !git clone https://github.com/MachineLearning2020/Homework2-Caltech101.git
  !mv 'Homework2-Caltech101' 'Caltech101'

#####     REMBER TO CHANGE caltech_dataset.py FILE INSIDE Caltech101 FOLDER                                   #####
#####     WITH THE CORRISPONDENT FILE INSIDE THE SUBMITTED ZIP FILE                                           #####
#####     IT MAY BE NEEDED ALSO TO RESTART THE KERNEL (RUNTIME -> RESTART RUNTIME) AND RUN AGAIN THE CELLS    #####
from Caltech101.caltech_dataset import Caltech
DATA_DIR = 'Caltech101/101_ObjectCategories'
def PrepareDataset():
  # Prepare Pytorch train/test Datasets
  train_dataset_Caltech = Caltech(DATA_DIR, split='train',  transform=train_transform)

  #Split ad-hoc inside Caltech class
  #train_indexes = []
  #val_indexes = []

  train_dataset = deepcopy(train_dataset_Caltech)
  train_dataset.SetTrain()

  val_dataset = train_dataset_Caltech
  val_dataset.SetVal(eval_transform)

  test_dataset = Caltech(DATA_DIR, split='test', transform=eval_transform)
  test_dataset.SetTest()


  # Check dataset sizes
  print('Train Dataset: {}'.format(len(train_dataset.samples_train)))
  print('Valid Dataset: {}'.format(len(val_dataset.samples_val)))
  print('Train/Valid Dataset Proportion: {} (Required: {})'.format( len(train_dataset.samples_train)/len(val_dataset.samples_val), int(1/1) ) )
  print('Test Dataset: {}'.format(len(test_dataset.samples)))

  return train_dataset, val_dataset, test_dataset
  
train_dataset, val_dataset, test_dataset = PrepareDataset()

"""CLASS DISTRIBUTION"""

#Remove/Change if statement to plot the class distribution 
if(False):
  classes_size = {}
  elements = 0
  targets = train_dataset.targets + val_dataset.targets + test_dataset.targets
  class_to_idx = train_dataset.class_to_idx 
  for i in targets:
    class_name = next((name for name, index in class_to_idx.items() if index == i), None)
    elements += 1
    if class_name not in classes_size:
      classes_size[class_name] = 0
    else:
      classes_size[class_name] = classes_size[class_name] + 1

  sorted_classes = dict(sorted(classes_size.items(), key=lambda x: x[1],reverse=True))
  fig, ax = plt.subplots(figsize=(20,10))
  x_pos = np.arange(len(train_dataset.classes))
  ax.set_xticks(x_pos)
  ax.set_xticklabels(list(sorted_classes.keys()),rotation='vertical', fontsize=13)

  plt.axhline(np.mean(list(classes_size.values())), c='r' )

  l , r = plt.xlim()
  value = 0.7
  plt.xlim( l-value, r+value )

  plt.bar(x_pos,sorted_classes.values())
  plt.title('Class Distribution')
  plt.xlabel('Class Name')
  plt.ylabel('# Occurrences')
  plt.show()

  print('Total Images: {}'.format(elements))
  print('Max # Images in a class: {}'.format(max(classes_size.values())))
  print('Min # Images in a class: {}'.format(min(classes_size.values())))
  print('Mean Images for classes: {:.3f}'.format(np.mean(list(classes_size.values()))))
  print('STD Images for classes: {:.3f}'.format(np.std(list(classes_size.values()))))

"""**Prepare Dataloaders**"""

def PrepareDataLoaders():
  # Dataloaders iterate over pytorch datasets and transparently provide useful functions (e.g. parallelization and shuffling)
  train_dataloader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=4, drop_last=True)
  val_dataloader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=4)

  test_dataloader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=4)

  return train_dataloader, val_dataloader, test_dataloader
train_dataloader, val_dataloader, test_dataloader = PrepareDataLoaders()

def NumParamsToTrain(net):
  # Find total parameters and trainable parameters
  total_params = sum(p.numel() for p in net.parameters())
  print(f'{total_params:,} total parameters.')
  total_trainable_params = sum(p.numel() for p in net.parameters() if p.requires_grad)
  print(f'{total_trainable_params:,} training parameters.')
  diff = total_params-total_trainable_params
  print(f'{diff:,} frozen parameters.')
  ratio = total_trainable_params/total_params
  print(f'{ratio:.2f} ratio training/total.')

"""**Prepare Network**"""

net = alexnet() # Loading AlexNet model

# AlexNet has 1000 output neurons, corresponding to the 1000 ImageNet's classes
# We need 101 outputs for Caltech-101
net.classifier[6] = nn.Linear(4096, NUM_CLASSES) # nn.Linear in pytorch is a fully connected layer
                                                # The convolutional layer is nn.Conv2d

# We just changed the last layer of AlexNet with a new fully connected layer with 101 outputs
# It is strongly suggested to study torchvision.models.alexnet source code

"""**Prepare Training**"""

# Define loss function
criterion = nn.CrossEntropyLoss() # for classification, we use Cross Entropy

# Choose parameters to optimize
# To access a different set of parameters, you have to access submodules of AlexNet
# (nn.Module objects, like AlexNet, implement the Composite Pattern)
# e.g.: parameters of the fully connected layers: net.classifier.parameters()
# e.g.: parameters of the convolutional layers: look at alexnet's source code ;) 
parameters_to_optimize = net.parameters() # In this case we optimize over all the parameters of AlexNet

# Define optimizer
# An optimizer updates the weights based on loss
# We use SGD with momentum
optimizer = optim.SGD(parameters_to_optimize, lr=LR, momentum=MOMENTUM, weight_decay=WEIGHT_DECAY)

# Define scheduler
# A scheduler dynamically changes learning rate
# The most common schedule is the step(-down), which multiplies learning rate by gamma every STEP_SIZE epochs
scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=STEP_SIZE, gamma=GAMMA)

"""**Validation**"""

def Validation(model, dataloader):
  model = model.to(DEVICE) # this will bring the network to GPU if DEVICE is cuda
  model.train(False) # Set Network to evaluation mode

  running_corrects = 0
  for images, labels in (dataloader):#tqdm
    images = images.to(DEVICE)
    labels = labels.to(DEVICE)

    # Forward Pass
    outputs = model(images)

    loss = criterion(outputs, labels)
    max = 6
    loss_value = loss.item() if loss.item()<max else max

    # Get predictions
    _, preds = torch.max(outputs.data, 1)
    
    # Update Corrects
    running_corrects += torch.sum(preds == labels.data).data.item()

  # Calculate Accuracy
  accuracy = running_corrects / float(len(dataloader.dataset))

  print('*** Validation Accuracy: {} ***'.format(accuracy))

  return (accuracy, loss_value)

"""**Train**"""

PATH_MODELS = 'Models/'
if not os.path.isdir('./'+PATH_MODELS):
  os.mkdir('./'+PATH_MODELS)
def Training(net, meta =''):
  # By default, everything is loaded to cpu
  model = net.to(DEVICE) # this will bring the network to GPU if DEVICE is cuda

  cudnn.benchmark # Calling this optimizes runtime

  current_step = 0
  current_epoch = 0
  loss_value = 0
  # Start iterating over the epochs

  #Test and Validation Loss and Accuracy
  train = []
  valid = []
  best_acc = -9999
  for epoch in range(NUM_EPOCHS):
    print('Starting epoch {}/{}, LR = {}'.format(epoch+1, NUM_EPOCHS, scheduler.get_lr()))

    running_corrects = 0
    # Iterate over the dataset
    for images, labels in train_dataloader:
      #net.train(True)
      # Bring data over the device of choice
      images = images.to(DEVICE)
      labels = labels.to(DEVICE)

      net.train() # Sets module in training mode

      # PyTorch, by default, accumulates gradients after each backward pass
      # We need to manually set the gradients to zero before starting a new iteration
      optimizer.zero_grad() # Zero-ing the gradients

      # Forward pass to the network
      outputs = net(images)

      # Compute loss based on output and ground truth
      loss = criterion(outputs, labels)
      max = 6
      loss_value = loss.item() if loss.item()<max else max

      # Get predictions
      _, preds = torch.max(outputs.data, 1)
      
      # Update Corrects
      running_corrects += torch.sum(preds == labels.data).data.item()

      # Log loss
      if current_step % LOG_FREQUENCY == 0:
        print('Step {}, Loss {}'.format( current_step, loss_value ))

      # Compute gradients for each layer and update weights
      loss.backward()  # backward pass: computes gradients
      optimizer.step() # update weights based on accumulated gradients

      current_step += 1

    # Calculate Accuracy
    accuracy = running_corrects / float(len(train_dataset))

    #Store training values each epoch
    train.append( (accuracy, loss_value) )

    
    #Evaluate the model each epoch and store the values
    acc_val = 0
    loss_val = 0
    if current_epoch % VAL_FREQUENCY == 0:
      acc_val, loss_val = Validation(net,val_dataloader)
      valid.append( (acc_val , loss_val) )

      #Get model with best accuracy
      if(best_acc < acc_val):
        best_acc = acc_val
        torch.save(net, PATH_MODELS+meta+'.pth')

    current_epoch += 1

    # Step the scheduler
    scheduler.step()

  return train, valid, best_acc

NumParamsToTrain(net)

if(False):
  #Train from scratch
  meta = 'scratch'
  test, valid, best_acc = Training(net,meta)

  print()
  best_net_scratch = torch.load(PATH_MODELS+meta+'.pth')
  print('Best accuracy on Validation set {}'.format(best_acc))
  _ = Validation(best_net_scratch, test_dataloader)

def PlotAccuracyLoss(train, valid, meta=''):
  acc_train = np.array(train)[:,0]
  acc_valid = np.array(valid)[:,0]

  loss_train = np.array(train)[:,1]
  loss_valid = np.array(valid)[:,1]

  epoch_train = [i for i in range(len(acc_train))]
  epoch_val = [i*VAL_FREQUENCY for i in range(len(acc_valid))]

  fig, ax = plt.subplots(1,2,figsize=(13,7))
  size = 10

  color_train = '#ff0000'
  color_val = '#00ff00'

  ax[0].plot(epoch_train,loss_train,color=color_train)
  ax[0].scatter(epoch_train,loss_train,marker='s',s=size,color=color_train)
  ax[0].plot(epoch_val,loss_valid,color=color_val)
  ax[0].scatter(epoch_val,loss_valid,marker='s',s=size,color=color_val)
  ax[0].set_title('Loss Graph')
  ax[0].set_ylabel('Loss')
  ax[0].set_xlabel('Epoch')

  ax[1].plot(epoch_train,acc_train,color=color_train)
  ax[1].scatter(epoch_train,acc_train,marker='s',s=size,color=color_train)
  ax[1].plot(epoch_val,acc_valid,color=color_val)
  ax[1].scatter(epoch_val,acc_valid,marker='s',s=size,color=color_val)
  ax[1].set_title('Accuracy Graph')
  ax[1].set_ylabel('Accuracy')
  ax[1].set_xlabel('Epoch')

  fig.suptitle(meta)
  plt.legend(["Train", "Validation"])

  fig.tight_layout(rect=[0, 0.03, 1, 0.95])
  plt.show()

  print('Min Loss: Train: {:.6f}, Val: {:.6f}'.format( min(loss_train), min(loss_valid) ))
  print('Max Accuracy: Train: {:.6f}, Val: {:.6f}'.format( max(acc_train), max(acc_valid) ))

if(False):
  meta = 'Training from Scratch: LR= {} and Optimazer= SGD'.format(LR)
  PlotAccuracyLoss(test,valid, meta)

"""Training using different parameters"""

NUM_EPOCHS = 25
  lr_values = [0.01, 0.001, 0.00001]
  optimazers = ['Adam','RMSprop','SGD']

if(False):
  
  scores_scratch = {}
  for lr in lr_values:
    for op in optimazers:

      meta = 'Training with LR = {} and Optimazer = {}'.format(lr,op)
      print('---  {}  ---'.format(meta))

      net_scratch = alexnet()
      net_scratch.classifier[6] = nn.Linear(4096, NUM_CLASSES) 
      criterion = nn.CrossEntropyLoss()

      parameters_to_optimize = net_scratch.parameters()
      if(op == 'Adam'):
        optimizer = optim.Adam(parameters_to_optimize, lr=lr, weight_decay=WEIGHT_DECAY)
      elif(op == 'RMSprop'):
        optimizer = optim.RMSprop(parameters_to_optimize, lr=lr, momentum=MOMENTUM, weight_decay=WEIGHT_DECAY)
      else:
        optimizer = optim.SGD(parameters_to_optimize, lr=lr, momentum=MOMENTUM, weight_decay=WEIGHT_DECAY)

      scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=STEP_SIZE, gamma=GAMMA)

      meta_t = 'scratch_'+str(lr)+'_'+op
      test, valid, best_acc = Training(net_scratch,meta_t)
      PlotAccuracyLoss(test,valid,meta=meta)

      best_net = torch.load(PATH_MODELS+meta_t+'.pth')
      scores_scratch[(lr,op)] = (test,valid, best_acc)

      print('---  --- ---  ---')
      print()

def GetMaxAcc(scores,printAll=False):
  values = dict()
  for k,v in scores.items():
    if(printAll):
      print(k)

    count = 0
    values[k] = []
    train = (0,0)
    val = (0,0)
    for i in v:
      if(count==0):
        train = ( np.min(np.array(i)[:,1]), np.max(np.array(i)[:,0]) )
        if(printAll):
          #print('Train: Min Loss {}'.format(train[0]))
          print('Train: Max Acc {}'.format(train[1]))
      elif(count==1):
        val = ( np.min(np.array(i)[:,1]), np.max(np.array(i)[:,0]) )
        if(printAll):
          print('Val: Min Loss {}'.format(val[0]))
          print('Val: Max Acc {}'.format(val[1]))
      count += 1
    values[k].append(train)
    values[k].append(val)
    if(printAll):
      print('---  ----  ----')
  return values
  
def SketchHeatMap(scores,trainAcc=False):
  score = GetMaxAcc(scores)

  keys = list(score.keys())
  x = sorted(set(i[0] for i in keys),reverse=True)
  y = sorted(set(i[1] for i in keys))

  meta = ''
  if (trainAcc):
    index = 0
    meta = 'Training'
  else: 
    index = 1
    meta = 'Validation'

  values = []
  for v in list(score.values()):
    count = 0
    for i in v:
      if(count==index):
        values.append(i[1]) 
      count += 1

  v = np.reshape(values,(3,3))

  pd_scores = pd.DataFrame(v, index=x, columns=y)
  sns.heatmap(pd_scores, vmin=0, vmax=1, linewidths=.1, annot=True,xticklabels='auto', yticklabels='auto')
  plt.xlabel("Optimizer")
  plt.ylabel("Learning Rate")
  plt.title('HeatMap {} Accuracy'.format(meta))
  plt.show()

if(False):
  SketchHeatMap(scores_scratch,True)
  SketchHeatMap(scores_scratch)

if(False):
  lr_best = 0.001
  op_best = 'Adam'
  meta_t = 'scratch_'+str(lr_best)+'_'+op_best
  best_net_scratch = torch.load(PATH_MODELS+meta_t+'.pth')
  print('Best accuracy on Validation set {}'.format(scores_scratch[lr_best,op_best][2]))
  _ = Validation(best_net_scratch, test_dataloader)

"""Pre-Trainined net"""

train_transform = transforms.Compose([transforms.Resize(256),      # Resizes short size of the PIL image to 256
                                      transforms.CenterCrop(224),  # Crops a central square patch of the image
                                                                   # 224 because torchvision's AlexNet needs a 224x224 input!
                                                                   # Remember this when applying different transformations, otherwise you get an error
                                      transforms.ToTensor(), # Turn PIL Image to torch.Tensor
                                      transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)) # Normalizes tensor with mean and standard deviation
])
# Define transforms for the evaluation phase
eval_transform = transforms.Compose([transforms.Resize(256),
                                      transforms.CenterCrop(224),
                                      transforms.ToTensor(),
                                      transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))                                    
])

train_dataset, val_dataset, test_dataset = PrepareDataset()
train_dataloader, val_dataloader, test_dataloader = PrepareDataLoaders()

if(False):

  scores = {}
  for lr in lr_values:
    for op in optimazers:

      meta = 'Training with LR = {} and Optimazer = {}'.format(lr,op)
      print('---  {}  ---'.format(meta))

      net = alexnet(pretrained=True)
      net.classifier[6] = nn.Linear(4096, NUM_CLASSES) 
      criterion = nn.CrossEntropyLoss()

      parameters_to_optimize = net.parameters()
      if(op == 'Adam'):
        optimizer = optim.Adam(parameters_to_optimize, lr=lr, weight_decay=WEIGHT_DECAY)
      elif(op == 'RMSprop'):
        optimizer = optim.RMSprop(parameters_to_optimize, lr=lr, momentum=MOMENTUM, weight_decay=WEIGHT_DECAY)
      else:
        optimizer = optim.SGD(parameters_to_optimize, lr=lr, momentum=MOMENTUM, weight_decay=WEIGHT_DECAY)

      scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=STEP_SIZE, gamma=GAMMA)

      meta_t = 'pre_'+str(lr)+'_'+op
      test, valid, best_acc = Training(net,meta_t)
      PlotAccuracyLoss(test,valid,meta=meta)

      best_net = torch.load(PATH_MODELS+meta_t+'.pth')
      scores[(lr,op)] = (test,valid, best_acc)

      print('---  --- ---  ---')
      print()

if(False):
  SketchHeatMap(scores,True)
  SketchHeatMap(scores)

#Update NUM_EPOCHS since RMSprop seems to converge before 15/20 epochs
NUM_EPOCHS = 25
best_lr = 0.00001
best_opti = 'RMSprop'

#Test the model on the test dataset using best parameters found
if(False):
  meta_t = 'pre_'+str(best_lr)+'_'+best_opti
  best_net = torch.load(PATH_MODELS+meta_t+'.pth')
  print('Best accuracy on Validation set {}'.format(scores[best_lr,best_opti][2]))
  _ = Validation(best_net, test_dataloader)

"""Pre-Trainined net (Fixed CNN)"""

def FreezeNetwork(net, freeze=0):
  if(freeze!=0 and freeze!= 2):
    print('ERROR INPUT!! Received freeze = {} ### Legend: 0 -> freeze CNN, 2 -> freeze FC ###'.format(freeze))
  else:
    #Set the training for all layers to False
    #freeze: 0 -> freeze FC, 2 -> freeze CNN
    count = 0
    for child in net.children():
      if(count==freeze):#count==freeze
        print('Freezing: {}. ### Legend: 0 -> freeze CNN, 2 -> freeze FC ###'.format(freeze))
        for param in child.parameters():
              param.requires_grad = False
        exit
      count += 1
  #Print anyway the number of parameters
  NumParamsToTrain(net)
  return net

if(False):
  net = alexnet(pretrained=True)

  net.classifier[6] = nn.Linear(4096, NUM_CLASSES) 

  net = FreezeNetwork(net,2)

  criterion = nn.CrossEntropyLoss()

  parameters_to_optimize = net.parameters()
  optimizer = optim.RMSprop(parameters_to_optimize, lr=best_lr, momentum=MOMENTUM, weight_decay=WEIGHT_DECAY)
  scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=STEP_SIZE, gamma=GAMMA)

  print()
  meta_t = 'fixcnn_'+str(best_lr)+'_'+best_opti
  test, valid, best_acc = Training(net,meta_t)

  print()
  meta = 'Fixed CNN wirh LR = {} and Optimizer = {}'.format(best_lr, best_opti)
  PlotAccuracyLoss(test,valid,meta=meta)

  print()
  best_net = torch.load(PATH_MODELS+meta_t+'.pth')
  print('Best accuracy on Validation set {}'.format(best_acc))
  _ = Validation(best_net, test_dataloader)

"""Pre-Trainined net (Fixed FC Layer)"""

if(False):
  net = alexnet(pretrained=True) # Loading AlexNet model

  net.classifier[6] = nn.Linear(4096, NUM_CLASSES) 

  net = FreezeNetwork(net,0)

  criterion = nn.CrossEntropyLoss()

  parameters_to_optimize = net.parameters()
  optimizer = optim.RMSprop(parameters_to_optimize, lr=best_lr, momentum=MOMENTUM, weight_decay=WEIGHT_DECAY)
  scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=STEP_SIZE, gamma=GAMMA)

  print()
  meta_t = 'fixfc_'+str(best_lr)+'_'+best_opti
  test, valid, best_acc = Training(net,meta_t)

  print()
  meta = 'Fixed FCs wirh LR = {} and Optimizer = {}'.format(best_lr, best_opti)
  PlotAccuracyLoss(test,valid,meta=meta)

  print()
  best_net = torch.load(PATH_MODELS+meta_t+'.pth')
  print('Best accuracy on Validation set {}'.format(best_acc))
  _ = Validation(best_net, test_dataloader)

"""Augmented Dataset"""

def TrainingAug(net, meta =''):
  showImage=True
  # By default, everything is loaded to cpu
  model = net.to(DEVICE) # this will bring the network to GPU if DEVICE is cuda

  cudnn.benchmark # Calling this optimizes runtime

  current_step = 0
  current_epoch = 0
  loss_value = 0
  # Start iterating over the epochs

  #Test and Validation Loss and Accuracy
  train = []
  valid = []
  best_acc = -9999
  for epoch in range(NUM_EPOCHS):
    print('Starting epoch {}/{}, LR = {}'.format(epoch+1, NUM_EPOCHS, scheduler.get_lr()))

    running_corrects = 0
    # Iterate over the dataset
    for images, labels in train_dataloader:
      #net.train(True)
      # Bring data over the device of choice
      images = images.to(DEVICE)
      labels = labels.to(DEVICE)

      if(showImage):
        invTrans = transforms.Compose([ transforms.Normalize(mean = [ 0., 0., 0. ],
                                                     std = [ 1/0.229, 1/0.224, 1/0.225 ]),
                                transforms.Normalize(mean = [ -0.485, -0.456, -0.406 ],
                                                     std = [ 1., 1., 1. ]),
                               ])

        inv_tensor_0 = invTrans(images[0])
        plt.imshow(np.transpose(inv_tensor_0.cpu().detach().numpy(), (1, 2, 0)))
        plt.show()
        inv_tensor_5 = invTrans(images[5])
        plt.imshow(np.transpose(inv_tensor_5.cpu().detach().numpy(), (1, 2, 0)))
        plt.show()
        inv_tensor_10 = invTrans(images[10])
        plt.imshow(np.transpose(inv_tensor_10.cpu().detach().numpy(), (1, 2, 0)))
        plt.show()
        inv_tensor_15 = invTrans(images[15])
        plt.imshow(np.transpose(inv_tensor_15.cpu().detach().numpy(), (1, 2, 0)))
        plt.show()
        showImage = False

      net.train() # Sets module in training mode

      # PyTorch, by default, accumulates gradients after each backward pass
      # We need to manually set the gradients to zero before starting a new iteration
      optimizer.zero_grad() # Zero-ing the gradients

      # Forward pass to the network
      outputs = net(images)

      # Compute loss based on output and ground truth
      loss = criterion(outputs, labels)
      max = 6
      loss_value = loss.item() if loss.item()<max else max

      # Get predictions
      _, preds = torch.max(outputs.data, 1)
      
      # Update Corrects
      running_corrects += torch.sum(preds == labels.data).data.item()

      # Log loss
      if current_step % LOG_FREQUENCY == 0:
        print('Step {}, Loss {}'.format( current_step, loss_value ))

      # Compute gradients for each layer and update weights
      loss.backward()  # backward pass: computes gradients
      optimizer.step() # update weights based on accumulated gradients

      current_step += 1

    # Calculate Accuracy
    accuracy = running_corrects / float(len(train_dataset))

    #Store training values each epoch
    train.append( (accuracy, loss_value) )

    
    #Evaluate the model each epoch and store the values
    acc_val = 0
    loss_val = 0
    if current_epoch % VAL_FREQUENCY == 0:
      acc_val, loss_val = Validation(net,val_dataloader)
      valid.append( (acc_val , loss_val) )

      #Get model with best accuracy
      if(best_acc < acc_val):
        best_acc = acc_val
        torch.save(net, PATH_MODELS+meta+'.pth')

    current_epoch += 1

    # Step the scheduler
    scheduler.step()

  return train, valid, best_acc

if(False):
  '''in any epoch the dataloader will apply a fresh set of random operations “on the fly”.
  So instead of showing the exact same items at every epoch,
  you are showing a variant that has been changed in a different way.
  So after three epochs, you would have seen three random variants of each item in a dataset.'''

  # Define transforms for training phase
  train_transformations = []
  train_transform_1 = transforms.Compose([transforms.RandomHorizontalFlip(1),
                                        transforms.Resize(256),      
                                        transforms.CenterCrop(224),                         
                                                                    
                                        transforms.ToTensor(),
                                        transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))
  ])
  train_transformations.append( ('Horizontal Flip',train_transform_1) )

  angle = 90
  train_transform_2 = transforms.Compose([transforms.RandomRotation([-angle,angle]),
                                        transforms.Resize(256),      
                                        transforms.CenterCrop(224),                         
                                                                    
                                        transforms.ToTensor(),
                                        transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))
  ])
  train_transformations.append( ('Rotation',train_transform_2) )

  train_transform_3 = transforms.Compose([transforms.RandomVerticalFlip(1),
                                        transforms.Resize(256),      
                                        transforms.CenterCrop(224),                         
                                                                    
                                        transforms.ToTensor(),
                                        transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))
  ])
  train_transformations.append( ('Vertical Flip',train_transform_3) )

  # Define transforms for the evaluation phase
  eval_transform = transforms.Compose([transforms.Resize(256),
                                        transforms.CenterCrop(224),
                                        transforms.ToTensor(),
                                        transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))                                    
  ])

  for t in range(len(train_transformations)):
    print('Augmentation with transformation: {}'.format(train_transformations[t][0]))

    train_transform = train_transformations[t][1]
    train_dataset, val_dataset, test_dataset = PrepareDataset()
    train_dataloader, val_dataloader, test_dataloader = PrepareDataLoaders()

    net = alexnet(pretrained=True) # Loading AlexNet model

    net.classifier[6] = nn.Linear(4096, NUM_CLASSES) 

    #net = FreezeNetwork(net,0)

    criterion = nn.CrossEntropyLoss()

    parameters_to_optimize = net.parameters()
    optimizer = optim.RMSprop(parameters_to_optimize, lr=best_lr, momentum=MOMENTUM, weight_decay=WEIGHT_DECAY)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=STEP_SIZE, gamma=GAMMA)

    print()
    meta_t = 'augm'+str(t)
    test, valid, best_acc = TrainingAug(net,meta_t)

    print()
    meta = 'Augmentation with Transformation: {}'.format(train_transformations[t][0])
    PlotAccuracyLoss(test,valid,meta=meta)

    print()
    best_net = torch.load(PATH_MODELS+meta_t+'.pth')
    print('Best accuracy on Validation set {}'.format(best_acc))
    _ = Validation(best_net, test_dataloader)
    print()

"""Beyond AlexNet"""

train_transform = transforms.Compose([transforms.Resize(256),      
                                      transforms.CenterCrop(224),                         
                                                                   
                                      transforms.ToTensor(),
                                      transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))
])
# Define transforms for the evaluation phase
eval_transform = transforms.Compose([transforms.Resize(256),
                                      transforms.CenterCrop(224),
                                      transforms.ToTensor(),
                                      transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))                                    
])

train_dataset, val_dataset, test_dataset = PrepareDataset()

"""VGG16"""

from torchvision.models import vgg16
net = vgg16(pretrained=True)


#Print the number of Weights
#net = FreezeNetwork(net,1)

for child in net.children():
  for param in child.parameters():
    param.requires_grad = False
    
net.classifier[6] = nn.Sequential(
                      nn.Linear(4096, 2024), 
                      nn.ReLU(), 
                      nn.Dropout(0.4),
                      nn.Linear(2024, NUM_CLASSES),                   
                      nn.LogSoftmax(dim=1))

NumParamsToTrain(net)

criterion = nn.CrossEntropyLoss()

BATCH_SIZE = 256
factor = 8
BATCH_SIZE = int(BATCH_SIZE / factor)
LR = LR / factor

train_dataloader, val_dataloader, test_dataloader = PrepareDataLoaders()

parameters_to_optimize = net.parameters()
optimizer = optim.SGD(parameters_to_optimize, lr=LR, momentum=MOMENTUM, weight_decay=WEIGHT_DECAY)
scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=STEP_SIZE, gamma=GAMMA)

print()
meta_t = 'vgg'+str(LR)+'_'+'SGD'
test, valid, best_acc = Training(net,meta_t)

print()
meta = 'VGG16 wirh LR = {} and Optimizer = {}'.format(LR, 'SGD')
PlotAccuracyLoss(test,valid,meta=meta)


print()
best_net = torch.load(PATH_MODELS+meta_t+'.pth')
print('Best accuracy on Validation set {}'.format(best_acc))
_ = Validation(best_net, test_dataloader)

"""RESNET18"""

from torchvision.models import resnet18
from collections import OrderedDict

net = resnet18(pretrained=True)

#Add FC Layer
fc = nn.Sequential(OrderedDict([
    ('fc1', nn.Linear(512,4096)),
    ('relu', nn.ReLU()),
    ('fc2', nn.Linear(4096,NUM_CLASSES)),
    ('output', nn.LogSoftmax(dim=1))
]))

net.fc = fc

#Print the number of Weights
net = FreezeNetwork(net,-1)

criterion = nn.CrossEntropyLoss()

BATCH_SIZE = 256
LR = 0.001

#Depending on which GPU Google Colab assign, you may need to reduce the batch size (factor of 2 is enough)
'''
factor = 2
BATCH_SIZE = int(BATCH_SIZE / factor)
LR = LR / factor
''' 

train_dataloader, val_dataloader, test_dataloader = PrepareDataLoaders()

parameters_to_optimize = net.parameters()
optimizer = optim.SGD(parameters_to_optimize, lr=LR, momentum=MOMENTUM, weight_decay=WEIGHT_DECAY)
scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=STEP_SIZE, gamma=GAMMA)


print()
meta_t = 'resn'+str(LR)+'_'+'SGD'
test, valid, best_acc = Training(net,meta_t)

print()
meta = 'ResNet18 wirh LR = {} and Optimizer = {}'.format(LR, 'SGD')
PlotAccuracyLoss(test,valid,meta=meta)


print()
best_net = torch.load(PATH_MODELS+meta_t+'.pth')
print('Best accuracy on Validation set {}'.format(best_acc))
_ = Validation(best_net, test_dataloader)

