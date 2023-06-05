#!/bin/bash
url="https://$USER:$PASSWORD@github.com/opengisch/sh.oereb.oereb-server.database.git"
git config --global user.email "$MAIL"
git clone $url /git


while true;
do
  python3 /app/update.py;
  cd /git && git add .;
  cd /git && git commit . -m 'automatic update after transformation';
  cd /git && git push;
  sleep 5;
done;
