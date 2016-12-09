#!/bin/bash
#echo "Formatting..."
#find . -name "*.py" -exec yapf -i '{}' +
echo "Linting..."
find . -name "*.py" -exec pylint --rcfile=.pylintrc -E '{}' +
echo "Done."
