def HField(*a,**b):
    b['writable']=b['readable']=False
    return Field(*a,**b)

db.define_table(
    'page',
    Field('title',requires=IS_NOT_EMPTY()),
    HField('theme'),    
    HField('body','text'),
    HField('body_text','text'),
    HField('full_html','text'),
    HField('owner','reference auth_user'),
    HField('layout_page','reference page'),
    HField('parent_page','reference page'),
    HField('child_index','integer'),
    HField('public_read','boolean',default=False),
    HField('public_edit','boolean',default=False),
    Field('document','upload'),
    auth.signature)

db.define_table(
    'tag',
    Field('name'),
    Field('page','reference page'))

# only for backward compatibility
db.page.is_active.writable=False
db.page.is_active.readable=False

def make_link(page):
    # currently unused!
    if not page.document:
        return ''
    short = '%s.%s' % (page.id,page.document.split('.')[-1]),
    return A('@{media/%s}' % short,_href=URL('media',args=short))

def can(name,tablename,record):
    if auth.user and record.owner == auth.user.id:
        return True
    elif name=='read' and record.public_read:
        return True
    elif name=='edit' and auth.user:
        return True
    elif not auth.user:
        return False
    else:
        return auth.has_permission(name,tablename,record.id)

def cannot(name,tablename,record):
    return not can(name,tablename,record)

