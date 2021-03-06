#!/bin/bash

cd "$(dirname $0)";

which hugo;

if [ 0 -eq $? ]; then
    # bash ./pull-subtree.sh;

    mkdir -p source/css;
    hugo gen chromastyles --style=github > source/css/syntax.css ;
    # patch css
    echo "/* Patch */ .chroma { padding: 0.5em; border-radius: 3px; }" >> source/css/syntax.css;
    echo "/* Patch */ .chroma span.err { background-color: transparent; }" >> source/css/syntax.css;

    hugo --gc --minify --cleanDestinationDir;

    if [ 0 -ne $? ]; then
        echo "Something error, exit with $?";
        exit $?;
    fi
fi

chmod +x *.py;

./build_index_for_gitbook.py

# rsync -az --progress --force --delete --chmod=775 public/ owent@vr-s.ouri.app:/home/website/owent_blog