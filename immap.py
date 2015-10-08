
    # TODO: __init__ & API

class ImageMapper:


#    def find_scaling(self, p11, p12, p21, p22):
#        norm, sub = np.linalg.norm, np.subtract
#        return norm(sub(p12, p11)) / norm(sub(p22,p21))
#
#    def find_rotation(self, p11, p12, p21, p22):
#        x11, y11 = p11
#        x12, y12 = p12
#        x21, y21 = p21
#        x22, y22 = p22
#        alpha1 = np.arctan2(y12-y11, x12-x11)
#        alpha2 = np.arctan2(y22-y21, x22-x21)
#        return alpha1 - alpha2
#
#    def transform_img2(self):
#        p11,p12 = self.tags_[0]
#        p21,p22 = self.tags_[1]
#        print "Points: ", p11, p12, p21, p22
#
#        # transform the second image for a rotation of alpha and a scaling of s
#        new_size = (1600, 1600)
#
#        alpha = self.find_rotation(p11, p12, p21, p22)
#        cosa = np.cos(alpha)
#        sina = np.sin(alpha)
#        rot_mat = [[cosa, -sina], [sina, cosa]]
#        print "Rotation angle: " , alpha
#
#        # new points are rotated before finding scaling factor
#        dot = np.dot
#        np11, np12 = dot(p11, rot_mat), dot(p12, rot_mat)
#        np21, np22 = dot(p21, rot_mat), dot(p22, rot_mat)
#        s = self.find_scaling(np11, np12, np21, np22)
#        #s = self.find_scaling(p11, p12, p21, p22)
#        print "Scaling factor: " , s
#
#        # rotate around p11, by angle a, and scale by s
#        a = e = cosa / s
#        b = sina / s
#        d = -b
#        c = p11[0] * (1 - a - b)
#        f = p11[1] * (1 - d - e)
#        trans_mat = (a, b, c, d, e, f)
#        print "Transformation matrix:" ,trans_mat
#
#        return load_img.load_img(self.imgPaths_[1]).transform(new_size, Image.AFFINE, trans_mat)



#    def compute(self, data):
#        if len(self.tags_) != 2:
#            self.errMsg("Need 2 images!")
#            return
#        for i in range(0,1):
#            if len(self.tags_[i]) != 2:
#                self.errMsg("Need 2 tags for image %i!" % (i))
#                return
#
#        new_img = self.transform_img2()
 
