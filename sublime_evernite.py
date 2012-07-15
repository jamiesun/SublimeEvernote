#coding:utf-8
import sys
reload(sys)
sys.path.append("lib")

import thrift.protocol.TBinaryProtocol as TBinaryProtocol
import thrift.transport.THttpClient as THttpClient
import evernote.edam.userstore.UserStore as UserStore
import evernote.edam.notestore.NoteStore as NoteStore
import evernote.edam.type.ttypes as Types
import evernote.edam.error.ttypes as Errors
from html import XHTML
import sublime,sublime_plugin

consumer_key = 'jamiesun-2467'
consumer_secret ='7794453e92251986'
evernoteHost = "www.evernote.com"
userStoreUri = "https://" + evernoteHost + "/edam/user"

settings = sublime.load_settings("SublimeEvernote.sublime-settings")

class SendToEvernoteCommand(sublime_plugin.TextCommand):
    def __init__(self,view):
        self.view = view    
        self.window = sublime.active_window()

    def connect(self,callback):
        try:
            def on_username(username):
                def on_passwd(password):
                    if  username and  password:
                        userStoreHttpClient = THttpClient.THttpClient(userStoreUri)
                        userStoreProtocol = TBinaryProtocol.TBinaryProtocol(userStoreHttpClient)
                        userStore = UserStore.Client(userStoreProtocol)
                        authresult = userStore.authenticate(username,password,consumer_key,consumer_secret) 
                        if authresult:
                           token = authresult.authenticationToken
                           noteStoreUrl = authresult.noteStoreUrl
                           settings.set("authToken",token)  
                           settings.set("noteStoreUrl",noteStoreUrl) 
                           sublime.save_settings('SublimeEvernote.sublime-settings')
                           callback()
                        else:
                            raise Exception("authenticate failure")
                self.window.show_input_panel("password (required)::","",on_passwd,None,None) 
            self.window.show_input_panel("username (required)::","",on_username,None,None) 
        except Exception,e:
            sublime.error_message("error:%s"%e)  

    def send_note(self):
        authToken = settings.get("authToken")
        noteStoreUrl = settings.get('noteStoreUrl')
        noteStoreHttpClient = THttpClient.THttpClient(noteStoreUrl)
        noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)
        noteStore = NoteStore.Client(noteStoreProtocol)        
        region = sublime.Region(0L, self.view.size())
        content = self.view.substr(region)        
        def on_title(title):
            def on_tags(tags):
                xh =  XHTML()
                note = Types.Note()
                note.title = title.encode('utf-8')
                note.content = '<?xml version="1.0" encoding="UTF-8"?>'
                note.content += '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
                note.content += '<en-note><pre>%s'%xh.p(content.encode('utf-8'))
                note.content += '</pre></en-note>'
                note.tagNames = tags and tags.split(",") or []
                try:
                    sublime.status_message("please wait...")   
                    cnote = noteStore.createNote(authToken, note)   
                    sublime.status_message("send success guid:%s"%cnote.guid)   
                except Errors.EDAMUserException,e:
                    if e.errorCode == 9:
                        self.connect(self.send_note)
                    else:
                        sublime.error_message('error %s'%e)
                except  Exception,e:
                    sublime.error_message('error %s'%e)
            self.window.show_input_panel("Tags (Optional)::","",on_tags,None,None) 

        self.window.show_input_panel("Title (required)::","",on_title,None,None) 

    def run(self, edit):
        if not settings.get("authToken"):
            self.connect(self.send_note)
        else:
            self.send_note()