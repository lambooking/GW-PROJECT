#自注意力机制
import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import numpy as np
import matplotlib.pyplot as plt
from torch.autograd import Variable
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
import os
import time
import argparse
import copy
import torch.nn.init as init
from torch.nn.parameter import Parameter
from torch.nn.modules.module import Module
import torch.nn.functional as F
import torch.nn.init as init
from torch.nn.parameter import Parameter
from torch.nn.modules.module import Module
import torch.nn.functional as F
import torch.nn.init as init
from torch.nn.parameter import Parameter
from torch.nn.modules.module import Module
import torch.nn.functional as F
import torch.nn.init as init
from torch.nn.parameter import Parameter
from torch.nn.modules.module import Module

class SelfAttention(nn.Module):
    def __init__(self, in_dim, activation):
        super(SelfAttention, self).__init__()
        self.chanel_in = in_dim
        self.activation = activation

        self.query_conv = nn.Conv2d(in_channels=in_dim, out_channels=in_dim // 8, kernel_size=1)
        self.key_conv = nn.Conv2d(in_channels=in_dim, out_channels=in_dim // 8, kernel_size=1)
        self.value_conv = nn.Conv2d(in_channels=in_dim, out_channels=in_dim,