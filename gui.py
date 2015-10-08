import gtk
import gobject
import numpy as np
from PIL import Image
import load_img
import copy

CROSS_SIZE = 6
DRAW_RECTANGLE = 0
DRAW_CROSS = 1

alpha = 255
colorpalette = [
           [255,   0,   0, 255], #red
           [  0, 255,   0, 255], #green
           [  0,   0, 255, 255], #blue
           [255, 255,   0, 255], #yellow
           [255,   0, 255, 255], #purple
           [  0, 255, 255, 255], #cyan
           [  0, 127, 255, 255], #light blue
           [255, 127, 127, 255], #pig
           [255, 255, 127, 255], #light yellow
           [255, 130, 255, 255], #light purple
           [255, 160,   0, 255], #orange
           [255, 255, 255, 255], # white
           [  0,   0,   0, 255], #black
       ]

class LabelPopup(gtk.Dialog):

    def __init__(self):
        gtk.Dialog.__init__(self, "Specify the rectangle's label")
        vbox = gtk.Dialog.get_content_area(self)
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label("Specify label: "))
        self.entry = gtk.Entry(10)
        hbox.pack_start(self.entry)
        vbox.pack_start(hbox)

        gtk.Dialog.add_buttons(self, gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)


    # return (b,v) where b is a boolean telling whether v (the input label) is valid
    def show(self):
        self.show_all()
        resp = self.run()
        value = self.entry.get_text()
        try:
            value = int(value)
        except:
            return (False, 0)
        if resp != gtk.RESPONSE_NONE:
            self.destroy()
        return (resp == gtk.RESPONSE_OK, value)


class LabelledRect:

    def __repr__(self):
        return str(self.box) + ": " + str(self.label)

    def __init__(self, box, label):
        self.box = box
        self.label = label

        a = 70
      
class MainWin:
    """ displays images and receives clicks to adjust them """

    def errMsg(self, msg):
        gtk.MessageDialog(self.window_, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE, msg)

    def quit_event(widget, event, data=None):
        gtk.main_quit()

    def button_pressed(self, event, data):
        x,y = data.x, data.y
        if self.click_op == DRAW_CROSS:
            self.add_tag(x, y)
        elif self.click_op == DRAW_RECTANGLE:
            self.draw_rect(x,y)
          

    def treeview_clicked(self, iter, path, user_data):
        img_n = path[0]
        self.show_image(img_n)
        

    # we want to capture these events, but do nothing with them...
    def imgPanel_event_handler(self, event, data):
        pass


    def erase_rect(self):
        x0 = int(min(self.tmp_rect_base[0], self.tmp_rect_end[0]))
        x1 = int(max(self.tmp_rect_base[0], self.tmp_rect_end[0]))
        y0 = int(min(self.tmp_rect_base[1], self.tmp_rect_end[1]))
        y1 = int(max(self.tmp_rect_base[1], self.tmp_rect_end[1]))

        pixarr = self.imgPanel_.get_pixbuf().pixel_array

        for i in range(x0, x1 + 1):
            for j in range(y0, y1+1):
                pixarr[j][i] = self.orig_pixbuf[j][i]

    def draw_rect(self, rect, col = [255, 255, 255, 255]):
        x0, y0, x1, y1 = rect
        pixarr = self.imgPanel_.get_pixbuf().pixel_array
        ndim = len(pixarr[0][0])
        for i in range(x0, x1):
            pixarr[y0][i] = col[0:ndim]
            pixarr[y1][i] = col[0:ndim]
        for i in range(y0, y1):
            pixarr[i][x0] = col[0:ndim]
            pixarr[i][x1] = col[0:ndim]
        self.imgPanel_.queue_draw()


    def draw_pixmap(self, pixmap):
        pixarr = self.imgPanel_.get_pixbuf().pixel_array
        for y in range(0, min(len(pixmap), len(pixarr))):
            for x in range(0, min(len(pixmap[y]), len(pixarr[y]))):
                pixarr[y][x] = pixmap[y][x]


    def start_rect(self, x, y):
        self.orig_pixbuf = copy.copy(self.imgPanel_.get_pixbuf().pixel_array)
        self.tmp_rect_base = [x,y]
        self.tmp_rect_end = [x,y]

    def update_rect(self, x, y):
        self.erase_rect()

        self.tmp_rect_end = [x,y]

        x0 = int(min(self.tmp_rect_base[0], x))
        x1 = int(max(self.tmp_rect_base[0], x))
        y0 = int(min(self.tmp_rect_base[1], y))
        y1 = int(max(self.tmp_rect_base[1], y))
        self.draw_rect((x0,y0,x1,y1))
        
    def commit_rect(self, x, y):

        labelPopup = LabelPopup()
        valid, label = labelPopup.show()
        if valid:

            x0 = int(min(self.tmp_rect_base[0], x))
            x1 = int(max(self.tmp_rect_base[0], x))
            y0 = int(min(self.tmp_rect_base[1], y))
            y1 = int(max(self.tmp_rect_base[1], y))

            box = (x0, y0, x1, y1)
            print "New rect: ", box, ", label=", label
            self.add_labelledRect(box, label)

        else:
            self.erase_rect()
        self.imgPanel_.queue_draw()

    def add_labelledRect(self, box, label):
        self.labelledRects.append(LabelledRect(box, label))
        self.rect_list_.append([str(box), label])
        self.draw_rect(box, colorpalette[label])

    def scroll_event_handler(self, data, event):
        if event.type == gtk.gdk.BUTTON_PRESS:
            self.start_rect(event.x, event.y)
        elif event.type == gtk.gdk.MOTION_NOTIFY:
            self.update_rect(event.x, event.y)
        elif event.type == gtk.gdk.BUTTON_RELEASE:
            self.commit_rect(event.x, event.y)


    def __init__(self):
        self.height_ = 700
        self.width_ = 1000
        self.window_ = gtk.Window()
        w = self.window_
        w.connect('delete-event', self.quit_event)

        self.current_img_ = -1
        self.tags_ = []
        self.imgPaths_ = []
        self.labelledRects = []

        #self.click_op = DRAW_RECTANGLE

        hbox = gtk.HBox()
        vbox = gtk.VBox()
        vbox.pack_start(self.createImgList(), False, False, 5)
        self.img_iter_ = None
        #computeButton = gtk.Button("compute")
        #computeButton.connect("clicked", self.compute)
        #vbox.pack_start(computeButton, False, False, 5)
        vbox.pack_start(self.createRectList(), False, False, 5)
        vbox.set_size_request(300, self.height_)
        hbox.pack_start(vbox, False, False, 4)
        # create img panel
        self.imgPanel_ = gtk.Image()
        i = self.imgPanel_
        i.set_events(gtk.gdk.ALL_EVENTS_MASK)
        i.connect("event", self.imgPanel_event_handler)
        self.scroll_ = gtk.ScrolledWindow()
        scroll = self.scroll_
        scroll.grab_focus()
        scroll.add_with_viewport(i);
        hbox.pack_end(scroll, False, False, 4)
        scroll.set_events(gtk.gdk.ALL_EVENTS_MASK)
        scroll.connect("event", self.scroll_event_handler)
        scroll.set_size_request(self.width_ - 300, self.height_)
        w.add(hbox)
        w.resize(self.width_, self.height_);
        w.show_all()

    def createImgList(self):
        self.img_list_ = gtk.ListStore(str, bool)
        treeview = gtk.TreeView(self.img_list_)
        treeview.connect("row-activated", self.treeview_clicked)
        column_img = gtk.TreeViewColumn("images")
        treeview.append_column(column_img)
        column_rem = gtk.TreeViewColumn("")
        treeview.append_column(column_rem)
        cell_img = gtk.CellRendererText()
        column_img.pack_start(cell_img, True)
        column_img.add_attribute(cell_img, 'text', 0)
        cell_rem = gtk.CellRendererToggle()
        column_rem.pack_start(cell_rem, True)
        column_rem.add_attribute(cell_rem, 'active', 1)
        return treeview

    def createRectList(self):
        self.rect_list_ = gtk.ListStore(str, str)
        treeview = gtk.TreeView(self.rect_list_)
        column_rects = gtk.TreeViewColumn("rectangles")
        column_labels = gtk.TreeViewColumn("labels")

        treeview.append_column(column_rects)
        cell_rect = gtk.CellRendererText()
        column_rects.pack_start(cell_rect, True)
        column_rects.add_attribute(cell_rect, 'text', 0)

        treeview.append_column(column_labels)
        cell_label = gtk.CellRendererText()
        column_labels.pack_start(cell_label, True)
        column_labels.add_attribute(cell_label, 'text', 1)
        return treeview


    def addImagePath(self, img_path):
        self.img_iter_ = self.img_list_.append([img_path, False])
        self.imgPanel_.set_from_file(img_path)
        self.tags_.append([])
        self.current_img_ = len(self.imgPaths_) # select the new one
        self.imgPaths_.append(img_path)

    def show_image(self, n):
        """ show nth image """
        self.current_img_ = n
        self.imgPanel_.set_from_file(self.imgPaths_[self.current_img_])
        for tag in self.tags_[n]:
            self.draw_cross(tag[0], tag[1], CROSS_SIZE)
        for rect in self.labelledRects:
            self.draw_rect(rect.box)


    def resize(self, x, y):
        self.window_.resize(x,y)

    def add_tag(self, x, y):
        self.tags_[self.current_img_].append((x,y))
        self.draw_cross(x, y, CROSS_SIZE)

    def draw_cross(self, x, y, size):
        pixarr = self.imgPanel_.get_pixbuf().pixel_array
        max_w, max_h = len(pixarr), len(pixarr[0])
        col = [255, 0, 0, 255]
        for i in range(-size, size + 1):
            if x+i < max_w and x+i >= 0:
                if y + i < max_h and y+i >= 0:
                    pixarr[y+i][x+i] = col
                if y - i < max_h and y+i >= 0:
                    pixarr[y-i][x+i] = col
        self.imgPanel_.queue_draw()


