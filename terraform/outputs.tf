output "app_name" {
  value = juju_application.kubeflow_roles.name
}

output "provides" {
  value = {}
}

output "requires" {
  value = {}
}
