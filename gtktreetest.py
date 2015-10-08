import pygtk
pygtk.require('2.0')

import gtk
from gtk import TRUE, FALSE
import gobject

TOGGLE_WIDTH = 12

class MyCellRenderer(gtk.GenericCellRenderer):
    def __init__(self):
        self.__gobject_init__()
        self.xpad = -2; self.ypad = -2
        self.xalign = 0.5; self.yalign = 0.5
        self.active = 0

    def on_render(self, window, widget, background_area,cell_area, expose_area, flags):

        x_offset, y_offset, width, height = self.on_get_size(widget, cell_area)
        width -= self.xpad*2
        height -= self.ypad*2

#        if width <= 0 or height <= 0:
#            return

        widget.style.paint_check(window,
                gtk.STATE_ACTIVE, gtk.SHADOW_IN, 
                cell_area, widget, "cellradio",
                cell_area.x + x_offset + self.xpad,
                cell_area.y + y_offset + self.ypad,


    def on_get_size(self, widget, cell_area):
        calc_width = self.xpad * 2 + TOGGLE_WIDTH
        calc_height = self.ypad * 2 + TOGGLE_WIDTH

        if cell_area:
            x_offset = self.xalign * (cell_area.width - calc_width)
            x_offset = max(x_offset, 0)
            y_offset = self.yalign * (cell_area.height - calc_height)
            y_offset = max(y_offset, 0)            
        else:
            x_offset = 0
            y_offset = 0

        return calc_width, calc_height, x_offset, y_offset

gobject.type_register(MyCellRenderer)

class Tree(gtk.TreeView):
    def __init__(self):
        self.store = gtk.ListStore(gobject.TYPE_STRING,
                gobject.TYPE_PYOBJECT)
        gtk.TreeView.__init__(self)
        self.set_size_request(300, 200)
        self.set_model(self.store)
        self.set_headers_visible(TRUE)
        rend = gtk.CellRendererText()
        column = gtk.TreeViewColumn('First', rend, text=0)
        self.append_column(column)

        rend = MyCellRenderer()
        column = gtk.TreeViewColumn('Second', rend)
        self.append_column(column)        

    def insert(self, name):
        iter = self.store.append()
        self.store.set(iter,
                0, name)

w = gtk.Window()
w.set_position(gtk.WIN_POS_CENTER)
w.connect('delete-event', gtk.mainquit)
t = Tree()
t.insert('foo')
t.insert('bar')
t.insert('baz')
w.add(t)

w.show_all()
gtk.main()
