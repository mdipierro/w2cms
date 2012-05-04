db.define_table(
    'comment',
    Field('body',notnull=True),
    Field('page','reference page'),
    auth.signature)

def COMMENT(now,username,comment_id,body,deletable=True):
    return DIV(MARKMIN(body),
               SPAN('posted ',prettydate(now),' by ',username,
                    A(IMG(_src=URL('static','plugin_selectlist/cross-circle.png')),
               callback=URL('del_comment',args=comment_id),
                      delete='.comment'),_class='comment_header') \
                   if deletable else '',
               _class='comment')


