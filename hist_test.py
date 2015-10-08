__all__ = ["ImageHist", "FeatureExtracter", "test_img1" , "test_FE", "test_img1_IR"]
from PIL import Image


class FeatureExtracter:
    
    def __init__(self, img):
        self.img = img
        data = self.img.getdata();
        self.r = list(data.getband(0))
        self.g = list(data.getband(1))
        self.b = list(data.getband(2))
        self.tex1 = self.findTexture1()

    def findTexture1(self):
        print "yeah"
    



class ImageHist:
    def __init__(self, hist):
        self.histR = hist[0:256]
        self.histG = hist[256:512]
        self.histB = hist[512:768]
       
    def cross(self, other):
        resR, resG, resB = [], [], []
        for i in range(0,256):
            resR.append(self.histR[i] * other.histR[i])
            resG.append(self.histG[i] * other.histG[i])
            resB.append(self.histB[i] * other.histB[i])
        return (resR, resG, resB)
    

test_img1 = Image.open("DOP25cm_2010_example_spring.tif")
test_img1_IR = Image.open("SI_FCIR_LV95_25cm.tif")
test_FE = FeatureExtracter(im)
