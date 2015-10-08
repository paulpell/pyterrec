import gui
import gtk
from load_img import load_img
import numpy as np
from scipy.ndimage import filters
from time import time, sleep
import svmutil
from multiprocessing import Process, Queue
import lrects
import os


orig_ir_path = "img/SI_FCIR_LV95_25cm.tif"
orig_rgb_path = "img/DOP25cm_2010_example_spring.tif"


def start_gui():
    w = gui.MainWin()
    w.addImagePath(orig_ir_path)
    w.addImagePath(orig_rgb_path)
    return w

def add_lrects(w):
    for l in lrects.lrects:
        w.add_labelledRect(l.box, l.label)

def create_draw_gui():
    w = gtk.Window()
    w.imgPanel = gtk.Image()
    scroll = gtk.ScrolledWindow()
    scroll.add_with_viewport(w.imgPanel)
    w.add(scroll)
    w.show_all()
    return w

def draw_cross(imgPanel, x, y, size):
    pixarr = imgPanel.get_pixbuf().pixel_array
    max_w, max_h = len(pixarr), len(pixarr[0])
    col = [255, 0, 0, 255]
    for i in range(-size, size + 1):
        if x+i < max_w and x+i >= 0:
            if y + i < max_h and y+i >= 0:
                pixarr[y+i][x+i] = col
            if y-i < max_h and y-i >= 0:
                pixarr[y-i][x+i] = col
    imgPanel.queue_draw()



# border is: int(patch_size / 2)
def run_extract_features(nr, np_rgb_img, np_ir_img, grad_magn, grad_orient, grad_threshold, border, queue):

    old_time = int(time() * 1000)

    height = min(len(np_rgb_img), len(np_ir_img)) if np_ir_img else len(np_rgb_img)
    width = min(len(np_rgb_img[0]), len(np_ir_img[0])) if np_ir_img else len(np_rgb_img[0])
    border = border

    print "Process %i starting, height = %i" % (nr, height)

    feats = []

    for y in range(0, height):
        if not (y+1) % int(height / 10.):
            new_time = int(time() * 1000)
            diff = new_time - old_time
            print "%i: %i%% (%i ms)" % (nr, int(100 * (y+1) / height), diff)
            old_time = new_time

        fs_row = []
        for x in range(0, width):
            pix_rgb = np_rgb_img[y][x]
            pix_ir = np_ir_img[y][x] if np_ir_img else 0.

            fs = []
            r, g, b = pix_rgb[0], pix_rgb[1], pix_rgb[2]
            nir = pix_ir[0] if np_ir_img else 0
            fs.append(r/255.)                     # red
            fs.append(g/255.)                     # green
            fs.append(b/255.)                     # blue
            fs.append(nir/255.)                   # near IR
            ndvi = 0 if r == 0 and nir == 0 else (r - nir) / (r + nir)      # NDVI
            fs.append(ndvi)

            # use gradient orientation and magnitude
            fs.append(grad_magn[y][x])
            fs.append(grad_orient[y][x])

            # patch-based stuff
            nr_patch_feats = 2 # UPDATE THIS!!!!!!!!!!!!!!
            if x >= border and x < width - border and y >= border and y < height - border:
                #TODO: use patch_rgb
                #patch_rgb = np_rgb_img[(y-border):(y+border+1) , (x-border):(x+border+1)]


                # mean gradient orientation in patch
                patch_grad_orient = grad_orient[(y-border):(y+border+1) ,(x-border):(x+border+1)]
                fs.append(np.mean(patch_grad_orient))

                # mean thresholded gradient
                patch_grad_magn = grad_magn[(y-border):(y+border+1) , (x-border):(x+border+1)]
                thr = lambda x: 0. if x < grad_threshold else 1.
                edge_pixels = map(thr, patch_grad_magn.flatten())
                fs.append(np.mean(edge_pixels))

                #histogram of colors in neighborhood

            else:
                for i in range(0,nr_patch_feats):
                    fs.append(0)

            fs_row.append(fs)

        feats.append(fs_row)


    filename = ("feats_%i_%i.npy" % (int(os.times()[-1]), nr))
    np.save(filename, feats)
    queue.put(filename)
    print "Process %i done" % nr



# Returns feats, a np.array, all values are scaled to [0,1]
# patch_size: 5 for a 5x5 patch, for example
# img_size: percent of the image to use in both directions 
def extract_features(path_rgb_img, path_ir_img = None, patch_size=5, img_size=(1.,1.), n_threads=4):

    print "Loading images.."
    pil_rgb_img = load_img(path_rgb_img)
    size_rgb = pil_rgb_img.size
    new_size = (0, 0, int(size_rgb[0] * img_size[0]), int(size_rgb[1] * img_size[1]))
    pil_rgb_img = pil_rgb_img.crop(new_size)
    pil_rgb_img_grey = pil_rgb_img.convert("L")

    if path_ir_img:
        pil_ir_img = load_img(path_ir_img)
        size_ir = pil_ir_img.size
        new_size = (0, 0, int(size_ir[0] * img_size[0]), int(size_ir[1] * img_size[1]))
        pil_ir_img = pil_ir_img.crop(new_size)
        pil_ir_img_grey = pil_ir_img.convert("L")

        np_ir_img = np.array(pil_ir_img)
        np_ir_img_grey = np.array(pil_ir_img_grey)
    else:
        pil_ir_img = None
        pil_ir_img_grey = None

        np_ir_img = None
        np_ir_img_grey = None


    np_rgb_img = np.float32(np.array(pil_rgb_img))
    np_rgb_img_grey = np.float32(np.array(pil_rgb_img_grey))

    print "shape of np_rgb_img : " 
    for i in np_rgb_img.shape:
        print i


    print "Computing gradients.."
    dx_rgb_grey = filters.sobel(np_rgb_img_grey, 1)
    dy_rgb_grey = filters.sobel(np_rgb_img_grey, 0)
    grad_magn = np.sqrt(dx_rgb_grey**2 + dy_rgb_grey**2)
    grad_orient = np.arctan2(dy_rgb_grey, dx_rgb_grey)

    max_grad_orient = np.max(grad_orient)
    grad_orient = grad_orient / max_grad_orient


    max_grad_magn = np.max(grad_magn)
    grad_magn = grad_magn / max_grad_magn
    grad_threshold = 0.4 # arbitrary threshold to detect edges

    print "Extracting other features.."
    border = int(patch_size / 2)


    old_time = int(1000 * time())

    # create n_threads processes that will run the run_extract_features function above

    processes = []
    feat_files_queues = [] # contains for each thread, the name of the output file with the result
    slice_width = int(len(np_rgb_img) / n_threads)
    for i in range(0, n_threads-1):
        s,e = i * slice_width, (i+1) * slice_width
        feat_files_queues.append(Queue())
        if np_ir_img:
            args = (i+1, np_rgb_img[s:e], np_ir_img[s:e], grad_magn[s:e], grad_orient[s:e], grad_threshold, border,feat_files_queues[-1])
        else:
            args = (i+1, np_rgb_img[s:e], None, grad_magn[s:e], grad_orient[s:e], grad_threshold, border,feat_files_queues[-1])
        p = Process(target=run_extract_features, args=args)
        processes.append(p)
        p.start()

    # handle last thread
    s = (n_threads - 1) * slice_width
    feat_files_queues.append(Queue())
    if np_ir_img:
        args = (n_threads, np_rgb_img[s:], np_ir_img[s:], grad_magn[s:], grad_orient[s:], grad_threshold, border, feat_files_queues[-1])
    else:
        args = (n_threads, np_rgb_img[s:], None, grad_magn[s:], grad_orient[s:], grad_threshold, border, feat_files_queues[-1])
    p = Process(target=run_extract_features, args=args)
    processes.append(p)
    p.start()


    feat_files = []
    for q in feat_files_queues:
        while q.empty():
            sleep(1) # wait 1 second
        filename = q.get()
        feat_files.append(filename)

    time_diff = int(1000 * time()) - old_time

    height = min(len(np_rgb_img), len(np_ir_img)) if np_ir_img else len(np_rgb_img)
    #print "final feats has same size than begin: " , len(feats) == height
    #print "Total time: %i" % time_diff

    # re-create the original shape for the complete set of features
    feats = np.vstack(map(lambda x: np.load(x), feat_files))

    return feats



def create_svm_problem(feats, labelledRects):
    labels = []
    values = []

    height, width, nd = feats.shape

    for rect in labelledRects:
        x0, y0, x1, y1 = rect.box
        if x0 >= width or y0 >= height:
            continue
        if x1 >= width:
            x1 = width - 1
        if y1 >= height:
            y1 = height - 1
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                vs = []
                for i in feats[y][x]:
                    vs.append(i)
                labels.append(rect.label)
                values.append(vs)

    return svmutil.svm_problem(labels, values)

def create_svm_labels_and_values(feats, labelledRects):
    labels = []
    values = []

    height, width, nd = feats.shape

    for rect in labelledRects:
        x0, y0, x1, y1 = rect.box
        if x0 >= width or y0 >= height:
            continue
        if x1 >= width:
            x1 = width - 1
        if y1 >= height:
            y1 = height - 1
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                vs = []
                for i in feats[y][x]:
                    vs.append(i)
                labels.append(rect.label)
                values.append(vs)

    return (labels, values)


# for the 3D feats (height, width, nd),
# return the 2D labels (height,width)
# Needs to be a model generated by svmutil.svm_train()
def run_predict_svm(nr, model, feats, q):
    print "Process %i starting for %i rows" % (nr, len(feats))

    labels = []

    old_time = int(time() * 1000)

    l = len(feats)
    for i in range(0,l):
        if not (i+1) % int(l / 10.):
            new_time = int(time() * 1000)
            diff = new_time - old_time
            print "%i: %i%% (%i ms)" % (nr, int(100 * (i+1) / l), diff)
            old_time = new_time
        
        fs_list = map(lambda x: list(x), feats[i]) # svm uses lists (or dicts)
        rl = np.ones(len(fs_list))
        rl1 = svmutil.svm_predict(rl, fs_list, model, '-q') #-q: quiet
        labels.append(rl1[0]) # rl1 = (labels, accuracy, another_val)



    filename = ("labels_%i_%i.npy" % (int(os.times()[-1]), nr))
    np.save(filename, labels)
    q.put(filename)
    print "Process %i done" % nr



# uses processes to run the above function
def predict_svm(model, feats, n_threads = 4):


    old_time = int(1000 * time())

    # create n_threads processes that will run the run_extract_features function above

    processes = []
    label_files_queues = []
    slice_width = int(len(feats) / n_threads)
    for i in range(0, n_threads-1):
        s,e = i * slice_width, (i+1) * slice_width
        label_files_queues.append(Queue())
        args = (i+1, model, feats[s:e],label_files_queues[-1])
        p = Process(target=run_predict_svm, args=args)
        processes.append(p)
        p.start()

    # handle last thread
    s = (n_threads - 1) * slice_width
    label_files_queues.append(Queue())
    args = (n_threads, model, feats[s:], label_files_queues[-1])
    p = Process(target=run_predict_svm, args=args)
    processes.append(p)
    p.start()


    label_files = []
    for q in label_files_queues:
        while q.empty():
            sleep(1) # wait 1 second
        label_files.append(q.get())

    time_diff = int(1000 * time()) - old_time

    # re-create the original shape for the complete set of features
    labels = np.vstack(map(lambda x: np.load(x), label_files))

    print "Total time: %i ms" % time_diff

    return labels







