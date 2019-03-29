import os, torch
import numpy as np
from torch import nn
from torch.nn import functional as F
import tifffile



def default_conv(in_channels, out_channels, kernel_size, bias=True):
    return nn.Conv2d(
        in_channels,
        out_channels,
        kernel_size,
        padding=(kernel_size // 2),
        bias=bias)


def default_conv3d(in_channels, out_channels, kernel_size, bias=True):
    return nn.Conv3d(
        in_channels,
        out_channels,
        kernel_size,
        padding=(kernel_size // 2),
        bias=bias)


def prepare(dev, *args):
    # print(dev)
    device = torch.device(dev)
    if dev == 'cpu':
        device = torch.device('cpu')
    return [a.to(device) for a in args]


def calc_psnr(sr, hr, scale):
    diff = (sr - hr)
    # shave = scale + 6
    # valid = diff[..., shave:-shave, shave:-shave,:]#2，2，1
    # mse = valid.pow(2).mean()
    mse = np.mean(diff * diff) + 0.0001
    return -10 * np.log10(mse / (4095 ** 2))


def RestoreNetImg(img, mean, max):
    # rImg = (img - self.mean1) / self.std1
    rImg = np.maximum(np.minimum(img * max + mean, 255), 0)
    return rImg


class WDSRABlock3D(nn.Module):
    def __init__(
            self, n_feats, kernel_size,
            block_feats, wn, act=nn.ReLU(True)):
        super(WDSRABlock3D, self).__init__()
        body = []
        body.append(
            wn(nn.Conv3d(n_feats, block_feats, kernel_size, padding=kernel_size // 2)))
        body.append(act)
        body.append(
            wn(nn.Conv3d(block_feats, n_feats, kernel_size, padding=kernel_size // 2)))

        self.body = nn.Sequential(*body)

    def forward(self, x):
        res = self.body(x) + x
        return res


class ResBlock3D(nn.Module):
    def __init__(self,
                 conv=default_conv3d,
                 n_feats=64,
                 kernel_size=3,
                 bias=True,
                 bn=False,
                 act=nn.ReLU(inplace=True),  # nn.LeakyReLU(inplace=True),
                 res_scale=1):

        super(ResBlock3D, self).__init__()
        m = []
        for i in range(2):
            m.append(conv(n_feats, n_feats, kernel_size, bias=bias))
            if bn:
                m.append(nn.BatchNorm2d(n_feats))
            if i == 0:
                m.append(act)

        self.body = nn.Sequential(*m)
        self.res_scale = res_scale

    def forward(self, x):
        res = self.body(x)
        res += x
        return res


class PixelUpsampler3D(nn.Module):
    def __init__(self,
                 upscale_factor,
                 # conv=default_conv3d,
                 # n_feats=32,
                 # kernel_size=3,
                 # bias=True
                 ):
        super(PixelUpsampler3D, self).__init__()
        self.scaleFactor = upscale_factor

    def _pixel_shuffle(self, input, upscale_factor):
        batch_size, channels, in_depth, in_height, in_width = input.size()
        channels //= upscale_factor[0] * upscale_factor[1] * upscale_factor[2]
        out_depth = in_depth * upscale_factor[0]
        out_height = in_height * upscale_factor[1]
        out_width = in_width * upscale_factor[2]
        input_view = input.contiguous().view(
            batch_size, channels, upscale_factor[0], upscale_factor[1], upscale_factor[2], in_depth,
            in_height, in_width)
        shuffle_out = input_view.permute(0, 1, 5, 2, 6, 3, 7, 4).contiguous()
        return shuffle_out.view(batch_size, channels, out_depth, out_height, out_width)

    def forward(self, x):
        # x = self.conv(x)
        up = self._pixel_shuffle(x, self.scaleFactor)
        return up


class GetTrainDataSet3():
    def __init__(self, lrDir, midDir, hrDir, mean, std):
        self.lrDir = lrDir
        self.mrDir = midDir
        self.hrDir = hrDir
        self.lrFileList = os.listdir(self.lrDir)
        self.hrFileList = os.listdir(self.hrDir)
        if len(self.lrFileList) != len(self.hrFileList):
            self.check = False

        # self.mean1=np.array([160],dtype=np.float32)
        self.mean1 = mean  # np.array([127], dtype=np.float32)
        self.std1 = std  # np.array([350], dtype=np.float32)

    def Check(self):
        return self.check

    def DataNum(self):
        return len(self.lrFileList)

    def __len__(self):
        return len(self.lrFileList)

    def __getitem__(self, ind):
        # load the image and labels
        imgName = self.lrFileList[ind]
        lrName = os.path.join(self.lrDir, imgName)
        mrName = os.path.join(self.mrDir, imgName)
        hrName = os.path.join(self.hrDir, imgName)
        # hrName = os.path.join(self.hrDir, '_'.join(imgName.split('_')[0:3])+'.tif')
        lrImg = tifffile.imread(lrName)
        mrImg = tifffile.imread(mrName)
        hrImg = tifffile.imread(hrName)

        if (np.multiply(lrImg.shape, 2) != mrImg.shape).any():
            sp = np.multiply(lrImg.shape, 2)
            # print(sp)
            msp = mrImg.shape
            tmpImg = np.zeros(sp, dtype=lrImg.dtype)
            tmpImg[0:msp[0], 0:msp[1], 0:msp[2]] = mrImg
            mrImg = tmpImg

        lrImg = np.array(lrImg, dtype=np.float32)
        mrImg = np.array(mrImg, dtype=np.float32)
        hrImg = np.array(hrImg, dtype=np.float32)

        lrImg = (lrImg - self.mean1) / self.std1
        mrImg = (mrImg - self.mean1) / self.std1
        hrImg = (hrImg - self.mean1) / self.std1

        lrImg = np.expand_dims(lrImg, axis=0)
        mrImg = np.expand_dims(mrImg, axis=0)
        hrImg = np.expand_dims(hrImg, axis=0)

        # torch.set_grad_enabled(True)
        lrImg = torch.from_numpy(lrImg).float()
        mrImg = torch.from_numpy(mrImg).float()
        hrImg = torch.from_numpy(hrImg).float()
        return lrImg, mrImg, hrImg, imgName


class GetTrainDataSet2():
    def __init__(self, lrDir, hrDir, mean, std):
        self.lrDir = lrDir
        self.hrDir = hrDir
        self.lrFileList = os.listdir(self.lrDir)
        self.hrFileList = os.listdir(self.hrDir)
        if len(self.lrFileList) != len(self.hrFileList):
            self.check = False

        # self.mean1=np.array([160],dtype=np.float32)
        self.mean1 = mean  # np.array([127], dtype=np.float32)
        self.std1 = std  # np.array([350], dtype=np.float32)

    def Check(self):
        return self.check

    def DataNum(self):
        return len(self.hrFileList)

    def __len__(self):
        return len(self.hrFileList)

    def __getitem__(self, ind):
        # load the image and labels
        imgName = self.hrFileList[ind]
        lrName = os.path.join(self.lrDir, imgName)
        hrName = os.path.join(self.hrDir, imgName)

        lrImg = tifffile.imread(lrName)
        hrImg = tifffile.imread(hrName)

        lrImg = np.array(lrImg, dtype=np.float32)
        hrImg = np.array(hrImg, dtype=np.float32)

        lrImg = (lrImg - self.mean1) / self.std1
        hrImg = (hrImg - self.mean1) / self.std1

        lrImg = np.expand_dims(lrImg, axis=0)
        hrImg = np.expand_dims(hrImg, axis=0)

        # torch.set_grad_enabled(True)
        lrImg = torch.from_numpy(lrImg).float()
        hrImg = torch.from_numpy(hrImg).float()
        return lrImg, hrImg


class GetTestDataSet():
    def __init__(self, testDir, mean, std):
        self.testDir = testDir
        self.testFileList = os.listdir(self.testDir)

        # self.mean1=np.array([160],dtype=np.float32)
        self.mean1 = mean  # np.array([127], dtype=np.float32)
        self.std1 = std  # np.array([350], dtype=np.float32)

    def Check(self):
        return self.check

    def DataNum(self):
        return len(self.testFileList)

    def __len__(self):
        return len(self.testFileList)

    def __getitem__(self, ind):
        # load the image and labels
        imgName = self.testFileList[ind]
        lrName = os.path.join(self.testDir, imgName)
        lrImg = tifffile.imread(lrName)

        lrImg = np.array(lrImg, dtype=np.float32)
        lrImg = (lrImg - self.mean1) / self.std1
        lrImg = np.expand_dims(lrImg, axis=0)
        # torch.set_grad_enabled(True)
        lrImg = torch.from_numpy(lrImg).float()
        return lrImg
