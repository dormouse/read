# read
A RSS READER

Now working in PyQt5 GUI

# Change log

20170515:

- improve setting, for dock status have to change to QSetting.
- remember last tree menu status

20170516:

- add load all function
- add load all feeds in folder function
- get rid of tree menu header
- hide tree menu root
- reload item list after update

20170518
- add test for queries
- add right click menu for tree menu
- show unread number in tree menu

20170519

- auto mark item read after 2000ms
- when add feed, set defautl folder to current folder
- [bug-fix] smzdm not get item, reason:not use en_US locale to parse publish datetime
- [bug-fix] repeat item

20170522
- cache content html
- clean html: remove image width and heigh

20170523
- modify database struct
- if today time just show HH:mm:ss

20170524
- make title column stretch

20170528
- [function] auto get title when add feed
- [function] delete folder
- [function] delete feed

20170529
- [function] update one feed
- [function] update one folder
- [function] upeate feed in separate progress

20170531
- [function] use keyboard to show next item

20170606
- use model to show tree menu

20170610
- add run.sh run.py
- [bug-fix] delete feed not reload item list view
- [bug-fix] some feed has not ['content'][0]['value']

# TODO
- [function] if there is no cache, download it.
- [function] show only unread items
- [function] full screen model
- [bug] when have unread item menu tree font is not bold
- [function] mark read/unread
- [function] tree menu drag and drop
- [function] next unread item
- context menu for tree menu and item list view
- Setting tree menu expanding policy to "fixed" or setting a maximum fixed it.
- add update in every 10 minutes function
- add change font function
- add open in browser function
- show icon in tree menu 
- import & export rss feeds
- Sent web page to kindle
- deal with penti
- improve show tree view unread item, not the whole tree, just a single item

# Note
icon download:http://www.easyicon.net/iconsearch/mail/
ompl:http://dev.opml.org/spec2.html

test rss:
    https://kindlefere.com/feed