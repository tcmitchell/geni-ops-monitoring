

class rsyslog::opsmon {
  service {
    "rsyslog":
      ensure => "running",
      enable => "true";
  }

  file {
    "/etc/rsyslog.d/opsmon.conf":
      source => "puppet:///modules/rsyslog/opsmon/opsmon.conf",
      mode => 0644,
      notify => Service["rsyslog"];
  }

}

