output "team" {
  value = datadog_team.infra_cloud
}

output "services" {
  value = local.software_catalog_services
}

output "system_entity" {
  value = datadog_software_catalog.system_definition.id
}

output "queue_entity" {
  value = datadog_software_catalog.queue_definition.id
}

output "service_entities" {
  value = {
    for service_name, entity in datadog_software_catalog.service_definitions :
    service_name => entity.id
  }
}
