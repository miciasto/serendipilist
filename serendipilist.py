# Serendipilist Rhythmbox Plugin

# Copyright miciasto <miciasto@gmx.com> 2025
# This is a derivative of the same software name originally created by
# Larry Price <larry.price.dev@gmail.com>, 2011-2012
# This program is free software: you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import RB, Gtk, GObject, Peas
import random, string, copy, os
from serendipilist_rb3compat import ActionGroup
from serendipilist_rb3compat import Action
from serendipilist_rb3compat import ApplicationShell

_version="0.1"

ui_string = \
"""<ui>
    <menubar name="MenuBar">
        <menu name="ControlMenu" action="Control">
            <menuitem name="Serendipilist" action="Serendipilist"/>
        </menu>
    </menubar>
</ui>"""

NRATINGS=6

def txt_to_int(txt, default=0):
    return abs(int(txt)) if txt.isdigit() else default

def normalise_ratings(ratings):
    total = sum(ratings)
    return [1,0,0,0,0,0] if total == 0 else [r/total for r in ratings]

def labelDesc():
    label = Gtk.Label(f"Adds a random selection of tracks to the play queue, selecting tracks from each rating level in the selected proportions.")
    label.set_line_wrap(True)
    label.set_max_width_chars(20)
    return label

def boxRatings(eRatings):
        vb1 = Gtk.VBox()
        vb2 = Gtk.VBox()
        for i in range(len(eRatings)):
            vb1.pack_start(Gtk.Label(f"Rating {i}: "), True, True, 0)
            e = eRatings[i]
            e.set_editable(1)
            e.set_max_width_chars(4)
            e.set_width_chars(4)
            e.set_text(f"{[0,0,0,1,5,5][i]}")
            vb2.pack_start(e, True, True, 0)
        
        hbox = Gtk.HBox(True, 3)
        hbox.add(vb1)
        hbox.add(vb2)
        return hbox

def boxCount(eCount):
    eCount.set_editable(1)
    eCount.set_max_width_chars(4)
    eCount.set_width_chars(4)
    eCount.set_text("20")
    
    hbox = Gtk.HBox(True, 3)
    hbox.add(Gtk.Label("Playlist length (number of songs): "))
    hbox.add(eCount)
    return hbox

class Serendipilist (GObject.GObject, Peas.Activatable):
    __gtype_name = 'SerendipilistPlugin'
    object = GObject.property(type=GObject.GObject)

    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        self.shell = self.object
        self.sp = self.shell.props.shell_player
        
        self.action_group = ActionGroup(self.shell, 'SerendipilistActionGroup')
        action = self.action_group.add_action(
            func=self.serendipilist,
            action_name='Serendipilist',
            label='Serendipilist Playlist',
            action_type='app')

        self._appshell = ApplicationShell(self.shell)
        self._appshell.insert_action_group(self.action_group)
        self._appshell.add_app_menuitems(ui_string, 'SerendipilistActionGroup')
        
    def do_deactivate(self):
        self._appshell.cleanup()
    
    def addTracksToQueue(self, theList):
        for track in theList:
            self.shell.props.queue_source.add_entry(track, -1)
        
    def ClearQueue(self):
        for row in self.shell.props.queue_source.props.query_model:
            entry = row[0]
            self.shell.props.queue_source.remove_entry(entry)
    
    def CreateGuiGetInfo(self):
        print("CreateGuiGetInfo")
        dialog = Gtk.Dialog(
            "Serendipilist Configuration", None, 0, (
                Gtk.STOCK_OK, Gtk.ResponseType.YES,
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL
            ))
        
        eRatings = [Gtk.Entry() for i in range(NRATINGS)]
        eCount = Gtk.Entry()

        dialog.vbox.pack_start(labelDesc(), True, True, 15)
        dialog.vbox.pack_start(Gtk.Label("Playback proportion by song rating level"), True, True, 5)
        dialog.vbox.pack_start(boxRatings(eRatings), True, True, 0)
        dialog.vbox.pack_start(boxCount(eCount), True, True, 0)
        dialog.vbox.pack_start(Gtk.Label(f"Serendipilist plugin version {_version}"), True, True, 15)
        dialog.show_all()
                          
        response = dialog.run()
        ratings = [txt_to_int(eRatings[i].get_text()) for i in range(len(eRatings))]
        count = txt_to_int(eCount.get_text())
        dialog.destroy()
        
        while Gtk.events_pending():
            Gtk.main_iteration()
        
        return ([], 0) if response == Gtk.ResponseType.CANCEL else (ratings, count)
    
    def serendipilist(self, *args):
        (reqRatings, reqCount) = self.CreateGuiGetInfo()
        if reqCount==0:
            return
        reqRatings = normalise_ratings(reqRatings)
        
        tracklist = {i:[] for i in range(NRATINGS)}
        for row in self.shell.props.library_source.props.base_query_model:
            entry = row[0]
            rating = min(int(entry.get_double(RB.RhythmDBPropType.RATING)),5)
            tracklist[rating].append(entry)
        
        ratings = random.choices([i for i in range(len(reqRatings))], weights=reqRatings, k=reqCount)
        selections = [random.choice(tracklist[r]) for r in ratings]
        
        self.ClearQueue()
        self.addTracksToQueue(selections)
        self.shell.props.shell_player.stop()
        self.shell.props.shell_player.set_playing_source( self.shell.props.queue_source )
        self.shell.props.shell_player.playpause()
