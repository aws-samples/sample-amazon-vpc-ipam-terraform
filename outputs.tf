#==============================================================================
# Sample Terraform Implementation for Hierarchical IPAM on AWS
#
# This code demonstrates how to implement hierarchical IP Address Management
# across multiple AWS regions, business units, and environments.
#
# IMPORTANT: This code is provided as a sample for educational purposes.
# Before using in production, review security configurations and customize
# to meet your organizational requirements.
#==============================================================================

#=======================================
# IPAM Pool Identifier Outputs
#=======================================

output "ipam_top_pool_id" {
  description = <<-EOT
    The ID of the top-level IPAM pool.
    Use this ID when referencing the entire organizational address space.
    Useful for administrative tasks affecting the entire IPAM hierarchy.
  EOT
  value       = module.ipam.top_pool_id
}

output "ipam_regional_pool_ids" {
  description = <<-EOT
    Map of regional IPAM pool IDs keyed by region identifier.
    Format: {region_key => pool_id}
    Example: {"us_east_1" => "ipam-pool-0123456789abcdef"}
    Use these IDs when referencing region-specific address allocations.
  EOT
  value       = module.ipam.regional_pool_ids
}

output "ipam_bu_pool_ids" {
  description = <<-EOT
    Map of Business Unit IPAM pool IDs keyed by region-bu composite identifier.
    Format: {region-bu => pool_id}
    Example: {"us-east-1-finance" => "ipam-pool-0123456789abcdef"}
    Use these IDs when referencing business unit-specific address allocations.
  EOT
  value       = module.ipam.bu_pool_ids
}

output "ipam_env_pool_ids" {
  description = <<-EOT
    Map of Environment IPAM pool IDs keyed by region-bu-env composite identifier.
    Format: {region-bu-env => pool_id}
    Example: {"us-east-1-finance-dev" => "ipam-pool-0123456789abcdef"}
    These are the leaf-level pools used for allocating CIDRs to actual VPCs.
    
    Usage example:
    ```
    module "vpc" {
      source = "./modules/vpc"
      ipam_pool_id = module.ipam.ipam_env_pool_ids["us-east-1-finance-dev"]
    }
    ```
  EOT
  value       = module.ipam.env_pool_ids
}

#=======================================
# IPAM CIDR Allocation Outputs
#=======================================

output "ipam_bu_pool_cidrs" {
  description = <<-EOT
    Map of Business Unit IPAM pool CIDRs organized by region and BU.
    Format: {region => {bu => cidr_list}}
    Example: {"us-east-1" => {"finance" => ["10.0.0.0/14"]}}
    Use these for network planning and documentation purposes.
  EOT
  value       = module.ipam.bu_cidrs
}

output "ipam_env_pool_cidrs" {
  description = <<-EOT
    Map of Environment IPAM pool CIDRs organized by region, BU, and environment.
    Format: {region => {bu => {env => cidr_list}}}
    Example: {"us-east-1" => {"finance" => {"dev" => ["10.0.0.0/16"]}}}
    These are the actual CIDR ranges available for VPC allocations in each environment.
  EOT
  value       = module.ipam.env_cidrs
}

#=======================================
# Resource Access Manager (RAM) Outputs
#=======================================

output "ipam_ram_resource_share_arns" {
  description = <<-EOT
    The ARNs of the RAM resource shares for IPAM pools.
    Format: {pool_key => share_arn}
    These ARNs can be used to reference the RAM shares in IAM policies or other AWS resources.
  EOT
  value       = module.ipam.ram_resource_share_arns
  sensitive   = false
}

output "ipam_ram_principal_associations" {
  description = <<-EOT
    Details of the RAM principal associations for the organization.
    Contains information about which principals (organization/accounts) have access to the shared resources.
    Format: {key => {resource_share_arn => arn, principal => principal_id}}
  EOT
  value       = module.ipam.ram_principal_associations
  sensitive   = false
}

output "ipam_ram_resource_associations" {
  description = <<-EOT
    Details of RAM resource associations for IPAM pools, including ARNs and IDs.
    Contains information about which IPAM pools are shared and their association details.
    Format: {key => {association_arn => arn, association_id => id}}
    
    These details are useful for troubleshooting cross-account access issues or auditing resource sharing.
  EOT
  value       = module.ipam.ram_resource_associations
  sensitive   = false
}
