import os, torch
import numpy as np
from torch import nn
from torch.nn import functional as F

class SuperResolutionGenerator:
    def __init__(self):
        pass
    def SetTorchFilePath(self,path):
        self.pretrained_net = torch.load(path)
        self.pretrained_net.eval()
        torch.set_grad_enabled(False)
        torch.cuda.empty_cache()

    def SetMeanMax(self,mean,max):
        self.meamVal = mean
        self.maxVal = max

    def Generate(self,img):
        torch.cuda.empty_cache()
        torch.set_grad_enabled(False)
        lrImg = np.array(img, dtype=np.float32)
        lrImg = (lrImg - self.meamVal) / (self.maxVal / 2)
        lrImg = np.expand_dims(lrImg, axis=0)
        lrImg = np.expand_dims(lrImg, axis=0)
        lrImg = torch.from_numpy(lrImg).float()
        lrImg = lrImg.to(torch.device('cuda:1'))
        pre2 = self.pretrained_net(lrImg)
        saveImg = pre2.cpu().data.numpy()[0, 0, :, :, :]
        saveImg *= (self.maxVal / 2)
        saveImg += self.meamVal
        saveImg = np.uint8(np.maximum(np.minimum(saveImg, 255),0))
        return saveImg