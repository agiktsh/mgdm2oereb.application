#!/bin/bash
git config --global user.email "$MAIL"
git clone $GIT_REPO_URL /git


while true;
do
  cd /git && git pull;
  python3 /app/update.py;
  cd /git && git add .;
  cd /git && git commit . -m 'automatic update after transformation';
  cd /git && git push;
  sleep 5;
done;
