import urllib
import re
import os
import sys
import hashlib
import cgi

re_path = re.compile(r'(?P<base>\w+\://[^/]+)(?P<path_info>.*?)(?P<query_string>\?(.*))?')
re_urls = re.compile(r'\s(src|href|SRC|HREF)\s*=\s*[\'"](.*?)[\'"]')
re_urls2 = re.compile(r'url\([\'"]?(.+?)[\'"]?\)')
re_iframe = re.compile(r'<iframe(.*?)</iframe>',re.DOTALL)
STATIC = ('js','gif','css','png','jpg','jpeg','mov','svg','mp3','wav','mp4')

def normalize(url1,url2):
    if '://' in url2:
        return url2
    items = url1.split('/')
    if url2.startswith('/'):
        return '/'.join(items[:3])+url2
    while url2.startswith('../'):
        url2 = url2[3:]
        items = items[:-1]
    return '/'.join(items[:-1])+'/'+url2

def encode_name(url):
    base,filename = urllib.unquote(url.split('?')[0]).rsplit('/',1)
    return '%s.%s' % (hashlib.md5(base).hexdigest(),filename)

def extension(path_info):
    return path_info.split('?')[0].replace('css.php','css').split('.')[-1].lower()

def process_item(item,html,urls,url,static):
    base = '/'.join(url.split('/')[:3])
    proto = base.split('://')[0]
    url2=proto+':'+item if item.startswith('//') else item
    newurl = normalize(url,url2)
    if extension(item) in STATIC:
        if not newurl in urls:
            urls.append(newurl)
        html = html.replace(item,static+encode_name(newurl))
    return html

def htmldownload(url,destination=None,prefix='',verbose=False, iframes=True):
    """
    usage:
    download('http://web2py.com','web2py_com','static/')
    downloads web2py.com and all its css/media files recursively.
    it renames all the files and stores the in web2py_com folder
    'static/' is to be changed only if index.html is moved in a different folder,
    it affects prefix of links in index.html only.
    """
    success, fail = [], []
    m = re_path.match(url)
    if not destination: destination=m.group('base').split('://')[1]
    html = urllib.urlopen(url).read()
    if not iframes:
        html = re_iframe.sub('',html) # delete iframes
    if not os.path.exists(destination):
        os.mkdir(destination)
    static_path = os.path.join(destination,'static')
    if not os.path.exists(static_path):
        os.mkdir(static_path)
    if prefix and not prefix.endswith('/'): prefix = prefix+'/'
    static = prefix+'static/'
    urls = []
    for tmp, item in re_urls.findall(html):
        html = process_item(item,html,urls,url,static)
    for item in re_urls2.findall(html):
        html = process_item(item,html,urls,url,static)
    if prefix:
        open(os.path.join(destination,'index.html'),'wb').write(
            html.replace(prefix,''))
        open(os.path.join(destination,'theme.html'),'wb').write(html)
    else: 
        open(os.path.join(destination,'index.html'),'wb').write(html)
    success.append(url)
    while urls:
        ourl = urls.pop()
        try:
            data = urllib.urlopen(ourl).read()
            static_filename = os.path.join(static_path,encode_name(ourl))
            if verbose: print ourl,'->',static_filename
            if extension(ourl) == 'css':
                for item in re_urls2.findall(data):
                    data = process_item(item,data,urls,ourl,'')
            open(static_filename,'wb').write(data)
            success.append(ourl)
        except IOError:
            if verbose: print ourl,'(DOWNLOAD ERROR)'
            fail.append(ourl)
    return (success, fail)

re_title = re.compile('<(title|TITLE)>(.*?)</(title|TITLE)>',re.DOTALL)

def inject_title(html,title):
    return re_title.sub('<title>%s</title>' % cgi.escape(title),html)

def inject_script(html,url=None,script=None): 
    if script and not user:
        # script = script.replace('\\','\\\\')
        return html.replace('</head>',
                            '<script language="javascript">\n%s\n</script></head>' % script)
    elif url and not script:
        return html.replace('</head>',
                            '<script language="javascript" src="%s"></script></head>' % url)
    else:
        raise SyntaxError, "invalid arguments"

def inject_body(html,body):
    return re.compile('(?P<a>\<(body|BODY)[^>]*\>)(?P<b>.*)\</(body|BODY)\>',re.DOTALL).sub(
        '\g<a>%s</body>' % body.replace('\\','\\\\'),html)

def inject_buttons(html,buttons):
    code = ''.join('<button onclick="document.location=\'%s\'">%s</button>' % \
                       (item[1],item[0]) for item in buttons)
    return html.replace('</body>',
                        '<span style="position:fixed;padding:5px;z-index:1000;top:0;right:0;">%s</span></body>' % code)

spaces = re.compile('[ ]+')

def extract_text(html):
    from BeautifulSoup import BeautifulSoup
    def html2text(soup):
        if soup.string!=None:
            return soup.string.strip().replace('\n',' ')
        else:
            return ' '.join(html2text(item) for item in soup.contents)
    soup = BeautifulSoup(html)
    ingredients = soup.findAll(('h1','h2','h3','h4','h5','p','li'))
    text = '\n'.join(html2text(item) for item in ingredients)
    return spaces.sub(' ',text)

def download_all(page_url='http://www.csstemplatesfree.org/page/%s',
                 page_range=range(4,16),
                 tag = 'li',
                 _class='clearfloat'):
    from BeautifulSoup import BeautifulSoup
    for page in page_range:
        print 'page',page
        html = urllib.urlopen(page_url % page).read()
        soup = BeautifulSoup(html)
        items = soup.findAll(tag,{'class':_class})
        for item in items:
            try:
                name = item.find('img')['alt'].replace(' ','_')
                image_url = item.find('img')['src']
                source_url = item.findAll('a')[2]['href']
                print name
                if not os.path.exists(name): os.mkdir(name)
                htmldownload(source_url,name,prefix='@{page.theme}/')
                image_name = os.path.join(name,image_url.split('/')[-1])
                open(image_name,'wb').write(urllib.urlopen(image_url).read())
                os.system('convert %s %s' % (image_name,os.path.join(name,'thumbnail.png')))
            except:
                print name,'FAILED'
                try: os.system('rm -r %s' % name)
                except: pass

if __name__=='__main__':    
    if len(sys.argv)<2:
        print 'usage: htmldownload.py http://web2py.com'
    else:
        (success,fail) = htmldownload(sys.argv[1],verbose=True)
        print len(success),'files downloaded.',len(fail),'download errors'

