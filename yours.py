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
        <head/>
        <body>
            <div id='upload'>%s
            </div>
            <div id='dir'>%s
            </div>
        </body>
    </html>
    '''     

UPLOAD_TEPMPLATE =   '''
                <script>function uploadSubmit(){document.getElementById("upload").submit();}</script>
                <form id='upload' method='POST' enctype='multipart/form-data' >
                    <input type=file name=upfile  multiple/><br>
                    <input type=submit value=Submit />
                </form>
    '''

DIR_TEMPLATE = '''
                <ul id='dir_elements'>%s
                </ul>
    '''

SUBDIR_TEMPLATE = '''
                    <li><a href='%s'>[ %s ]</a> %s </li>
    '''

FILE_TEMPLATE = '''
                    <li><a href='%s'>%s</a> %s %s </li>
    '''

def render(subdirs, files):  
    subdirs = ''.join([ (SUBDIR_TEMPLATE % (d['path'], d['name'], d['mtime'] )) for d in subdirs ])
    files = ''.join([ (FILE_TEMPLATE % (f['path'], f['name'], f['size'], f['mtime'] )) for f in files ])
    
    directory = DIR_TEMPLATE % ( subdirs + files )
    page = PAGE_TEMPLATE % ( UPLOAD_TEPMPLATE, directory )
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
            
            if type(field_storage['upfile']) == type([]):
                files = field_storage['upfile']
            else :
                files = [field_storage['upfile']]

            for file_in in files :
                name = os.path.split(file_in.filename)[1]
                path = self.path_from_url()
                file_out = os.path.join(path, name)

                # 'version control'
                if os.path.exists( file_out ):
                    # FIX IT (windows ?)
                    versions_dir =  cwd+'/_yours_versions_'+path.split(cwd)[1]
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
            # pass
            print e
            self.send_error(404,'POST to "%s" failed: %s' % (self.path, str(e)) )

    def send_page(self, path):
        # Shame on me for theses two functions, but getsize and getmtime sometimes crash... ex : on a empty file (touch)
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
        q=self.path.split('/')
        r=q[len(q)-1]

        for (p, d, f) in os.walk(path) :
            # what's in it ?
            subdirs = [ {
                'name': n, 
                'path': r+'/'+n,
                'mtime': try_mtime(n)
                 } for n in d ] 
            files = [ {
                'name': n,
                'path': r+'/'+n,
                'size': try_size(n),
                'mtime': try_mtime(n)
                } for n in f ]
            break

        page = render( subdirs, files)
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
        print 'Keyboard interrupt, closing.'
        yours.socket.close()

if __name__ == '__main__':
    main()
