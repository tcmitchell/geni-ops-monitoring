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

class local::server {

  if $populate_data {
    $local_setup_script = "local_restart_node_interface_stats.py -b http://localhost:8088"
  } else {
    $local_setup_script = "local_table_reset.py"
  }

  exec {
    "local_update_code":
      command => "/usr/bin/rsync -a --delete /ops-monitoring/ /usr/local/ops-monitoring/";

    "local_setup":
      command => "/usr/bin/python ./${local_setup_script}",
      cwd => "/usr/local/ops-monitoring/local/unit-test",
      require => [
        File["/usr/local/ops-monitoring/config/local_datastore_operator.conf"],
        Exec["postgresql_set_postgres_passwords"],
        Package["python-psycopg2"]
      ];
  }

  file {
    "/usr/local/ops-monitoring/config/local_datastore_operator.conf":
      content => template("local/local_datastore_operator.conf.erb"),
      require => Exec["local_update_code"];
  }
}
