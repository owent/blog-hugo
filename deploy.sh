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

    python3 scripts/build-d2.py --gc --minify --cleanDestinationDir || exit $?;
fi

chmod +x *.py;

./build_index_for_gitbook.py

# rsync -az --progress --force --delete --chmod=775 public/ owent@vr-s.ouri.app:/home/website/owent_blog
