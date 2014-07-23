

class rsyslog::opsmon {
  file {
    "/etc/rsyslog.d/opsmon.conf":
      source => "puppet:///modules/rsyslog/opsmon/opsmon.conf",
      mode => 0644;
  }
}

