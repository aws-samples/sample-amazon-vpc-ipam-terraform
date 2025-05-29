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

output "top_pool_id" {
  description = <<-EOT
    The ID of the top-level IPAM pool that represents the organization's entire IP space.
    This is the root of the hierarchical pool structure.
  EOT
  value       = aws_vpc_ipam_pool.top.id
}

output "regional_pool_ids" {
  description = <<-EOT
    Map of regional IPAM pool IDs keyed by region identifier.
    Format: {region_key => pool_id}
    These pools are direct children of the top-level pool and represent regional allocations.
  EOT
  value       = { for k, v in aws_vpc_ipam_pool.regional : k => v.id }
}

output "bu_pool_ids" {
  description = <<-EOT
    Map of Business Unit IPAM pool IDs keyed by region-bu composite identifier.
    Format: {region-bu => pool_id}
    These pools are children of regional pools and represent business unit allocations.
  EOT
  value       = {
    for key, pool in aws_vpc_ipam_pool.bu :
    key => pool.id
  }
}

output "bu_cidrs" {
  description = <<-EOT
    Map of Business Unit IPAM pool CIDRs organized by region and business unit.
    Format: {region => {bu => cidr_list}}
    These CIDR blocks define the address space available to each business unit within a region.
  EOT
  value       = {
    for region, bu_configs in var.bu_ipam_configs : region => {
      for bu, bu_config in bu_configs : bu => bu_config.cidr
    }
  }
}

output "env_pool_ids" {
  description = <<-EOT
    Map of Environment IPAM pool IDs keyed by region-bu-env composite identifier.
    Format: {region-bu-env => pool_id}
    These are the leaf-level pools used for allocating CIDRs to actual VPCs.
    Typical environments include: dev, qa, prod, and core.
  EOT
  value       = {
    for key, pool in aws_vpc_ipam_pool.env :
    key => pool.id
  }
}

output "env_cidrs" {
  description = <<-EOT
    Map of Environment IPAM pool CIDRs organized by region, business unit, and environment.
    Format: {region => {bu => {env => cidr_list}}}
    These are the actual CIDR ranges available for VPC allocations in each environment.
    VPC CIDR allocations should be requested from these pools.
  EOT
  value       = {
    for region, env_configs in var.env_ipam_configs : region => {
      for bu, bu_envs in env_configs : bu => {
        for env, env_config in bu_envs : env => env_config.cidr
      }
    }
  }
}

#=======================================
# Resource Access Manager (RAM) Outputs
#=======================================

output "ram_resource_share_arns" {
  description = <<-EOT
    Map of RAM resource share ARNs keyed by pool identifier.
    Format: {pool_key => share_arn}
    These resource shares enable cross-account access to IPAM pools.
  EOT
  value       = { for k, v in aws_ram_resource_share.ram_shares : k => v.arn }
}

output "ram_principal_associations" {
  description = <<-EOT
    Details of the RAM principal associations for the organization.
    Contains information about which principals (organization/accounts) have access to the shared resources.
    Format: {key => {resource_share_arn => arn, principal => principal_id}}
    Used for auditing cross-account access permissions.
  EOT
  value       = {
    for k, v in aws_ram_principal_association.ram_shares_prin_assoc :
    k => {
      resource_share_arn = v.resource_share_arn
      principal          = v.principal
    }
  }
}

output "ram_resource_associations" {
  description = <<-EOT
    Details of RAM resource associations for IPAM pools.
    Contains information about which IPAM pools are shared via RAM.
    Format: {key => {association_arn => arn, association_id => id}}
    Used for tracking which resources are shared and their association identifiers.
  EOT
  value       = {
    for k, v in aws_ram_resource_association.share_assoc :
    k => {
      association_arn = v.resource_arn
      association_id  = v.id
    }
  }
}
