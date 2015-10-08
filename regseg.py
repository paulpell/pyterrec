import numpy as np 
from time import time

REGION_BIG = 0
REGION_SMALL = 1
REGION_MERGED = 2

def pix2hash(p):
    return (p[0] << 32) | p[1]

def hash2pix(h):
    return [h >> 32, h & 0xFFFFFFFF]


class Region:
    def __init__(self):
        self.label = -1
        self.pixels = []
        self.category = -1
        self.neighbors = [] # list of ids
        
class RegionSegmenter():

    def __init__(self, labels, min_region_size, advanced = False):
        self.labels = labels
        self.min_region_size = min_region_size
        self.small_region_dict = {}
        self.big_region_dict = {}

        self.pix2reg = [ np.zeros(len(l)) for l in labels ]
        self.id2reg = {}

        self.pixhashes = [ [(y << 32) | x for x in range(0, len(labels[y])) ] for y in range(0, len(labels)) ]

        self.border_left = {}
        self.border_right = {}
        self.border_top = {}
        self.border_down = {}

        self.setup()
        # if advanced:
        #TODO


    def setup(self):


        ls = self.labels

        old_time = int(1000 * time())

        " array to know which points were classified so far "
        self.classified = [np.zeros(len(l)) for l in ls]


        # try to visit each pixel
        small, big = self.small_region_dict, self.big_region_dict
        x,y = 0,0
        while y < len(ls):

            r = self.create_region(x,y)
            l = r.label
            if r.category == REGION_SMALL:
                if small.has_key(l):
                    small[l].append(r)
                else:
                    small[l] = [r]
            elif r.category == REGION_BIG:
                if big.has_key(l):
                    big[l].append(r)
                else:
                    big[l] = [r]

            # adapt next i,j
            while y < len(ls) and self.classified[y][x]:
                x += 1
                if x >= len(ls[y]):
                    x = 0
                    y += 1

        new_time = int(1000 * time())
        diff = new_time - old_time

        print "Time to visit the pixels: %i ms" % (diff)
        print "Setup done"


    # return Region
    # we check if all points on left and right are in the same region:
    # if so, we merge if needed
    def create_region(self, x0, y0):
        ls = self.labels
        ret_reg = Region()
        regid = id(ret_reg)

        self.id2reg[regid] = ret_reg

        """ When we create the region, if the label of all the left and top
        neighbors is the same, then we know for sure that it is the most
        important neighbor """
        certain_neighbor = None
        
        """ If there is no certain neighbor, we count the number of neighbor
        with each label; the maximum gives us the most important neighbor """
        neigh_label_cnt = {}
        neigh_label_id = {}

        tovisit = [[x0,y0]]

        while len(tovisit) > 0:
            x, y = tovisit.pop()
            self.pix2reg[y][x] = regid

            # initialize the region with this point
            ph = self.pixhashes[y][x]
            if 0 == len(ret_reg.pixels):
                ret_reg.pixels = [[y,x]]
                ret_reg.label = ls[y][x]
                """ if we are not on the border, we check if both left and top
                neighbors are the same"""
                if x > 0 and y > 0:
                    neigh_top = self.border_top[ph]
                    neigh_left = self.border_left[ph]
                    if neigh_top == neigh_left:
                        certain_neighbor = neigh_top
            # or add this point to the region
            else:
                ret_reg.pixels.append([y,x])
                if certain_neighbor:
                    if y > 0:
                        if self.border_top.has_key(ph):
                            if self.border_top[ph] is not certain_neighbor:
                                certain_neighbor = None
                    if x > 0:
                        if self.border_left.has_key(ph):
                            if self.border_left[ph] is not certain_neighbor:
                                certain_neighbor = None


            self.classified[y][x] = 1

            # check if neighbors are in the same region
            # left and top contain this id,
            # right and down contain the label of the other
            if y + 1 < len(ls):
                l2 = ls[y+1][x]
                if ret_reg.label == l2:
                    if not self.classified[y+1][x]:
                        tovisit.append([x, y+1])
                else:
                    self.border_down[self.pixhashes[y][x]] = -l2
                    self.border_top[self.pixhashes[y+1][x]] = regid
            if x + 1 < len(ls[y]):
                l2 = ls[y][x+1]
                if ret_reg.label == l2:
                    if not self.classified[y][x+1]:
                        tovisit.append([x+1, y])
                else:
                    self.border_right[self.pixhashes[y][x]] = -l2
                    self.border_left[self.pixhashes[y][x+1]] = regid

        if len(ret_reg.pixels) < self.min_region_size:
            if certain_neighbor:
                ret_reg.category = REGION_MERGED
                self.id2reg[certain_neighbor].pixels.extend(ret_reg.pixels)
            else:
                ret_reg.category = REGION_SMALL
        else:
            ret_reg.category = REGION_BIG

        return ret_reg





















    # WARNING: top-down and right-left definitions were changed!
    # and pix2hash now has a table

    def shrink_region(self, region):
        pass # TODO

    def shrink(self):
        
        # count for each pixel that has a neighbor, which label(s) is(are) neighbor
        # return (most imp. region, other regs with same label, label)
        def find_most_important_neighbor(reg):
            regs =  self.pix2reg.values()
            def reg2hash(r):
                return regs.index(r)
            def hash2reg(h):
                return regs[h]

            # dict counting pixels shared between reg and the other regions
            b_cnt = {}
            # dicts to konw which border info to remove
            b_pix_l = {}
            b_pix_r = {}
            b_pix_t = {}
            b_pix_d = {}
            for r in self.pix2reg.values():
                b_cnt[reg2hash(r)] = 0
                b_pix_r[reg2hash(r)] = []
                b_pix_l[reg2hash(r)] = []
                b_pix_t[reg2hash(r)] = []
                b_pix_d[reg2hash(r)] = []

            # count neighbors and store border info for each p in reg
            for p in reg:
                ph = pix2hash(p)
                if self.border_left.has_key(ph):
                    p2 = [p[0]-1, p[1]]
                    rh = reg2hash(self.pix2reg[pix2hash(p2)])
                    b_cnt[rh] += 1
                    b_pix_l[rh].append(p)
                if self.border_right.has_key(ph):
                    p2 = [p[0]+1, p[1]]
                    rh = reg2hash(self.pix2reg[pix2hash(p2)])
                    b_cnt[rh] += 1
                    b_pix_r[rh].append(p)
                if self.border_top.has_key(ph):
                    p2 = [p[0], p[1]-1]
                    rh = reg2hash(self.pix2reg[pix2hash(p2)])
                    b_cnt[rh] += 1
                    b_pix_t[rh].append(p)
                if self.border_down.has_key(ph):
                    p2 = [p[0], p[1]+1]
                    rh = reg2hash(self.pix2reg[pix2hash(p2)])
                    b_cnt[rh] += 1
                    b_pix_d[rh].append(p)


            
            # look in which region there is the biggest count
            best_score = -1
            best_reg = []
            best_label = -1
            for rh in b_cnt.keys():
                if b_cnt[rh] > best_score:
                    best_score = b_cnt[rh]
                    best_reg = hash2reg(rh)
                    p = best_reg[0]
                    best_label = self.labels[p[0]][p[1]]

            print 'best score: %i, best label: %i' % (best_score, best_label)

            ls = self.labels

            # find all neighbor regions with same label
            all_regs = []
            for rh in b_cnt.keys(): # for each neighbor (cnt > 0)
                r = hash2reg(rh)
                p = r[0]
                l = ls[p[0]][p[1]]
                if b_cnt[rh] > 0 and l == best_label and not r is best_reg and not r in all_regs:
                    all_regs.append(r)


            # remove border information
            for k in b_pix_r.keys():
                for p in b_pix_r[k]:
                    if ls[p[0]][p[1]] == best_label:
                        del self.border_right[pix2hash(p)]
                        del self.border_left[self.pixhashes[p[0]+1][p[1]]]
            for k in b_pix_l.keys():
                for p in b_pix_l[k]:
                    if ls[p[0]][p[1]] == best_label:
                        del self.border_left[pix2hash(p)]
                        del self.border_right[self.pixhashes[p[0]-1][p[1]]]
            for k in b_pix_t.keys():
                for p in b_pix_t[k]:
                    if ls[p[0]][p[1]] == best_label:
                        del self.border_top[pix2hash(p)]
                        del self.border_down[self.pixhashes[p[0]][p[1]-1]]
            for k in b_pix_d.keys():
                for p in b_pix_d[k]:
                    if ls[p[0]][p[1]] == best_label:
                        del self.border_down[pix2hash(p)]
                        del self.border_top[self.pixhashes[p[0]][p[1]+1]]


            ret = (best_reg, all_regs, best_label)
            print 'Returning ', ret
            return ret

        def update_pix2reg(reg, new_reg):
            for p in reg:
                self.pix2reg[pix2hash(p)] = new_reg

        # while something moves, merge small regions into their neighbors
        moved = True
        while moved:
            moved = False

            for l in self.region_dict.keys():
                for r in self.region_dict[l]:
                    if len(r) < self.min_region_size:
                        moved = True
                        print 'Found region to shrink'
                        new_reg, others, l2 = find_most_important_neighbor(r)
                        new_reg.extend(r)
                        self.region_dict[l].remove(r)
                        for r2 in others:
                            new_reg.extend(r2)
                            if r2 in self.region_dict[l2]:
                                self.region_dict[l2].remove(r2)
                        update_pix2reg(r, new_reg)
                        for r2 in others:
                            update_pix2reg(r2, new_reg)


