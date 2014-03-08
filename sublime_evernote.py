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
import oauth2 as oauth
import urllib
import urlparse
import markdown2

consumer_key = 'oparrish-4096'
consumer_secret ='c112c6417738f06a'
evernoteHost = "www.evernote.com"
userStoreUri = "https://" + evernoteHost + "/edam/user"
temp_credential_request_uri = "https://" + evernoteHost + "/oauth"
resource_owner_authorization_uri = "https://" + evernoteHost + "/OAuth.action"
token_request_uri = "https://" + evernoteHost + "/oauth"

settings = sublime.load_settings("SublimeEvernote.sublime-settings")

class SendToEvernoteCommand(sublime_plugin.TextCommand):
    def __init__(self,view):
        self.view = view    
        self.window = sublime.active_window()

    def to_markdown_html(self):
        region = sublime.Region(0, self.view.size())
        encoding = self.view.encoding()
        if encoding == 'Undefined':
            encoding = 'utf-8'
        elif encoding == 'Western (Windows 1252)':
            encoding = 'windows-1252'
        contents = self.view.substr(region)

        markdown_html = markdown2.markdown(contents, extras=['footnotes', 'fenced-code-blocks', 'cuddled-lists', 'code-friendly', 'metadata'])

        return markdown_html

    def connect(self,callback,**kwargs):
        sublime.status_message("authenticate..., please wait...")   
        
        def _connect(authToken):
            try:
                callback(**kwargs)
            except Exception as e:
                sublime.error_message("error:%s"%e)  

        def on_verifier(verifier):
            if verifier:
                token = oauth.Token(request_token['oauth_token'],request_token['oauth_token_secret']) 
                token.set_verifier(verifier)
                            
                client = oauth.Client(consumer, token)
                resp, content = client.request(token_request_uri, "POST")
                
                access_token = dict(urlparse.parse_qsl(content))
                
                if access_token:
                   settings.set("oauth_token",access_token['oauth_token']) 
                   settings.set("noteStoreUrl",access_token['edam_noteStoreUrl'])
                   sublime.save_settings('SublimeEvernote.sublime-settings') 
                   sublime.status_message("authenticate ok")
                   _connect(access_token['oauth_token'])
                else:
                    raise Exception("authenticate failure")
            else:
                self.window.show_input_panel("Paste the verifier string from from the URL here.  Verifier (required):","",on_verifier,None,None)

        i_auth_token = settings.get("oauth_token")
        i_note_store_url = settings.get("noteStoreUrl")
        
        consumer = None
        request_token = None
        
        if not i_auth_token or not i_note_store_url:
            consumer = oauth.Consumer(key=consumer_key , secret=consumer_secret)
            client = oauth.Client(consumer)

            # Make the request for the temporary credentials (Request Token)
            callback_url = 'http://127.0.0.1'
            request_url = '%s?oauth_callback=%s' % (temp_credential_request_uri,
                urllib.quote(callback_url))

            resp, content = client.request(request_url, "GET")
            print content
            if resp['status'] != '200':
                raise Exception("Invalid response %s." % resp['status'])

            request_token = dict(urlparse.parse_qsl(content))

            authorization_url = '%s?oauth_token=%s' % (resource_owner_authorization_uri, request_token['oauth_token'])

            def on_authorization_url(authorization_url):
                self.window.show_input_panel("Paste the verifier string from from the URL here.  Verifier (required):","",on_verifier,None,None)

            self.window.show_input_panel("Cut and paste this URL into a browswer to authorize SublimeEvernote to access your Evernote account.  After authorizing, press enter.",authorization_url,on_authorization_url,None,None) 
        else:
            self.send_note(**kwargs)        

    def send_note(self,**kwargs):
        authToken = settings.get("oauth_token")
        noteStoreUrl = settings.get('noteStoreUrl')

        noteStoreHttpClient = THttpClient.THttpClient(noteStoreUrl)
        noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)
        noteStore = NoteStore.Client(noteStoreProtocol)        
        region = sublime.Region(0L, self.view.size())
        content = self.view.substr(region)  

        markdown_html = self.to_markdown_html()

        def sendnote(title,tags):
            xh =  XHTML()
            note = Types.Note()
            note.title = title.encode('utf-8')
            note.content = '<?xml version="1.0" encoding="UTF-8"?>'
            note.content += '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
            note.content += '<en-note>%s'%markdown_html.encode('utf-8')
            note.content += '</en-note>'
            note.tagNames = tags and tags.split(",") or []
            try:
                sublime.status_message("please wait...")   
                cnote = noteStore.createNote(authToken, note)   
                sublime.status_message("send success guid:%s"%cnote.guid)  
                sublime.message_dialog("success") 
            except Errors.EDAMUserException as e:
                args = dict(title=title,tags=tags)
                if e.errorCode == 9:
                    self.connect(self.send_note,**args)
                else:
                    if sublime.ok_cancel_dialog('error %s! retry?'%e):
                        self.connect(self.send_note,**args)
            except  Exception as e:
                sublime.error_message('error %s'%e)

        def on_title(title):
            def on_tags(tags):
                sendnote(title,tags)
            if not 'tags' in markdown_html.metadata:
                self.window.show_input_panel("Tags (Optional)::","",on_tags,None,None) 
            else:
                sendnote(title, markdown_html.metadata['tags'])

        if not(kwargs.get("title") or 'title' in markdown_html.metadata):
            self.window.show_input_panel("Title (required)::","",on_title,None,None)
        elif not kwargs.get("tags"):
            on_title(markdown_html.metadata['title'])
        else:    
            sendnote(kwargs.get("title"),kwargs.get("tags")) 

    def run(self, edit):
        if not settings.get("oauth_token") and not settings.get("noteStoreUrl"):
            self.connect(self.send_note)
        else:
            self.send_note()
