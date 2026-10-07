resource "helm_release" "prometheus" {
  name       = "prometheus"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "prometheus"
  version    = var.prometheus_chart_version
  namespace  = var.namespace

  set {
    name  = "server.global.scrape_interval"
    value = "2s"
  }

  set {
    name  = "server.global.evaluation_interval"
    value = "2s"
  }

  set {
    name  = "alertmanager.enabled"
    value = "true"
  }

  set {
    name  = "server.persistentVolume.enabled"
    value = "false"
  }
}

resource "helm_release" "grafana" {
  name       = "grafana"
  repository = "https://grafana.github.io/helm-charts"
  chart      = "grafana"
  version    = var.grafana_chart_version
  namespace  = var.namespace

  set {
    name  = "adminPassword"
    value = "admin_sre_portfolio"
  }

  set {
    name  = "persistence.enabled"
    value = "false"
  }

  depends_on = [helm_release.prometheus]
}
