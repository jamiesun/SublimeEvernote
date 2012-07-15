#coding:utf-8
import sys
sys.path.append("lib")
import os
import tempfile
import thrift.protocol.TBinaryProtocol as TBinaryProtocol
import thrift.transport.THttpClient as THttpClient
import evernote.edam.userstore.UserStore as UserStore
import evernote.edam.notestore.NoteStore as NoteStore
import evernote.edam.type.ttypes as Types
from markupsafe import escape
import sublime,sublime_plugin

consumer_key = 'jamiesun-2467'
consumer_secret ='7794453e92251986'
evernoteHost = "www.evernote.com"
userStoreUri = "https://" + evernoteHost + "/edam/user"

LANGUAGES = {
    'c': 'clike',
    'cc': 'clike',
    'cpp': 'clike',
    'cs': 'clike',
    'coffee': 'coffeescript',
    'css': 'css',
    'diff': 'diff',
    'go': 'go',
    'html': 'htmlmixed',
    'htm': 'htmlmixed',
    'js': 'javascript',
    'json': 'javascript',
    'less': 'less',
    'lua': 'lua',
    'md': 'markdown',
    'markdown': 'markdown',
    'pl': 'perl',
    'php': 'php',
    'py': 'python',
    'pl': 'perl',
    'rb': 'ruby',
    'xml': 'xml',
    'xsl': 'xml',
    'xslt': 'xml'
}

DEPENDENCIES = {
    'php': ['xml', 'javascript', 'css', 'clike'],
    'markdown': ['xml'],
    'htmlmixed': ['xml', 'javascript', 'css']
}

settings = sublime.load_settings("SublimeEvernote.sublime-settings")

def to_html(contents,language,encoding='utf-8'):
    contents = contents.replace('<', '&lt;').replace('>', '&gt;')
    tmp_html = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
    tmp_html.write('<meta charset="%s">' % encoding)
    # package manager path
    plugin_dir = os.path.join(sublime.packages_path(), 'SublimeEvernote')
    js = open(os.path.join(plugin_dir, 'codemirror', 'lib', 'codemirror.js'), 'r').read()
    if language:
        for dependency in DEPENDENCIES.get(language, []):
            js += open(os.path.join(plugin_dir, 'codemirror', 'mode', dependency, '%s.js' % dependency), 'r').read()
        js += open(os.path.join(plugin_dir, 'codemirror', 'mode', language, '%s.js' % language), 'r').read()
    css = open(os.path.join(plugin_dir, 'codemirror', 'lib', 'codemirror.css'), 'r').read()

    datas = {
         'css': css,
         'js': js,
         'code': contents,
         'mode': language
    }
    # theme
    # <link rel="stylesheet" href="../theme/elegant.css">
    html = u"""
        <!doctype html>
        <html>
          <head>
            <script>%(js)s</script>
            <style>%(css)s</style>
            <style>.CodeMirror-scroll {height: auto; overflow: visible;}</style>
          </head>
          <body>
            <h3>%(title)s</h3>
            <textarea id="code" name="code">%(code)s</textarea>
            <script>
            var editor = CodeMirror.fromTextArea(document.getElementById("code"), {
                lineNumbers: true,
                mode: "%(mode)s"
            });
            </script>
          </body>
        </html>
    """ % datas
    return html

class SendToEvernoteCommand(sublime_plugin.TextCommand):
    def __init__(self,view):
        self.view = view    
        self.window = view.window()

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
        try:
            authToken = settings.get("authToken")
            noteStoreUrl = settings.get('noteStoreUrl')
            noteStoreHttpClient = THttpClient.THttpClient(noteStoreUrl)
            noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)
            noteStore = NoteStore.Client(noteStoreProtocol)        
            region = sublime.Region(0L, self.view.size())
            content = self.view.substr(region)    
              
            filename = self.view.file_name()
            language = None
            if filename:
                fileext = os.path.splitext(filename)[1][1:]
                language = LANGUAGES.get(fileext.lower())
                
            content = to_html(content,language)  

            def on_title(title):
                note = Types.Note()
                note.title = title
                note.content = '<?xml version="1.0" encoding="UTF-8"?>'
                note.content += '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
                note.content += '<en-note><pre>%s'%escape(content)
                note.content += '</pre></en-note>'
                
                # Finally, send the new note to Evernote using the createNote method
                # The new Note object that is returned will contain server-generated
                # attributes such as the new note's unique GUID.
                try:
                    cnote = noteStore.createNote(authToken, note)   
                    sublime.message_dialog("send success %s"%cnote.guid)   
                except  Exception,e:
                    sublime.error_message('error %s'%e)

                   
            self.window.show_input_panel("Title (required)::","",on_title,None,None) 
        except Exception,e:
            sublime.error_message("error:%s"%e)  

    def run(self, edit):
        if not settings.get("authToken"):
            self.connect(self.send_note)
        else:
            self.send_note()