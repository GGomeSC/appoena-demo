resource "datadog_team" "infra_cloud" {
  description = "Time de infraestrutura Cloud"
  handle      = "infra-cloud"
  name        = "Infra Cloud"
}

resource "datadog_user" "user" {
  email = "gabriel.coelho@segurosunimed.com.br"
}

resource "datadog_team_membership" "foo" {
  team_id = datadog_team.infra_cloud.id
  user_id = datadog_user.user.id
  role    = "admin"
}

resource "datadog_software_catalog" "system_definition" {
  entity = yamlencode({
    apiVersion = "v3"
    kind       = "system"
    metadata = {
      name        = "observability-demo"
      displayName = "Observability Demo"
      owner       = datadog_team.infra_cloud.handle
      tags = [
        "application:observability-demo",
        "env:dev",
        "team:${datadog_team.infra_cloud.handle}",
      ]
      contacts = [
        {
          name    = "Gabriel Gomes Coelho"
          type    = "email"
          contact = "gabrielcoelho2002@gmail.com"
        }
      ]
      additionalOwners = [
        {
          name = "Gabriel Gomes Coelho"
          type = "stakeholder"
        },
      ]
    }
    spec = {
      tier      = "1"
      lifecycle = "development"
      components = concat(
        [for service_name in local.software_catalog_services : "service:${service_name}"],
        ["queue:items-events"]
      )
    }
  })
}

resource "datadog_software_catalog" "service_definitions" {
  for_each = local.software_catalog_services

  entity = yamlencode({
    apiVersion = "v3"
    kind       = "service"
    metadata = {
      name        = each.value
      displayName = each.value
      owner       = datadog_team.infra_cloud.handle
      tags = [
        "application:observability-demo",
        "env:dev",
        "team:${datadog_team.infra_cloud.handle}",
      ]
      contacts = [
        {
          name    = "Gabriel Gomes Coelho"
          type    = "email"
          contact = "gabrielcoelho2002@gmail.com"
        }
      ]
    }
    spec = {
      tier      = "1"
      lifecycle = "development"
      type      = "web"
      languages = each.value == "appoena-demo-frontend" ? ["javascript"] : ["python"]
      dependsOn = local.service_dependencies[each.value]
    }
  })
}

resource "datadog_software_catalog" "queue_definition" {
  entity = yamlencode({
    apiVersion = "v3"
    kind       = "queue"
    metadata = {
      name        = "items-events"
      displayName = "items.events"
      owner       = datadog_team.infra_cloud.handle
      tags = [
        "application:observability-demo",
        "env:dev",
        "team:${datadog_team.infra_cloud.handle}",
      ]
      contacts = [
        {
          name    = "Gabriel Gomes Coelho"
          type    = "email"
          contact = "gabrielcoelho2002@gmail.com"
        }
      ]
    }
    spec = {
      tier      = "1"
      lifecycle = "development"
    }
  })
}
