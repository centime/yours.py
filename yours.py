#!/usr/bin/python2

#import string,cgi,time
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from urlparse import urlparse
import os
import datetime
import cgi

port = 3333    
cwd = os.path.abspath('.')


PAGE_TEMPLATE = '''
    <html>
        <head>
            <style>%s
            </style>
        </head>
        <body>
            <div class='pure-menu pure-menu-open'>%s
            </div>
        </body>
    </html>
    '''     
STYLE = open(os.path.join(os.path.dirname(os.path.realpath(__file__)),'pure-min.css')).read()+'''
    
    .size{
        float:right;
    }
    .mtime{
        float:right;
    }
    .subdir{
        font-weight : bold;
    }
    .pure-menu a, .pure-menu .pure-menu-heading{
        white-space:normal;
    }
    #current_path{
        text-transform:none;
        font-size:20;
    }

    '''


UPLOAD_TEPMPLATE = '''
                                <form id='upload_form' method='POST' enctype='multipart/form-data' style='position:absolute; top:-100px;'>
                                    <input type='file' id='upload_files' name='upload_files' multiple/>
                                </form>
                                <script>
                                    function browseFiles(){
                                        document.getElementById('files_to_upload').value = '';
                                        document.getElementById('upload_files').click();
                                    }
                                    function confirmUpload(){
                                        document.forms['upload_form'].submit();
                                        document.getElementById('upload_control').style.display='none';
                                    }
                                    function cancelUpload(){
                                       document.getElementById('upload_files').files=[];
                                       document.getElementById('upload_control').style.display='none';
                                    }
                                    document.getElementById('upload_files').onchange = function () {
                                        document.getElementById('files_to_upload').value = '' ;
                                        if (this.files.length > 0) {
                                            document.getElementById('upload_control').style.display='inline';
                                        }
                                        for (i=0;i<this.files.length;i++) document.getElementById('files_to_upload').value += this.files[i].name+', ';
                                    };
                                </script>
                                <button class='pure-button' onClick='browseFiles()'>Upload from hard drive</button>
                                <span id='upload_control' style='display:none;'>
                                    <input id='files_to_upload' readonly></input>
                                    <button class='pure-button' onClick='confirmUpload()'>Ok</button>
                                    <button class='pure-button' onClick='cancelUpload()'>Cancel</button>
                                </span>
    '''

DIR_TEMPLATE = '''
                <div class='pure-menu-heading'>
                    <a id='current_path'>%s</a>
                    <div class='pure-menu pure-menu-horizontal pure-menu-open'>
                        <ul>
                            <li><!-- parent directory --> <a href='%s' class='pure-button'> < </a></li>
                            <li><!-- upload --> %s
                            </li>
                        </ul>
                    </div>
                </div>
                <ul>
                    <a class="pure-menu-heading">
                        <span class='name'>[ name ]</span>
                        <span class='size'>[ size ]</span>
                        <!--<span class='mtime'>[ last modified ]</span>-->
                    </a>
                    <!-- directories and files --> %s
                </ul>
    '''

SUBDIR_TEMPLATE = '''
                    <li><a href='%s'> 
                        <span class='subdir'>%s</span>
                        <span class='size inner_elements'>%s</span> 
                        <!--<span class='mtime'>%s</span>-->
                    </a></li>
    '''

FILE_TEMPLATE = '''
                    <li><a href='%s'>
                        %s 
                        <span class='size'>%s</span> 
                        <!--<span class='mtime'>%s</span>-->
                    </a></li>
    '''

def render(path, subdirs, files):  
    subdirs = ''.join([ (SUBDIR_TEMPLATE % (path+'/'+d['name'], d['name'], d['inner_elements'], d['mtime'] )) for d in subdirs ])
    #subdirs = ''.join([ (SUBDIR_TEMPLATE % (path, d['name'], d['mtime'] )) for d in subdirs ])
    files = ''.join([ (FILE_TEMPLATE % (path+'/'+f['name'], f['name'], f['size'], f['mtime'] )) for f in files ])
    
    directory = DIR_TEMPLATE % (path, path+'/..', UPLOAD_TEPMPLATE, subdirs+files)
    page = PAGE_TEMPLATE % ( STYLE, directory )
    return page

def sizeof(num):
    for x in ['bytes','KB','MB','GB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')

class YoursHandler(BaseHTTPRequestHandler):
    def path_from_url(self) :
         # get path from url
        p=''
        for s in self.path.split('/') :
            p= os.path.join(p, s)
        return os.path.join(cwd, p)       

    def do_GET(self):
        try:
            path = self.path_from_url()
            
            if not os.path.exists(path) :
                # Not a file nor a dir
                self.send_error(404,'%s does not exist' % self.path)

            elif os.path.isdir(path) :
                # Is a dir : render it's content
                self.send_page(path)

            elif os.path.isfile(path) :
                # Is a file : start download
                f = open( path, 'rb' ) 
                self.send_response(200)
                self.send_header('Content-type','application/octet-stream')
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
            return
            
        except IOError as e :     
            print e
            self.send_error(404,'%s does not exist' % self.path)

    def do_POST(self):
        try:
            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))     

            if ctype == 'multipart/form-data' :     
                field_storage = cgi.FieldStorage( fp = self.rfile, headers = self.headers, environ={ 'REQUEST_METHOD':'POST' } )

            else: raise Exception("Unexpected POST request")
            
            if type(field_storage['upload_files']) == type([]):
                files = field_storage['upload_files']
            else :
                files = [field_storage['upload_files']]

            for file_in in files :
                name = os.path.split(file_in.filename)[1]
                path = self.path_from_url()
                file_out = os.path.join(path, name)

                # 'version control'
                if os.path.exists( file_out ):
                    # FIX IT (windows ?)
                    versions_dir =  cwd+'/.yours_versions.'+path.split(cwd)[1]
                    if not os.path.exists(versions_dir):
                        os.makedirs(versions_dir) 
                    i = 0
                    f = os.path.join(versions_dir, name)
                    file_backup = f+'.v0'
                    while os.path.exists( file_backup ):
                        file_backup = "%s.v%d" % (f, i)
                        i+=1
                    os.rename(file_out, file_backup)

                if not os.path.exists(file_out):
                    with open(file_out, 'wb') as o:
                        # self.copyfile(fs['upfile'].file, o)
                        o.write( file_in.file.read() )     

                #ups+=[os.path.split(fullname)[1]]

            #print ups
            self.send_page(path)

        except Exception as e:
            print e
            self.send_error(404,'POST to "%s" failed: %s' % (self.path, str(e)) )

    def url_from_path(self, path):

        rel_path = path.split(cwd)[1]
        identifiers = [ i for i in rel_path.split('/') if i != '' ]
        if len(identifiers)  > 0 :
            url = '/'+'/'.join(identifiers)
        else : url = '/'.join(identifiers)
        return url


    def send_page(self, path):
        # Forever ashamed, but getsize and getmtime sometime crash... ex : on a empty file (touch)
        def try_size(n):
            try :
                r = sizeof(os.path.getsize(n))
            except :
                r = 0
            return r
        def try_mtime(n):
            try :
                r = datetime.datetime.fromtimestamp(os.path.getmtime(n))
            except :
                r = 0
            return r

        def inner_elements(n):
            for (p, d, f) in os.walk(n) :
                return len(d)+len(f)  
        
        for (p, d, f) in os.walk(path) :
            # what's in it ?
            subdirs = [ {
                'name': n, 
                'inner_elements': inner_elements(os.path.join(p,n)),
                'mtime': try_mtime(n)
                 } for n in sorted(d) ] 
            files = [ {
                'name': n,
                'size': try_size(n),
                'mtime': try_mtime(n)
                } for n in sorted(f) ]
            break

        page = render( self.url_from_path(path), subdirs, files)
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write(page)


def main():
    try:
        yours = HTTPServer(('', port), YoursHandler)
        print 'Hi, i\'m yours,'
        print 'serving %s on port %s...' % (cwd,port)
        yours.serve_forever()
    except KeyboardInterrupt:
        print '\nKeyboard interrupt, closing.'
        yours.socket.close()

if __name__ == '__main__':
    main()
