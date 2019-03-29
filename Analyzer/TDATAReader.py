import os,cv2,tifffile,time
import numpy as np
from libtiff import TIFFimage

class Volume:
    def __init__(self):
        self.image = None
        self.xRes = 1
        self.yRes = 1
        self.zRes = 1

class ImageCache:
    def __init__(self,imageName,img,timeData):
        self.cache = img
        self.timeStamp = timeData
        self.cacheName = imageName

def CachSortFun(arg1,arg2):
    return arg1.timeStamp > arg2.timeStamp

class ImageCacheManager:
    def __init__(self,maxCache):
        self.maxCache = maxCache if maxCache > 1 else 2
        self.cacheList=[]

    def GetCache(self,nameArg):
        for cache in self.cacheList:
            if cache.cacheName == nameArg:
                print('%s is read'%nameArg)
                cache.timeStamp = time.time()
                self.SortCacheList()
                return cache.cache
        return None

    def isCacheExisting(self,name):
        for cache in self.cacheList:
            if cache.cacheName == name:
                return True
        return False

    def SortCacheList(self):
        self.cacheList.sort(key = lambda x: x.timeStamp, reverse = True)

    def AddCache(self,img,name):
        cache = ImageCache(name,img,time.time())
        self.cacheList.append(cache)
        self.SortCacheList()
        if len(self.cacheList) > self.maxCache:
            del(self.cacheList[len(self.cacheList)-1])

    def ClearCache(self):
        self.cacheList.clear()


class TDATAReader:
    def __init__(self):
        self.param = dict()
        self.imageCache=[]
        self.blockSize = 512
        self.imageCacheManager = ImageCacheManager(10)
        self.valid = False

    def SetInputFileName(self,fileName):
        if not os.path.exists(fileName):
            print('mostd file invalid')
            return
        self._LoadDataInfo(fileName)
        self.valid = True

    def _LoadDataInfo(self,fileName):
        with open(fileName,'r') as fp:
            lines = fp.readlines()
            self.param['id'] = int(lines[0])
            self.param['img_type'] = int(lines[1])
            self.param['sz0'] = int(lines[2])
            self.param['sz1'] = int(lines[3])
            self.param['sz2'] = int(lines[4])
            self.param['level_size'] = int(lines[5])
            index = 6
            self.param['block_num'] = np.zeros((self.param['level_size'],3),np.int)
            for i in range(self.param['level_size']):
                self.param['block_num'][i,0] = lines[index]
                self.param['block_num'][i, 1] = lines[index+1]
                self.param['block_num'][i, 2] = lines[index + 2]
                index += 3
            self.param['rez_x'] = float(lines[index])
            self.param['rez_y'] = float(lines[index+1])
            self.param['rez_z'] = float(lines[index + 2])
            self.file_path_t = lines[index+3].replace('\n','')[1:]
        print('hehe')

    def SelectIOR(self,xBeg,xEnd,yBeg,yEnd,zBeg,zEnd,level):
        if xEnd - xBeg+1 > self.param['sz0'] or \
            yEnd - yBeg+1 > self.param['sz1'] or \
            zEnd - zBeg + 1 > self.param['sz2']:
            print('out of size,error')
            return None
        if xBeg >= xEnd or yBeg >= yEnd or zBeg >= zEnd:
            print('out of size,error')
            return None
        x_index_b = xBeg
        x_index_e = xEnd
        y_index_b = yBeg
        y_index_e = yEnd
        z_index_b = zBeg
        z_index_e = zEnd
        for i in range(1, level):
            x_index_b //= 2
            x_index_e //= 2
            y_index_b //= 2
            y_index_e //= 2
            z_index_b //= 2
            z_index_e //= 2
        if x_index_e - x_index_b > 1024 or y_index_e - y_index_b > 1024 \
            or z_index_e - z_index_b > 1024:
            print('target image too large')
            return None
        dtype = np.uint16 if self.param['img_type']==2 else np.uint8
        resImg = np.zeros((z_index_e - z_index_b + 1,
                           y_index_e - y_index_b + 1,
                           x_index_e - x_index_b + 1),dtype = dtype)
        x_block_b = x_index_b // self.blockSize
        x_block_e = x_index_e // self.blockSize
        y_block_b = y_index_b // self.blockSize
        y_block_e = y_index_e // self.blockSize
        z_block_b = z_index_b // self.blockSize
        z_block_e = z_index_e // self.blockSize

        x_shift = x_index_b % self.blockSize
        y_shift = y_index_b % self.blockSize
        z_shift = z_index_b % self.blockSize

        for i in range(z_block_b, z_block_e+1):
            for j in range(y_block_b, y_block_e + 1):
                for k in range(x_block_b, x_block_e + 1):
                    name = '%d_%d_%d.tif'%(k,j,i)
                    fileName = os.path.join(self.file_path_t,
                                            'level%d_data'%(level),
                                            'z%d'%(i),
                                            'y%d'%j, name)
                    #fileName = fileName.replace('\\','/')
                    curImg = None
                    if self.imageCacheManager.isCacheExisting(fileName):
                        curImg = self.imageCacheManager.GetCache(fileName)
                    else:
                        curImg = tifffile.imread(fileName)
                        self.imageCacheManager.AddCache(curImg,fileName)
                    x_temp_b = 0
                    x_temp_e = 0
                    y_temp_b = 0
                    y_temp_e = 0
                    z_temp_b = 0
                    z_temp_e = 0
                    if k == x_block_b and k!= x_block_e:
                        x_temp_b = x_index_b % self.blockSize
                        x_temp_e = self.blockSize - 1
                    if k != x_block_b and k!= x_block_e:
                        x_temp_b = 0
                        x_temp_e = self.blockSize - 1
                    if k != x_block_b and k== x_block_e:
                        x_temp_b = 0
                        x_temp_e = x_index_e % self.blockSize
                    if k == x_block_b and k== x_block_e:
                        x_temp_b = x_index_b % self.blockSize
                        x_temp_e = x_index_e % self.blockSize

                    if j == y_block_b and j!= y_block_e:
                        y_temp_b = y_index_b % self.blockSize
                        y_temp_e = self.blockSize - 1
                    if j != y_block_b and j!= y_block_e:
                        y_temp_b = 0
                        y_temp_e = self.blockSize - 1
                    if j != y_block_b and j== y_block_e:
                        y_temp_b = 0
                        y_temp_e = y_index_e % self.blockSize
                    if j == y_block_b and j== y_block_e:
                        y_temp_b = y_index_b % self.blockSize
                        y_temp_e = y_index_e % self.blockSize
                        
                    if i == z_block_b and i!= z_block_e:
                        z_temp_b = z_index_b % self.blockSize
                        z_temp_e = self.blockSize - 1
                    if i != z_block_b and i!= z_block_e:
                        z_temp_b = 0
                        z_temp_e = self.blockSize - 1
                    if i != z_block_b and i== z_block_e:
                        z_temp_b = 0
                        z_temp_e = z_index_e % self.blockSize
                    if i == z_block_b and i== z_block_e:
                        z_temp_b = z_index_b % self.blockSize
                        z_temp_e = z_index_e % self.blockSize
                    #cache
                    #TODO
                    #
                    zIndex1 = (i-z_block_b)*self.blockSize+(z_temp_b-z_shift)
                    zIndex2 = (i - z_block_b) * self.blockSize + (z_temp_e - z_shift)
                    yIndex1 = (j-y_block_b)*self.blockSize+(y_temp_b-y_shift)
                    yIndex2 = (j - y_block_b) * self.blockSize + (y_temp_e - y_shift)
                    xIndex1 = (k - x_block_b) * self.blockSize + (x_temp_b - x_shift)
                    xIndex2 = (k - x_block_b) * self.blockSize + (x_temp_e - x_shift)
                    resImg[zIndex1:zIndex2+1,yIndex1:yIndex2+1,xIndex1:xIndex2+1] =\
                        curImg[z_temp_b:z_temp_e+1,y_temp_b:y_temp_e+1,x_temp_b:x_temp_e+1]

        return resImg


