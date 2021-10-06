'''The module containing the evacuation management system, used for ingest, etc.'''

import tkinter as tk
from tkinter import ttk

import mods.log as ml
import mods.database as md
import mods.widgets as mw
import mods.dehc_hardware as hw
# ----------------------------------------------------------------------------

class EMS():
    '''A class which represents the EMS application.
    
    bookmarks: Relative filepath to the bookmark definition file.
    cats: The categories which can be searched and created on the EMS screen.
    flags: The flags which can be assigned on the EMS screen.
    db: The database object which the app uses for database transactions.
    logger: The logger object used for logging.
    root: The root of the application, a tk.Tk object.
    '''

    def __init__(self, db: md.DEHCDatabase, *, bookmarks: str = "bookmarks.json", level: str = "NOTSET", autorun: bool = False, hardware: hw.Hardware = None):
        '''Constructs an EMS object.
        
        db: The database object which the app uses for database transactions.
        bookmarks: Relative filepath to the bookmark definition file.
        level: Minimum level of logging messages to report; "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "NONE".
        prepare: If true, automatically prepares widgets for packing.
        '''
        self.bookmarks = bookmarks
        self.level = level
        self.logger = ml.get("EMS", level=self.level)
        self.logger.debug("EMS object instantiated")

        self.hardware = hardware

        self.db = db
        self.cats = self.db.schema_cats()

        self.root = tk.Tk()
        self.root.title(f"EMS ({self.db.db.data['url']})")
        self.root.state('zoomed')
        self.root.configure(background="#D9D9D9")

        self.style = ttk.Style(self.root)
        self.style.theme_use("clam")
        self.style.map('TEntry', foreground=[('readonly', 'black')])
        self.style.map('TCombobox', fieldbackground=[('readonly', 'white')])
        self.style.configure("top.Treeview", fieldbackground="white", background="white", foreground="black")
        self.style.map('top.Treeview', background=[('selected', 'blue')], foreground=[('selected', 'white')])
        self.style.configure("bottom.Treeview", fieldbackground="#fcf0cf", background="#fcf0cf", foreground="black")
        self.style.map('bottom.Treeview', background=[('selected', 'blue')], foreground=[('selected', '#fcf0cf')])
        

        if autorun == True:
            self.prepare()
            self.pack()
            self.run()


    def prepare(self):
        '''Constructs the frames and widgets of the EMS.'''
        base, *_ = self.db.items_query(cat="Evacuation", fields=["_id", "Display Name"])
        self.cm = mw.ContainerManager(master=self.root, db=self.db, topbase=base, botbase=base, bookmarks=self.bookmarks, cats=self.cats, level=self.level, prepare=True, select=self.item_select)
        self.de = mw.DataEntry(master=self.root, db=self.db, cats=self.cats, delete=self.delete, level=self.level, newchild=self.newchild, prepare=True, save=self.save, show=self.show, hardware=self.hardware)
        self.bu_refresh = ttk.Button(master=self.root, text="Refresh", command=self.refresh)
        self.sb = mw.StatusBar(master=self.root, db=self.db, level=self.level, prepare=True)
        self.root.rowconfigure(0, weight=1000)
        self.root.rowconfigure(1, weight=1, minsize=16)
        self.root.columnconfigure(0, weight=1, minsize=48)
        self.root.columnconfigure(1, weight=1000)


    def newchild(self, target: str):
        '''Callback for when new child is pressed in the data pane.'''
        parent = self.cm.w_se_top.w_tr_tree.parent(target)
        if parent == "":
            self.cm.w_se_top.tree_rebase(target=target)
            parent = self.cm.w_se_top.w_tr_tree.parent(target)
        self.cm.highlight(item=parent)


    def pack(self):
        '''Packs & grids children frames and widgets of the EMS.'''
        self.cm.grid(column=0, row=0, columnspan=2, sticky="nsew", padx=2, pady=2)
        self.de.grid(column=2, row=0, sticky="nsew", padx=2, pady=2)
        self.bu_refresh.grid(column=0, row=1, sticky="nsew", padx=2, pady=2)
        self.sb.grid(column=1, row=1, columnspan=2, sticky="nsew", padx=2, pady=2)


    def refresh(self):
        '''Refreshes the trees and data pane.'''
        self.cm.refresh()


    def run(self):
        '''Enters the root's main loop, drawing the app screen.'''
        self.root.mainloop()


    def item_select(self, *args):
        '''Callback for when an item is selected on the top tree.'''
        doc, = args
        self.de.show(doc)


    def delete(self, *args):
        '''Callback for when the delete button is pressed in the data pane.'''
        id, parents, *_ = args
        if len(parents) > 0:
            parent, *_ = parents
            if id == self.cm.base()["_id"]:
                self.cm.base(newbase=self.db.item_get(id=parent, fields=["_id", "Display Name"]))
            self.cm.refresh()
            self.cm.highlight(item=parent)
            self.cm.open()
        else:
            self.cm.refresh()


    def save(self, *args):
        '''Callback for when the save button is pressed in the data pane.'''
        id, *_ = args
        if id != None:
            container, *_ = self.cm.selections()
            self.db.container_add(container=container, item=id)
        self.cm.refresh()
        if id != None:
            self.cm.highlight(item=container)
            self.cm.open()


    def show(self, *args):
        '''Callback for when the show button is pressed in the data pane.'''
        id, *_ = args
        if id != None:
            self.cm.refresh()
            self.cm.highlight(item=id)


    def __del__(self):
        '''Runs when EMS object is deleted.'''
        self.logger.debug("EMS object destroyed")
    


# ----------------------------------------------------------------------------