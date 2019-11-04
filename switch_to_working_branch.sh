export WORKING_BRANCH=$(cut -d'/' -f3 <<< cat /tmp/current_branch)
git checkout $WORKING_BRANCH
