# -*- coding: utf-8 -*-
from gluon.utils import web2py_uuid
from htmldownload import htmldownload, inject_script, inject_body, inject_title, extract_text
import cgi
import re
import os
import glob
import hashlib
import gluon.contrib.autolinks as autolinks

MATHJAX = 'http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML'
THISAPP = '://%s/%s/' % (request.env.http_host,request.application)

def index():
    if request.env.request_method=='POST':
        session.body_saved = request.now
        session.body = request.vars.body
        return
    if session.body and (request.now-session.body_saved).seconds>60:
        session.body = None
    path = os.path.join(request.folder,'views','default','index.html')
    data = response.render(open(path,'rb'))
    if session.body:
        new_body = session.body
        if not request.vars.edit: 
            if not session.cdict: session.cdict={}
            new_body = autolinks.expand_html(new_body,session.cdict)
        data = inject_body(data, new_body)

    editablebody = URL('static','js/editablebody.js',vars=dict(
            home_url=URL('index'),
            edit_url='' if request.vars.edit else URL('index',vars=dict(edit='true')),
            back_url=URL('index'),
            save_url=URL('index')))
    data = inject_script(data,editablebody)
    drawers = URL('static','js/drawers.js',vars=dict(
            left_url=URL('docs') if auth.user \
                else URL('static','demo/docs.html'),
            left_label='Docs'))
    share = URL('static','js/share.js',vars=dict(
            static=URL('static','images')))
    if not request.vars.edit:
        data = inject_script(data,MATHJAX)
    data = inject_script(data,drawers)
    data = inject_script(data,share)
    return data

@auth.requires_login()
def edit():
    # retrieve the page if it exists
    page = db.page(request.args(0,0,int),created_by=auth.user.id) \
        or redirect(URL('index'))   
    if cannot('edit','page',page):
        redirect(URL('no_edit_permission'))
    save_mode = request.env.request_method=='POST' and request.vars.body
    if save_mode:
        if not session.cdict: session.cdict={}
        naked_body = re.sub(THISAPP,'://THIS/',request.vars.body)
        tanned_body = autolinks.expand_html(naked_body,session.cdict)
        full_html = inject_body(page.full_html, tanned_body)
        full_html = inject_title(full_html, page.title)
        body_text = extract_text(naked_body)
        page.update_record(body=naked_body,
                           body_text=body_text,
                           full_html=full_html)
        return ''
    # inject corners 
    editablebody = URL('static','js/editablebody.js',vars=dict(
            body='true' if page.owner==auth.user.id and request.vars.body else 'false',
            home_url=URL('index'),
            back_url=URL('read',args=(page.id,IS_SLUG.urlify(page.title))),
            save_url=URL('edit',args=page.id)))
    data = page.full_html
    if page.body: data = inject_body(data, page.body)
    data = inject_script(data,editablebody)
    drawers = URL('static','js/drawers.js',vars=dict(
            left_url=URL('docs',args=page.id),left_label='Docs',
            right_url=URL('tags',args=page.id),right_label='Tags'))
    data = inject_script(data,drawers)
    # fix all links, the app may have moved
    data = data.replace('@{page.theme}',
                        URL('static','themes',args=page.theme))
    return data

def read():
    # retrieve the page if it exists
    page = db.page(request.args(0,0,int)) or redirect(URL('index'))
    if cannot('edit','page',page):
        redirect(URL('no_read_permission'))
    data = page.full_html
    buttons = [('Plasmid',URL('index'))]
    editablebody = URL('static','js/editablebody.js',vars=dict(
            home_url=URL('index'),
            edit_url=URL('edit',args=request.args(0,0,int)),
            delete_url=URL('delete',args=request.args(0,0,int))))
    data = inject_script(data,editablebody)
    drawers = URL('static','js/drawers.js',vars=dict(
            left_url=URL('docs',args=page.id),left_label='Docs'))
    data = inject_script(data,drawers)
    share = URL('static','js/share.js',vars=dict(
            static=URL('static','images')))
    data = inject_script(data,share)
    # inject mathjax
    data = inject_script(data,MATHJAX)
    # incject web2py (mostly for web2py_component)
    data = inject_script(data,URL('static','js/web2py.js'))
    # fix the links
    data = data.replace('@{page.theme}',URL('static','themes',args=page.theme))
    menupages = db(db.page.parent_page==page.id)(db.page.child_index>0).select(
        db.page.title,db.page.id,
        orderby=db.page.child_index|db.page.title)
    menuitems=[(r.title,None,URL(args=r.id)) for r in menupages]
    data = data.replace('@{page.menu}',MENU(menuitems).xml())
    data = data.replace('://THIS/',THISAPP)
    # inject other variables and macro (todo)
    # ...
    return data

@auth.requires_login()
def delete():
    # delete page, only allowed to owner
    db(db.page.id==request.args(0,0,int))(db.page.owner==auth.user.id).delete()
    return URL('index')

@auth.requires_login()
def clone():
    # to be called via ajax will return URL where to go next
    title = request.vars.title or 'New Page'
    if request.env.request_method=='POST':
        oid = request.args(0,0,int)
        page = db.page(oid)
        # if new page has same owner set default payout and menu relations
        page.title = title
        if page.owner == auth.user.id:
            if not page.layout_page: page.layout_page = page.id
            if not page.parent_page: page.parent_page, page.child_index = page.id, 1
            else: page.child_index = page.get('child_index',0) + 1
        else:
            page.layout_page = page.parent_page = page.child_index = None
        # reset ownership for new page
        page.owner = page.created_by = auth.user.id
        id = db.page.insert(**db.page._filter_fields(page))
        # if cloned page owner, copy tags and permissions too
        if page.owner == auth.user.id:
            for tag in db(db.tag.page==oid).select():
                db.tag.insert(name=tag.name,page=id)
            perm = db.auth_permission
            for p in db(perm.table_name=='page')(perm.record_id==oid).select():
                perm.insert(name=p.name,group_id=p.group_id,
                            table_name='page',record_id=id)
        # return URL where to go afect
        return URL('read',args=(id,IS_SLUG.urlify(title)))
    return ''

@auth.requires_login()
def create():
    title = request.vars.title or 'New Page'
    url = request.vars.url
    theme = request.vars.theme
    # if postback create a new page
    if request.env.request_method=='POST':
        # if no theme, download the page
        if title and not theme and url and url!='http://':
            theme = web2py_uuid().replace('-','')
            path = os.path.join(request.folder,'static','themes',theme)
            if not os.path.exists(path): os.makedirs(path)
            try:
                htmldownload(url,path,prefix='@{page.theme}/')
            except IOError:
                response.flash = 'Unable to download'
        # if downloaded or there is a theme create record
        if title and theme:
            path = os.path.join(request.folder,'static','themes',
                                theme,'theme.html')
            data = response.render(open(path,'rb'))
            id = db.page.insert(title=request.vars.title,theme=theme,
                                full_html = data,owner=auth.user.id)
            my_group = db.auth_group(role=auth.user.username).id
            # give author read and edit permission
            redirect(URL('edit',args=id))
    # if no postback, list of availbale themes
    filenames = glob.glob(os.path.join(
            request.folder,'static','themes','*','thumbnail.png'))    
    themes = [(f.split('/')[-2],URL('static','/'.join(f.split('/')[-3:]))) \
                  for f in filenames]
    return locals()

@auth.requires_login()
def upload():
    # upload a new file in a page
    db.page.title.default = request.vars.title
    db.page.parent_page.default = request.args(0,0,int)
    db.page.child_index.default = 0
    form = SQLFORM(db.page).process()
    if form.accepted:
        redirect(URL('docs',args=request.args,
                     vars=dict(keywords=form.vars.title)))
    return locals()

### change from here (todo)
@auth.requires_login()
def docs():
    this = request.args(0,0,int)
    query = auth.accessible_query('read','page')|(db.page.public_read==True)|(db.page.owner==auth.user.id)
    query = query|db.page.parent_page.belongs(db(query)._select(db.page.id))
    if request.vars.keywords:
        query = query & db.page.title.contains(request.vars.keywords)
    elif this>0:
        query = query & (db.page.parent_page==this)
    pages = db(query).select(
        db.page.id,db.page.title,db.page.owner,db.page.document,
        db.page.layout_page,db.page.parent_page,db.page.child_index,
        orderby=~db.page.modified_on,limitby=(0,10))    
    return locals()
# to here

# (todo) permissions below:
@auth.requires_login()
def tags():
    this = request.args(0,0,int)
    page = db.page(this) or redirect(URL('error'))
    if cannot('edit','page',page):
        redirect(URL('error'))
    query = (db.auth_permission.table_name=='page')&\
        (db.auth_permission.record_id==page.id)&\
        (db.auth_permission.group_id==db.auth_group.id)
    permissions = db(query).select()
    read_groups = permissions.find(
        lambda row: row.auth_permission.name=='read')
    edit_groups = permissions.find(
        lambda row: row.auth_permission.name=='edit')
    tags = db(db.tag.page==page.id).select(orderby=db.tag.name)
    return locals()

@auth.requires(request.env.request_method=='POST')
def set_title():
    page = db.page(request.args(0,0,int)) or redirect(URL('error'))
    if cannot('edit','page',page):
        return 'false'
    page.update_record(title=request.vars.title or 'no title')
    return 'true'

def autotags():
    from serializers import json
    key = request.vars.term
    limit = int(request.vars.limit or 10)
    rows = db(db.tag.name.startswith(key)).select(
        db.tag.id,db.tag.name,distinct=True,limitby=(0,limit))
    items = [dict(id=r.id,value=r.name,label=r.name) for r in rows]
    return json(items)

@auth.requires(request.env.request_method=='POST')
def add_tag():
    page=db.page(request.args(0,0,int))
    if cannot('edit','page',page):
        raise HTTP(404)
    if request.vars.key:
        db.tag.insert(name=request.vars.key,page=page.id)
    return 'ok'

@auth.requires(request.env.request_method=='POST')
def del_tag():
    page=db.page(request.args(0,0,int))
    if cannot('edit','page',page):
        raise HTTP(404)
    db(db.tag.name==request.vars.key)(db.tag.page==page.id).delete()
    return 'ok'

def autogroups():
    from serializers import json
    key = request.vars.term
    limit = int(request.vars.limit or 10)
    group = db.auth_group
    rows = db(group.role.startswith(key)).select(
        group.id,group.role,limitby=(0,limit))
    items = [dict(id=r.id,value=r.role,label=r.role) for r in rows]
    if 'everybody'.startswith(key):
        items.insert(0,dict(id=0, value='everybody',label='everybody'))
    return json(items)

@auth.requires(request.env.request_method=='POST')
def add_group():
    id, name =  request.args(0,0,int), request.args(1)
    page=db.page(id)
    if cannot('edit','page',page):
        raise HTTP(404)
    print request.vars

    if request.vars.key:
        if name=='edit':
            if request.vars.key=='everybody':
                db(db.page.id==id).update(public_edit=True,public_read=True)
            else:
                gid = auth.id_group(request.vars.key)
                auth.add_permission(gid,'read','page',id)
                auth.add_permission(gid,'edit','page',id)
        elif name=='read':
            if request.vars.key=='everybody':
                db(db.page.id==id).update(public_read=True)
            else:
                gid = auth.id_group(request.vars.key)
                auth.add_permission(gid,'read','page',id)
        return 'true'
    return 'false'


@auth.requires(request.env.request_method=='POST')
def del_group():
    id, name =  request.args(0,0,int), request.args(1)
    page = db.page(id)
    if cannot('edit','page',page):
        raise HTTP(404)
    if request.vars.key and name in ('read','edit'):
        if name=='edit':
            if request.vars.key=='everybody':
                db(db.page.id==id).update(public_edit=False)
            else:
                gid = auth.id_group(request.vars.key)                
                auth.del_permission(gid,'edit','page',id)
        elif name=='read':
            if request.vars.key=='everybody':
                db(db.page.id==id).update(public_read=False,public_write=False)
            else:
                gid = auth.id_group(request.vars.key)
                auth.del_permission(gid,'read','page',id)
                auth.del_permission(gid,'edit','page',id)
        return 'true'
    return 'false'

def user():
    return dict(form=auth())

def getcode():
    redirect('http://web2py.com')

def no_read_permission():
    return locals()

def no_edit_permission():
    return locals()

def media():
    # serves a media file, do not use download
    id = request.args(0,0,cast=int)
    ext = (request.args(1) or '').split('.')[-1].lower()
    page = db.page(id)
    if not page or not page.document:
        raise HTTP(404)
    parent_page = db.page(page.parent_page)
    if cannot('read','page',parent_page):
        raise HTTP(404)
    request.args = [page.document]
    return response.download(request,db)
        
@auth.requires(request.env.request_method=='POST')
def add_to_menu():
    page = db.page(request.vars.page_id)
    if not page:
        raise HTTP(404)
    if cannot('edit','page',page):
        raise HTTP(404)
    index = request.vars.index or None
    page.update_record(parent_page=request.args(0,0,int),child_index=index)
    return 'true'

@auth.requires(request.env.request_method=='POST')
def set_dependency(): # work in progress
    this = request.args(0,0,int)
    page = db.page(request.vars.page_id)
    if not page:
        raise HTTP(404)
    if cannot('edit','page',page):
        raise HTTP(404)
    if request.vars.page_id!=this:
        layout_page = request.vars.set=='true' and this or None
        page.update_record(layout_page=layout_page)
    return 'true'

def oembed():
    url = request.vars.url
    if not session.cdict: session.cdict={}
    if url in session.cdict:
        r = session.cdict['url']
    else:
        r = session.cdict['url'] = autolinks.oembed(request.vars.url)
    return r.get('html',A(url,_href=url).xml())
