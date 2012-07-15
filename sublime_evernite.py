#coding:utf-8
import sys
sys.path.append("lib")

import hashlib
import binascii
import time
import thrift.protocol.TBinaryProtocol as TBinaryProtocol
import thrift.transport.THttpClient as THttpClient
import evernote.edam.userstore.UserStore as UserStore
import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.notestore.NoteStore as NoteStore
import evernote.edam.type.ttypes as Types
import evernote.edam.error.ttypes as Errors

# import sublime,sublime_plugin


consumer_key = 'jamiesun-2467'
consumer_secret ='7794453e92251986'
evernoteHost = "www.evernote.com"
userStoreUri = "https://" + evernoteHost + "/edam/user"

userStoreHttpClient = THttpClient.THttpClient(userStoreUri)
userStoreProtocol = TBinaryProtocol.TBinaryProtocol(userStoreHttpClient)
userStore = UserStore.Client(userStoreProtocol)

# versionOK = userStore.checkVersion("Evernote EDAMTest (Python)",
#                                    UserStoreConstants.EDAM_VERSION_MAJOR,
#                                    UserStoreConstants.EDAM_VERSION_MINOR)
# print "Is my Evernote API version up to date? ", str(versionOK)

authresult = userStore.authenticate('jamiesun','wjt594123',consumer_key,consumer_secret)

print authresult

noteStoreUrl = authresult.noteStoreUrl
authToken = authresult.authenticationToken

noteStoreHttpClient = THttpClient.THttpClient(noteStoreUrl)
noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)
noteStore = NoteStore.Client(noteStoreProtocol)

# List all of the notebooks in the user's account        
notebooks = noteStore.listNotebooks(authToken)
print "Found ", len(notebooks), " notebooks:"
for notebook in notebooks:
    print "  * ", notebook.name

# settings = sublime.load_settings("SublimeEvernote.sublime-settings")

# class SendToEvernote(sublime_plugin.TextCommand):
#     def __init__(self,view):
#         self.view = view    
#         self.token = None

#     def run(self, edit):
#         pass
        
        
