# crawlonclick

[//]: # (server configuration)

alias runserver='cd; cd crawlonclick; nohup sudo python3 manage.py runserver 0.0.0.0:80 &'
alias runscrapyd='cd; cd crawlonclick; nohup sudo scrapyd &'
alias killserver='sudo pkill -f "runserver"'
alias killscrapyd='sudo pkill -f "scrapyd"'