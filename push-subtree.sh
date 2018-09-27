#!/bin/bash

cd "$(dirname $0)";

PREFIX=themes/distinctionpp;
HTTPS_REPO=https://github.com/owt5008137/hugo-theme-distinctionpp.git;
SSH_REPO=git@github.com:owt5008137/hugo-theme-distinctionpp.git;
BRANCH=master;


REMOTE_LIST=($(git remote show));
PUSH_URL=$(git remote get-url --push ${REMOTE_LIST[0]});

if [ "${PUSH_URL:0:7}"=="https:/" ] || [ "${PUSH_URL:0:7}"=="http://" ]; then
    REPO=$HTTPS_REPO;
else
    REPO=$SSH_REPO;
fi

if [ -e "themes/distinctionpp" ]; then
    git subtree push -P $PREFIX $REPO $BRANCH;
fi
