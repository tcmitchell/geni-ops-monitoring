#!/usr/bin/env bash -x

#----------------------------------------------------------------------
# Copyright (c) 2014 Raytheon BBN Technologies
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and/or hardware specification (the "Work") to
# deal in the Work without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Work, and to permit persons to whom the Work
# is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Work.
#
# THE WORK IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE WORK OR THE USE OR OTHER DEALINGS
# IN THE WORK.
#----------------------------------------------------------------------


# schema_date should be the date embedded in the $schema lines of the
# schemas.  This script does not verify that the schemas have the
# correct date in them.
schema_date=20140828

# Web server hosting the schemas
schema_server="ekron.gpolab.bbn.com"

# Directory on $schema_server to put the schemas in
schema_dir="/srv/www/monitoring/schema/"$schema_date

dest=$schema_server:$schema_dir

# Create directory on schema_server if it does not exist
ssh $schema_server "if [ ! -d $schema_dir ]; then mkdir $schema_dir; fi;"

for schema_file in $(ls *.schema)
do
    # strip off .schema suffix
    schema_file_no_ext=$(basename $schema_file .schema)
    scp $schema_file $dest/$schema_file_no_ext

    # ekron has some ssh connection throttling that prevents us
    # from making too many connections in quick succession, so
    # we sleep for a minute after each copy so as not to trigger
    # that.
    sleep 60
done

# Put all of the .jwc files there too for good measure
scp *.jwc $dest

# update ownership and permissions
ssh $schema_server "chgrp -R gpo $schema_dir ; chmod -R g+w $schema_dir ;"
