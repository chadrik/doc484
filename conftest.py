# the presence of this file prevents a strange bug during testing where
# __import__('doc484.fixes.fix_type_comments') fails inside lib2to3.  I've
# never seen this error happen during use of doc484 w/ python2, so I'm
# chalking it up to a pytest bug.
