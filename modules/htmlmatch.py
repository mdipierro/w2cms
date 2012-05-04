import BeautifulSoup

def htmlmatch(html1, html2):
    soup1 = BeautifulSoup.BeautifulSoup(html1)
    soup2 = BeautifulSoup.BeautifulSoup(html2)
    items = soup1.findAll(attrs={'class':'master'})
    for item in items:
        id = item.get('id')
        other = soup2.find(id=id)
        other.replaceWith(item)
    return str(soup2)

def test():
    a = '<div><div>Hello</div><div id="1" class="master">World</div></div>'
    b = '<div><div>World</div><div id="1">WORLD</div></div>'
    c = '<div><div>World</div><div id="1" class="master">World</div></div>'
    return htmlmatch(a,b)==c

if __name__=='__main__':
    print test()
