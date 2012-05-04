# logic for comments
def comments():
    page = db.page(request.args(0))
    comments = db(db.comment.page==page.id).select(orderby=db.comment.created_on)
    return locals()

@auth.requires_login()
def del_comment():
    comment = db.comment(request.args(0))
    if comment and (comment.created_by==auth.user.id or comment.page.owner==auth.user.id):
        del db.comment[comment.id]
        return 'true'
    return 'false'

@auth.requires_login()
def add_comment():
    page_id = request.args(0)
    if not auth.user: return ''
    id = db.comment.insert(page=page_id,body=request.vars.comment)
    return COMMENT(request.now,auth.user.username,id,request.vars.comment)
# end logic for comments
