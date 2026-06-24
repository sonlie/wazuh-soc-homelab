# Lessons Learned

## Overview

This document summarizes key lessons learned while building and operating a SOC homelab using Wazuh, Suricata, Fail2Ban, Kali Linux, Ubuntu Server, and custom Python detection tools.

---

## 1. SIEM Visibility Depends on Log Sources

One of the first lessons learned was that Wazuh can only detect events that are properly collected and forwarded.

Initially, SSH authentication events appeared in `/var/log/auth.log` but were not visible in the Wazuh dashboard because the relevant log source was not configured correctly.

Lesson:

* Always verify log ingestion before troubleshooting detection rules.
* Confirm logs are reaching the SIEM before investigating alert logic.

---

## 2. Suricata Requires Proper Rule Management

After installing Suricata, the service failed to start because no rule files were available.

Error:

```text
No rule files match the pattern
```

Resolution:

* Updated Emerging Threats rules.
* Verified rule paths in `suricata.yaml`.
* Tested configuration using:

```bash
sudo suricata -T -c /etc/suricata/suricata.yaml
```

Lesson:

* IDS deployments require both the engine and valid rule sets.
* Service installation alone does not provide detections.

---

## 3. Detection Does Not Equal Visibility

Suricata successfully generated alerts inside `eve.json`, but Wazuh did not initially display them.

Root cause:

* Incorrect or missing Wazuh log collection configuration.

Resolution:

* Added Suricata JSON log collection to the Wazuh Agent configuration.
* Restarted the agent.

Lesson:

* Event generation and event ingestion are separate processes.
* Always validate the complete detection pipeline.

---

## 4. Network Design Matters

The lab used a combination of Host-Only and NAT adapters.

Several connectivity issues occurred during deployment:

* Internet access problems
* Agent communication issues
* Dashboard accessibility challenges

Lesson:

* Proper network planning significantly reduces troubleshooting time.
* Host-Only networking is useful for isolation.
* NAT networking is useful for updates and package installation.

---

## 5. Custom Detection Logic Requires Context

The Python detection engine originally generated repeated alerts for the same source IP.

Root cause:

* Previously alerted IPs were not tracked correctly.

Resolution:

* Implemented alert deduplication using a Python set.

Lesson:

* Detection logic must account for duplicate events.
* Alert fatigue can become a problem without proper filtering.

---

## 6. Brute Force Detection Is More Complex Than Failed Logins

Simply counting failed SSH attempts can produce false positives.

The custom detector was improved to identify:

* Multiple failed login attempts
* Followed by a successful login
* Within a defined time window

Lesson:

* Context-based detections are more valuable than simple event counting.
* Event correlation improves detection quality.

---

## 7. Automation Improves Response Time

The Python detector was converted into a systemd service.

Benefits:

* Automatic startup
* Continuous monitoring
* Recovery after reboot

Lesson:

* Detection tools should operate as services rather than manual scripts.

---

## 8. Discord Provides Simple Alerting

Discord webhooks provided an easy method for delivering security alerts.

Benefits:

* Real-time notifications
* Minimal configuration
* Accessible from any device

Lesson:

* Alert delivery is as important as alert generation.

---

## 9. Automated Response Adds Defensive Value

Fail2Ban was integrated to automatically block malicious SSH sources.

Benefits:

* Reduced brute-force exposure
* Faster containment
* Reduced manual intervention

Lesson:

* Detection without response has limited value.
* Automated containment significantly improves security posture.

---

## 10. SOC Work Is More Than Installing Tools

The most important lesson from this project was understanding the full security workflow:

Attack

↓

Detection

↓

Investigation

↓

Alerting

↓

Response

Building the lab required troubleshooting, log analysis, detection engineering, incident investigation, and automation.

This provided a more realistic understanding of how a Security Operations Center functions in practice.

---

## Future Improvements

Planned enhancements include:

* Windows endpoint monitoring
* Sysmon integration
* Sigma rules
* Threat intelligence feeds
* Email alerting
* Active response scripts
* YARA-based detections
* Custom Wazuh rules
