#coding:utf-8
import sys
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

    def connect(self,callback,**kwargs):
        sublime.status_message("authenticate..., please wait...")   
        def _connect(username,password):
            try:
                userStoreHttpClient = THttpClient.THttpClient(userStoreUri)
                userStoreProtocol = TBinaryProtocol.TBinaryProtocol(userStoreHttpClient)
                userStore = UserStore.Client(userStoreProtocol)
                authresult = userStore.authenticate(username,password,consumer_key,consumer_secret) 
                if authresult:
                   token = authresult.authenticationToken
                   noteStoreUrl = authresult.noteStoreUrl
                   if not settings.get("password") and sublime.ok_cancel_dialog("Remember password?"):
                       settings.set("password",password)  
                   settings.set("username",username)
                   settings.set("authToken",token)  
                   settings.set("noteStoreUrl",noteStoreUrl) 
                   sublime.save_settings('SublimeEvernote.sublime-settings')
                   sublime.status_message("authenticate ok")   
                   callback(**kwargs)
                else:
                    raise Exception("authenticate failure")
            except Exception,e:
                sublime.error_message("error:%s"%e)  

        def on_username(username):
            def on_passwd(password):
                if  username and  password:
                    _connect(username,password)
            self.window.show_input_panel("password (required)::","",on_passwd,None,None) 

        iusername = settings.get("username")
        ipassword = settings.get("password")
        if not iusername or not ipassword:
            self.window.show_input_panel("username (required)::","",on_username,None,None) 
        else:
            _connect(iusername,ipassword)        

    def send_note(self,**kwargs):
        authToken = settings.get("authToken")
        noteStoreUrl = settings.get('noteStoreUrl')
        noteStoreHttpClient = THttpClient.THttpClient(noteStoreUrl)
        noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)
        noteStore = NoteStore.Client(noteStoreProtocol)        
        region = sublime.Region(0L, self.view.size())
        content = self.view.substr(region)  

        def sendnote(title,tags):
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
                sublime.message_dialog("success") 
            except Errors.EDAMUserException,e:
                args = dict(title=title,tags=tags)
                if e.errorCode == 9:
                    self.connect(self.send_note,**args)
                else:
                    if sublime.ok_cancel_dialog('error %s! retry?'%e):
                        self.connect(self.send_note,**args)
            except  Exception,e:
                sublime.error_message('error %s'%e)

        def on_title(title):
            def on_tags(tags):
                sendnote(title,tags)
            self.window.show_input_panel("Tags (Optional)::","",on_tags,None,None) 

        if not  kwargs.get("title"):
            self.window.show_input_panel("Title (required)::","",on_title,None,None)
        else:
            sendnote(kwargs.get("title"),kwargs.get("tags")) 

    def run(self, edit):
        if not settings.get("authToken"):
            self.connect(self.send_note)
        else:
            self.send_note()