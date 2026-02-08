/**
 * Common Internal Network Hostnames
 * 
 * These are hostnames and IP ranges commonly found in corporate
 * networks. Used by the favicon scanner to enumerate accessible
 * internal services.
 * 
 * Categories: CI/CD, Monitoring, Infra, Business Apps, Kubernetes
 * 
 * Research by Bountyy Oy - https://bountyy.fi
 */

export const COMMON_INTERNAL_HOSTS = {

    // ── Atlassian Suite ────────────────────────────────────────
    atlassian: [
        "jira.internal",
        "jira.corp.local",
        "jira.company.local",
        "confluence.internal",
        "confluence.corp.local",
        "bitbucket.internal",
        "bamboo.internal",
    ],

    // ── CI/CD ──────────────────────────────────────────────────
    cicd: [
        "jenkins.internal",
        "jenkins.corp.local",
        "gitlab.internal",
        "gitlab.corp.local",
        "ci.internal",
        "build.internal",
        "drone.internal",
        "circleci.internal",
        "teamcity.internal",
        "argocd.internal",
    ],

    // ── Monitoring & Observability ─────────────────────────────
    monitoring: [
        "grafana.internal",
        "grafana.corp.local",
        "kibana.internal",
        "prometheus.internal",
        "alertmanager.internal",
        "datadog.internal",
        "splunk.internal",
        "sentry.internal",
        "jaeger.internal",
        "zipkin.internal",
        "nagios.internal",
        "zabbix.internal",
    ],

    // ── Infrastructure ─────────────────────────────────────────
    infrastructure: [
        "vcenter.internal",
        "esxi.internal",
        "proxmox.internal",
        "idrac.internal",
        "ilo.internal",
        "ipmi.internal",
        "nas.internal",
        "san.internal",
        "backup.internal",
        "dns.internal",
        "dhcp.internal",
        "ldap.internal",
        "ad.internal",
        "dc01.internal",
        "dc02.internal",
    ],

    // ── Business Applications ──────────────────────────────────
    business: [
        "erp.internal",
        "crm.internal",
        "hr.internal",
        "finance.internal",
        "intranet.internal",
        "portal.internal",
        "wiki.internal",
        "mail.internal",
        "webmail.internal",
        "sharepoint.internal",
        "sso.internal",
        "okta.internal",
        "vpn.internal",
    ],

    // ── Kubernetes / Containers ────────────────────────────────
    kubernetes: [
        "k8s.internal",
        "kubernetes.internal",
        "rancher.internal",
        "portainer.internal",
        "registry.internal",
        "harbor.internal",
        "consul.internal",
        "vault.internal",
        "nomad.internal",
    ],

    // ── Databases ──────────────────────────────────────────────
    databases: [
        "db.internal",
        "mysql.internal",
        "postgres.internal",
        "redis.internal",
        "mongo.internal",
        "elastic.internal",
        "phpmyadmin.internal",
        "adminer.internal",
    ],

    // ── Common IP Gateways ─────────────────────────────────────
    gateways: [
        "192.168.1.1",
        "192.168.0.1",
        "10.0.0.1",
        "10.0.1.1",
        "10.1.0.1",
        "172.16.0.1",
        "172.16.1.1",
    ],

    // ── Cloud Metadata (if accessible from browser context) ────
    cloud_metadata: [
        "169.254.169.254",  // AWS/GCP/Azure metadata
    ],
};

/**
 * Generate hostname variants for a given base domain.
 * Corporate networks often use predictable naming schemes.
 * 
 * E.g., "jira" → ["jira.internal", "jira.corp.local", "jira.company.com"]
 */
export function generateVariants(basename, domains = [
    "internal",
    "corp.local",
    "company.local",
    "corp.net",
    "local",
]) {
    return domains.map(d => `${basename}.${d}`);
}
