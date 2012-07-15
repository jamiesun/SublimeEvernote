#coding:utf-8
import sys
sys.path.append("lib")

import hashlib
import binascii
import time
from functools import wraps
import thrift.protocol.TBinaryProtocol as TBinaryProtocol
import thrift.transport.THttpClient as THttpClient
import evernote.edam.userstore.UserStore as UserStore
import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.notestore.NoteStore as NoteStore
import evernote.edam.type.ttypes as Types
import evernote.edam.error.ttypes as Errors

import sublime,sublime_plugin


consumer_key = 'jamiesun-2467'
consumer_secret ='7794453e92251986'
evernoteHost = "www.evernote.com"
userStoreUri = "https://" + evernoteHost + "/edam/user"




settings = sublime.load_settings("SublimeEvernote.sublime-settings")

def process_error(func):
    @wraps(func)
    def func_warp(*args,**kwargs):
        try:
            return func(*args,**kwargs)
        except Exception, e:
            sublime.error_message("error:%s"%e)  
    return func_warp

class SendToEvernoteCommand(sublime_plugin.TextCommand):
    def __init__(self,view):
        self.view = view    
        self.window = view.window()

    @process_error
    def connect(self):
        if settings.get("authToken"):
            return
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
                    else:
                        raise Exception("authenticate failure")
            self.window.show_input_panel("password (required)::","",on_passwd,None,None) 
        self.window.show_input_panel("username (required)::","",on_username,None,None)         

    def run(self, edit):
        self.connect()
        authToken = settings.get("authToken")
        noteStoreUrl = settings.get('noteStoreUrl')
        sublime.message_dialog(authToken+noteStoreUrl)  

        noteStoreHttpClient = THttpClient.THttpClient(noteStoreUrl)
        noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)
        noteStore = NoteStore.Client(noteStoreProtocol)

        # List all of the notebooks in the user's account        
        notebooks = noteStore.listNotebooks(authToken)
        print "Found ", len(notebooks), " notebooks:"
        for notebook in notebooks:
            print "  * ", notebook.name        


    