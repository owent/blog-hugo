#!/bin/bash

cd "$(dirname $0)";

hugo && rsync -avz --delete public/ owent@owent.net:/home/website/owent_blog