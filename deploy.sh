#!/bin/bash

cd "$(dirname $0)";

which hugo;

if [ 0 -eq $? ]; then
    sh ./pull-subtree.sh;
    hugo;

    if [ 0 -ne $? ]; then
        echo "Something error, exit with $?";
        exit $?;
    fi
fi

rsync -avz --force --delete public/ owent@sssvr-s.owent.net:/home/website/owent_blog