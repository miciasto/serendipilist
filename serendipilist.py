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

_version="0.2"

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
    label = Gtk.Label(f"Play random selection of tracks in the given proportions.")
    label.set_line_wrap(True)
    label.set_max_width_chars(20)
    return label

def boxRatings(eRatings):
        b1 = Gtk.HBox()
        b2 = Gtk.VBox()
        b2.pack_start(Gtk.Label(f"Rating:"), True, True, 0)
        b2.pack_start(Gtk.Label(f"Propn: "), True, True, 0)       
        b1.pack_start(b2, True, True, 0)
        for i in range(len(eRatings)):
            b2 = Gtk.VBox()
            label = Gtk.Label(f"{i}")
            label.set_alignment(0.2, 0.5)
            b2.pack_start(label, True, True, 0)
            e = eRatings[i]
            e.set_editable(1)
            e.set_max_width_chars(4)
            e.set_width_chars(4)
            e.set_text(f"{[0,0,0,1,5,5][i]}")
            b2.pack_start(e, True, True, 0)
            b1.pack_start(b2, True, True, 0)
        
        b3 = Gtk.VBox(True, 3)
        b3.add(b1)
        b3.add(b2)
        return b3

def boxCount(eCount):
    eCount.set_editable(1)
    eCount.set_max_width_chars(4)
    eCount.set_width_chars(4)
    eCount.set_text("20")
    
    hbox = Gtk.HBox(True, 3)
    hbox.add(Gtk.Label("Playlist length (# songs): "))
    hbox.add(eCount)
    return hbox

def comboPlaylist(default, listnames):
    combo = Gtk.ComboBoxText()
    combo.set_entry_text_column(0)
    for n in [default] + listnames:
        combo.append_text(n)
    combo.set_active(0)
    return combo

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

    def list_playlists(self):
        shell = self.object
        pl_man = shell.props.playlist_manager
        pl_lists = pl_man.get_playlists()
        pl_count = len(pl_lists)
        pl_names = []
        for playlist in pl_lists:
            pl_names.append(playlist.props.name)
            # if isinstance(playlist, RB.StaticPlaylistSource):
            #     pl_names.append(playlist.props.name)
        return pl_names
    
    def get_playlist(self, name):
        if name=="All" or name=="":
            return None
        shell = self.object
        pl_man = shell.props.playlist_manager
        pl_lists = pl_man.get_playlists()
        for playlist in pl_lists:
            if playlist.props.name==name:
                return playlist
        return None
    
    def CreateGuiGetInfo(self):
        print("CreateGuiGetInfo")
        dialog = Gtk.Dialog(
            "Serendipilist Generator", None, 0, (
                Gtk.STOCK_OK, Gtk.ResponseType.YES,
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL
            ))
        
        eRatings = [Gtk.Entry() for i in range(NRATINGS)]
        eCount = Gtk.Entry()
        eInlist = comboPlaylist("All", self.list_playlists())
        eExlist = comboPlaylist("", self.list_playlists())

        hbox1 = Gtk.HBox(True, 3)
        hbox1.add(Gtk.Label("In: ", xalign=0))
        hbox1.add(eInlist)
        hbox2 = Gtk.HBox(True, 3)
        hbox2.add(Gtk.Label("Not in: ", xalign=0))
        hbox2.add(eExlist)
        
        dialog.vbox.pack_start(labelDesc(), True, True, 15)
        label = Gtk.Label("Playback proportion by star rating", xalign=0)
        dialog.vbox.pack_start(label, True, True, 5)
        dialog.vbox.pack_start(boxRatings(eRatings), True, True, 0)
        dialog.vbox.pack_start(hbox1, True, True, 0)
        dialog.vbox.pack_start(hbox2, True, True, 0)        
        dialog.vbox.pack_start(boxCount(eCount), True, True, 0)
        label = Gtk.Label(f"Serendipilist plugin version {_version}", xalign=1)
        dialog.vbox.pack_start(label, True, True, 15)
        dialog.show_all()
                          
        response = dialog.run()
        ratings = [txt_to_int(eRatings[i].get_text()) for i in range(len(eRatings))]
        count = txt_to_int(eCount.get_text())
        inlist = eInlist.get_active_text()
        exlist = eExlist.get_active_text()
        dialog.destroy()
        
        while Gtk.events_pending():
            Gtk.main_iteration()
        
        return ([], 0, "All", "") if response == Gtk.ResponseType.CANCEL else (ratings, count, inlist, exlist)
    
    def serendipilist(self, *args):
        (reqRatings, reqCount, inlistname, exlistname) = self.CreateGuiGetInfo()
        if reqCount==0:
            return
        reqRatings = normalise_ratings(reqRatings)
        tracklist = {i:[] for i in range(NRATINGS)}
        inlist = self.get_playlist(inlistname)
        exlist = self.get_playlist(exlistname)
        qmi = self.shell.props.library_source.props.base_query_model if inlist is None else inlist.props.query_model
        qmx = None if exlist is None else exlist.props.query_model
        inentries = [row[0] for row in qmi]
        exentries = [row[0] for row in qmx] if qmx is not None else None
        for entry in inentries:
            rating = min(int(entry.get_double(RB.RhythmDBPropType.RATING)),5)
            if exentries is not None and entry in exentries:
                continue
            tracklist[rating].append(entry)
        
        ratings = random.choices([i for i in range(len(reqRatings))], weights=reqRatings, k=reqCount)
        selections = [random.choice(tracklist[r]) for r in ratings if len(tracklist[r])>0]
        
        self.ClearQueue()
        self.addTracksToQueue(selections)
        self.shell.props.shell_player.stop()
        self.shell.props.shell_player.set_playing_source( self.shell.props.queue_source )
        self.shell.props.shell_player.playpause()
