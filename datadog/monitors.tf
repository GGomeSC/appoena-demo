resource "datadog_monitor" "infra_disk_usage" {
  name = "[INFRA] {{host.name}} ({{host.ip}}) | Utilização do disco {{device_name.name}} está acima de {{#is_alert}}{{eval \"int(threshold)\"}}% {{else}} {{warn_threshold}}% {{/is_alert}}"
  type = "query alert"

  message = join("\r\n", [
    "{{#is_alert}} ",
    "- **Servidor** = {{host.name}}",
    "- **Endereço IP** = {{host.ip}}",
    "- **Sistema Operacional** = {{host.metadata_platform}}",
    "- **Unidade** = {{device_name.name}}",
    "- **Threshold** = {{eval \"int(threshold)\"}}%",
    "- **Uso de disco** = {{eval \"int(value)\"}}%",
    "",
    "@gabrielcoelho2002@gmail.com ",
    "{{/is_alert}}",
    "",
    "{{#is_warning}}",
    "- **Servidor** = {{host.name}}",
    "- **Endereço IP** = {{host.ip}}",
    "- **Sistema Operacional** = {{host.metadata_platform}}",
    "- **Unidade** = {{device_name.name}}",
    "- **Threshold** = {{warn_threshold}}%",
    "- **Uso de disco** = {{eval \"int(value)\"}}%",
    "",
    "@gabrielcoelho2002@gmail.com ",
    "{{/is_warning}}",
    "",
    "{{#is_recovery}}",
    "- **Alerta Normalizado**",
    "- **Servidor** = {{host.name}}",
    "- **Endereço IP** = {{host.ip}}",
    "- **Sistema Operacional** = {{host.metadata_platform}}",
    "- **Unidade** = {{device_name.name}}",
    "- **Uso de disco** = {{eval \"int(value)\"}}%",
    "",
    "@gabrielcoelho2002@gmail.com ",
    "{{/is_recovery}}",
  ])

  query = "min(last_10m):100 * avg:system.disk.used{env:dev} by {env,host,device_name} / avg:system.disk.total{env:dev} by {env,host,device_name} > 95"

  include_tags             = false
  new_group_delay          = 60
  notification_preset_name = "hide_query_and_handles"
  notify_audit             = false
  on_missing_data          = "default"
  require_full_window      = false
  tags                     = ["env:dev", "team:infra-cloud"]

  lifecycle {
    ignore_changes = [
      new_host_delay,
      restricted_roles,
    ]
  }

  monitor_thresholds {
    critical = "95"
    warning  = "90"
  }
}

resource "datadog_monitor" "infra_memory_usage" {
  name = "[INFRA] {{host.name}} ({{host.ip}}) | Utilização memória está acima de {{#is_alert}}{{eval \"int(threshold)\"}}%%{{else}}{{warn_threshold}}%%{{/is_alert}}"
  type = "query alert"

  message = join("\r\n", [
    "{{#is_alert}}",
    "- **Servidor** = {{host.name}}",
    "- **Endereço IP** = {{host.ip}}",
    "- **Sistema Operacional** = {{host.metadata_platform}}",
    "- **Threshold** = {{eval \"int(threshold)\"}}%",
    "- **Uso de RAM** = {{eval \"int(value)\"}}%",
    "{{/is_alert}}",
    "",
    "{{#is_warning}}",
    "- **Servidor** = {{host.name}}",
    "- **Endereço IP** = {{host.ip}}",
    "- **Sistema Operacional** = {{host.metadata_platform}}",
    "- **Threshold** = {{warn_threshold}}%",
    "- **Uso de RAM** = {{eval \"int(value)\"}}%",
    "{{/is_warning}}",
    "",
    "",
    "{{#is_recovery}}",
    "- **Alerta Normalizado**",
    "- **Servidor** = {{host.name}}",
    "- **Endereço IP** = {{host.ip}}",
    "- **Sistema Operacional** = {{host.metadata_platform}}",
    "- **Uso de RAM** = {{eval \"int(value)\"}}%",
    "{{/is_recovery}}",
    "@gabrielcoelho2002@gmail.com",
  ])

  query = "min(last_10m):(sum:system.mem.total{env:dev} by {host,env} - sum:system.mem.usable{env:dev} by {host,env}) / sum:system.mem.total{env:dev} by {host,env} * 100 > 95"

  include_tags             = false
  new_group_delay          = 60
  notification_preset_name = "hide_query_and_handles"
  notify_audit             = false
  on_missing_data          = "default"
  require_full_window      = false
  tags                     = ["env:dev", "team:infra-cloud"]

  lifecycle {
    ignore_changes = [
      new_host_delay,
      restricted_roles,
    ]
  }

  monitor_thresholds {
    critical = "95"
    warning  = "90"
  }
}

resource "datadog_monitor" "infra_cpu_usage" {
  name = "[INFRA] {{host.name}} ({{host.ip}}) | Utilização CPU está acima de {{#is_alert}}{{eval \"int(threshold)\"}}%%{{else}}{{warn_threshold}}%%{{/is_alert}}"
  type = "query alert"

  message = join("\r\n", [
    "{{#is_alert}} ",
    "- **Sistema** = {{application.name}}",
    "- **Servidor** = {{host.name}}",
    "- **Endereço IP** = {{host.ip}}",
    "- **Sistema Operacional** = {{host.metadata_platform}}",
    "- **Threshold** = {{eval \"int(threshold)\"}}%",
    "- **Uso de CPU** = {{eval \"int(value)\"}}%",
    "{{/is_alert}}",
    "",
    "{{#is_warning}}",
    " - **Sistema** = {{application.name}}",
    " - **Servidor** = {{host.name}}",
    " - **Endereço IP** = {{host.ip}}",
    " - **Sistema Operacional** = {{host.metadata_platform}}",
    " - **Threshold** = {{warn_threshold}}%",
    " - **Uso de CPU** = {{eval \"int(value)\"}}%",
    "{{/is_warning}}",
    "",
    "{{#is_recovery}}",
    "**Alerta Normalizado**",
    " - **Sistema** = {{application.name}}",
    " - **Servidor** = {{host.name}}",
    " - **Endereço IP** = {{host.ip}}",
    " - **Sistema Operacional** = {{host.metadata_platform}}",
    " - **Uso de CPU** = {{eval \"int(value)\"}}%",
    "{{/is_recovery}}",
    "@gabrielcoelho2002@gmail.com",
  ])

  query = "min(last_10m):100 - avg:system.cpu.idle{env:dev} by {host}.rollup(avg, 60) > 95"

  include_tags             = false
  new_group_delay          = 60
  notification_preset_name = "hide_query_and_handles"
  notify_audit             = false
  on_missing_data          = "default"
  require_full_window      = false
  tags                     = ["env:dev", "team:infra-cloud"]

  lifecycle {
    ignore_changes = [
      new_host_delay,
      restricted_roles,
    ]
  }

  monitor_thresholds {
    critical = "95"
    warning  = "90"
  }
}

resource "datadog_monitor" "frontend_rum_5xx_error_rate" {
  name = "[{{[@application.name].name}}] Alta taxa de erro 5xx no {{[@resource.method].name}} {{[@resource.url_path_group].name}}"
  type = "rum alert"

  message = join("\r\n", [
    "[{{[@application.name].name}}] - Front-end com alta taxa de erro 5xx",
    "",
    "{{#is_alert}} ",
    "- **Path URL** = {{[@resource.url_path_group].name}}",
    "- **Threshold** = {{eval \"int(threshold)\"}}%",
    "- **Taxa de erro atual** = {{eval \"int(value)\"}}%",
    "{{/is_alert}}",
    "{{#is_recovery}}",
    "**Alerta Normalizado**",
    " ",
    "- **Path URL** = {{[@resource.url_path_group].name}}",
    "- **Threshold** = {{eval \"int(threshold)\"}}%",
    "- **Taxa de erro atual** = {{eval \"int(value)\"}}%",
    "{{/is_recovery}}",
    "@gabrielcoelho2002@gmail.com",
  ])

  query = "formula(\"100 * query / query1\").last(\"10m\") > 25"

  include_tags             = false
  new_group_delay          = 60
  notification_preset_name = "hide_query_and_handles"
  notify_audit             = false
  on_missing_data          = "default"
  require_full_window      = false
  tags = [
    "application:appoena-demo-frontend",
    "env:dev",
    "team:infra-cloud",
  ]

  lifecycle {
    ignore_changes = [
      new_host_delay,
      restricted_roles,
    ]
  }

  monitor_thresholds {
    critical = "25"
  }

  variables {
    event_query {
      data_source = "rum"
      indexes     = ["*"]
      name        = "query"

      compute {
        aggregation = "count"
      }

      group_by {
        facet = "@resource.method"
        limit = 10

        sort {
          aggregation = "count"
          metric      = "count"
          order       = "desc"
        }
      }

      group_by {
        facet = "@resource.url_path_group"
        limit = 10

        sort {
          aggregation = "count"
          metric      = "count"
          order       = "desc"
        }
      }

      group_by {
        facet = "@application.name"
        limit = 10

        sort {
          aggregation = "count"
          metric      = "count"
          order       = "desc"
        }
      }

      search {
        query = "@type:resource @application.id:(f8e07897-3d1e-42f6-be1a-1f39266305d7) @resource.status_code:5* @session.type:user -@resource.url_path_group:(*.png OR *.js OR *.svg OR *.json OR *.css)"
      }
    }

    event_query {
      data_source = "rum"
      indexes     = ["*"]
      name        = "query1"

      compute {
        aggregation = "count"
      }

      group_by {
        facet = "@resource.method"
        limit = 10

        sort {
          aggregation = "count"
          metric      = "count"
          order       = "desc"
        }
      }

      group_by {
        facet = "@resource.url_path_group"
        limit = 10

        sort {
          aggregation = "count"
          metric      = "count"
          order       = "desc"
        }
      }

      group_by {
        facet = "@application.name"
        limit = 10

        sort {
          aggregation = "count"
          metric      = "count"
          order       = "desc"
        }
      }

      search {
        query = "@type:resource @application.id:(f8e07897-3d1e-42f6-be1a-1f39266305d7) @session.type:user -@resource.url_path_group:(*.png OR *.js OR *.svg OR *.json OR *.css)"
      }
    }
  }
}
